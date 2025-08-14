"GitHub Summary Application - Core application with integrated web server."

import asyncio
import functools
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import typer
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from rich.logging import RichHandler

from github_summary.config import load_config
from github_summary.github_client import GitHubService
from github_summary.last_run_manager import (
    _get_run_key,
    get_last_run_time,
    set_multiple_last_run_times,
)
from github_summary.llm_client import AsyncLLMClient
from github_summary.models import Config, FilterConfig, RepoConfig
from github_summary.rss import generate_feed_from_summaries
from github_summary.summarizer import Summarizer
from github_summary.summary_cache import add_summaries_to_cache, load_summaries

logger = logging.getLogger(__name__)


class GitHubSummaryApp:
    """Core GitHub summary application."""

    def __init__(self, config_path: str, skip_summary: bool = False):
        self.config_path = config_path
        self.skip_summary = skip_summary
        self._config: Config | None = None
        self._github_service: GitHubService | None = None
        self._summarizer: Summarizer | None = None
        self._logging_initialized = False

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        if self._github_service:
            await self._github_service.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def config(self) -> Config:
        """Lazy load and cache configuration."""
        if self._config is None:
            try:
                self._config = load_config(self.config_path)
            except (FileNotFoundError, ValueError) as e:
                logger.error("Configuration error: %s", e)
                raise typer.Exit(1)
        return self._config

    def _setup_logging(self) -> None:
        """Set up logging with console and file handlers."""
        if self._logging_initialized:
            return

        log_dir = Path("log")
        log_dir.mkdir(exist_ok=True)

        console_handler = RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
        console_handler.setFormatter(logging.Formatter("%(message)s"))

        file_handler = RotatingFileHandler(log_dir / "github_summary.log", maxBytes=5 * 1024 * 1024, backupCount=3)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper(), logging.INFO),
            handlers=[console_handler, file_handler],
        )

        # Mute httpx logging to avoid cluttering output
        logging.getLogger("httpx").setLevel(logging.WARNING)
        self._logging_initialized = True

    async def _get_github_service(self) -> GitHubService:
        """Get or create GitHub service instance."""
        if self._github_service is None:
            # Validate GitHub token
            github_token = self.config.github.token or os.environ.get("GITHUB_TOKEN")
            if not github_token:
                logger.error("GITHUB_TOKEN not found in config or environment variables.")
                raise typer.Exit(1)

            try:
                self._github_service = GitHubService(github_token)
                await self._github_service.__aenter__()
            except Exception as e:
                logger.error("GitHub service creation error: %s", e)
                raise typer.Exit(1)

        return self._github_service

    def _get_summarizer(self):
        """Get or create summarizer instance."""
        if self._summarizer is None and not self.skip_summary:
            if not self.config.llm:
                return None

            llm_client = AsyncLLMClient(
                api_key=self.config.llm.api_key if self.config.llm.api_key else "",
                base_url=self.config.llm.base_url,
                model_name=self.config.llm.model_name,
                retries=self.config.llm.retries,
                retry_delay=self.config.llm.retry_delay,
                max_concurrent=self.config.performance.max_concurrent_llm,
            )

            self._summarizer = Summarizer(
                llm_client=llm_client,
                system_prompt=self.config.llm.system_prompt,
                language=self.config.llm.language,
                timezone=self.config.timezone,
            )

            # Validate LLM config if needed
            if not self.skip_summary and not self._summarizer:
                logger.error("LLM configuration not found in config.toml.")
                raise typer.Exit(1)

        return self._summarizer

    def _get_max_concurrent_repos(self, override: Optional[int] = None) -> int:
        """Get max concurrent repos with environment variable override."""
        if override is not None:
            return override

        # Use config value as default
        max_concurrent = self.config.performance.max_concurrent_repos

        # Allow environment variable override
        env_concurrent = os.environ.get("GHSUM_CONCURRENT_REPOS")
        if env_concurrent:
            try:
                max_concurrent = int(env_concurrent)
                logger.info("Using GHSUM_CONCURRENT_REPOS environment variable: %d", max_concurrent)
            except ValueError:
                logger.warning("Invalid GHSUM_CONCURRENT_REPOS value: %s, using config/default", env_concurrent)

        return max_concurrent

    def _merge_filters(self, repo: RepoConfig, global_filters: FilterConfig) -> FilterConfig:
        """Merge global and repository-specific filters."""
        merged = global_filters.model_copy(deep=True) if global_filters else FilterConfig()

        if not repo.filters:
            return merged

        for field in ["commits", "pull_requests", "issues", "discussions"]:
            repo_filter = getattr(repo.filters, field)
            if repo_filter:
                current_filter = getattr(merged, field)
                if current_filter:
                    setattr(merged, field, current_filter.model_copy(update=repo_filter.model_dump(exclude_unset=True)))
                else:
                    setattr(merged, field, repo_filter)

        return merged

    async def _fetch_repo_data(self, github_service, repo: RepoConfig, since: datetime) -> dict:
        """Fetch all data for a repository using async GitHub service."""
        logger.info("Fetching data for repository: %s", repo.name)

        filters = self._merge_filters(repo, self.config.global_filters)

        # Create tasks only for enabled data types
        tasks = {}
        if repo.include_commits:
            tasks["commits"] = github_service.get_commits(repo, filters, since)
        if repo.include_pull_requests:
            tasks["pull_requests"] = github_service.get_pull_requests(repo, filters, since)
        if repo.include_issues:
            tasks["issues"] = github_service.get_issues(repo, filters, since)
        if repo.include_discussions:
            tasks["discussions"] = github_service.get_discussions(repo, filters, since)

        # Execute enabled fetches concurrently
        if tasks:
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            # Map results back to data types
            data_results = {}
            for i, (key, _) in enumerate(tasks.items()):
                if isinstance(results[i], Exception):
                    logger.error("Failed to fetch %s for %s: %s", key, repo.name, results[i])
                    data_results[key] = []
                else:
                    data_results[key] = results[i]
        else:
            data_results = {}

        # Ensure all keys exist with empty lists as defaults
        commits = data_results.get("commits", [])
        pull_requests = data_results.get("pull_requests", [])
        issues = data_results.get("issues", [])
        discussions = data_results.get("discussions", [])

        return {
            "repo": repo.name,
            "commits": [c.model_dump() for c in commits],
            "pull_requests": [pr.model_dump() for pr in pull_requests],
            "issues": [i.model_dump() for i in issues],
            "discussions": [d.model_dump() for d in discussions],
        }

    async def _calculate_since_time_for_repo(self, repo_name: str) -> datetime:
        """Calculate since time for a specific repository."""
        fallback_since = datetime.now(UTC) - timedelta(days=self.config.fallback_lookback_days)

        if not self.config.since_last_run:
            return fallback_since

        # Try per-repository last run time first
        last_run_time = await get_last_run_time(self.config_path, repo_name)
        if last_run_time:
            return last_run_time

        # Fall back to global last run time for backward compatibility
        global_last_run_time = await get_last_run_time(self.config_path)
        if global_last_run_time:
            return global_last_run_time

        logger.warning(
            "No last run time found for %s, falling back to %s days.", repo_name, self.config.fallback_lookback_days
        )
        return fallback_since

    async def _generate_summary(self, repo_data: dict, summarizer, since: datetime) -> str:
        """Generate summary from repository data using async summarizer."""
        if not summarizer:
            return ""

        logger.info("Generating summary with LLM for %s", repo_data.get("repo", "unknown"))
        summary = await summarizer.summarize(repo_data, since)
        logger.debug("Generated summary for %s (%d characters)", repo_data.get("repo", "unknown"), len(summary))
        return summary

    async def _save_markdown_summary(self, repo_name: str, summary: str) -> None:
        """Save summary as markdown file."""
        if not summary:
            return

        def _write_markdown(repo_name, summary, output_dir):
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            file_name = f"{repo_name.replace('/', '_')}_summary.md"
            file_path = output_path / file_name

            with open(file_path, "w") as f:
                f.write(f"## Summary for {repo_name}\n\n{summary}")

            return file_path

        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(
            None, functools.partial(_write_markdown, repo_name, summary, self.config.output_dir)
        )

        logger.info("Summary saved to %s", file_path)

    async def _save_json_report(self, repo_name: str, repo_data: dict) -> None:
        """Save repository data as JSON file."""

        def _write_json(repo_name, repo_data, output_dir):
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            file_name = f"{repo_name.replace('/', '_')}_summary.json"
            file_path = output_path / file_name

            with open(file_path, "w") as f:
                json.dump(repo_data, f, indent=2)

            return file_path

        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(
            None, functools.partial(_write_json, repo_name, repo_data, self.config.output_dir)
        )

        logger.info("Report saved to %s", file_path)

    def _filter_repositories(self, repo_name: str | None) -> list[RepoConfig]:
        """Filter repositories based on repo_name parameter."""
        if not repo_name:
            return self.config.repositories

        filtered = [repo for repo in self.config.repositories if repo.name == repo_name]
        if not filtered:
            raise ValueError(f"Repository '{repo_name}' not found in configuration.")

        return filtered

    async def _process_repository(
        self,
        github_service,
        repo: RepoConfig,
        summarizer,
        save_markdown: bool,
        save_json: bool,
    ):
        """Process a single repository."""
        logger.info("Processing repository: %s", repo.name)
        completion_time = None

        try:
            # Calculate since time for this specific repository
            since = await self._calculate_since_time_for_repo(repo.name)

            # Fetch data
            repo_data = await self._fetch_repo_data(github_service, repo, since)

            # Generate summary
            summary = await self._generate_summary(repo_data, summarizer, since)

            # Save outputs asynchronously
            if save_markdown:
                await self._save_markdown_summary(repo.name, summary)

            if save_json:
                await self._save_json_report(repo.name, repo_data)

            # Record completion time for batch last run time update
            if self.config.since_last_run:
                completion_time = datetime.now(UTC)

            logger.info("Completed processing repository: %s", repo.name)
            return repo.name, completion_time, summary, repo_data

        except Exception as e:
            logger.error("Failed to process repository %s: %s", repo.name, e)
            # Return empty results but don't crash
            return repo.name, completion_time, "", {}

    async def run(
        self,
        repo_names: list[str] | None = None,
        save_json: bool = False,
        save_markdown: bool = False,
        max_concurrent_repos: int | None = None,
    ) -> None:
        """Process repositories and generate summaries.

        Args:
            repo_names: List of repository names to process. If None, processes all configured repositories.
            save_json: Whether to save JSON reports.
            save_markdown: Whether to save markdown summaries.
            max_concurrent_repos: Maximum number of concurrent repository operations.
        """
        # Initialize logging
        self._setup_logging()

        # Get max concurrent repos with overrides
        max_concurrent_repos = self._get_max_concurrent_repos(max_concurrent_repos)
        logger.info("Starting report generation with max %d concurrent repositories.", max_concurrent_repos)

        # Get services
        async with self:
            github_service = await self._get_github_service()
            summarizer = self._get_summarizer()

            # Filter repositories
            if repo_names:
                repositories = []
                for repo_name in repo_names:
                    try:
                        filtered = self._filter_repositories(repo_name)
                        repositories.extend(filtered)
                    except ValueError as e:
                        logger.error(str(e))
                        raise typer.Exit(1)
            else:
                repositories = self.config.repositories

            if len(repositories) == 1:
                logger.info("Processing single repository.")
            else:
                logger.info("Processing %d repositories concurrently.", len(repositories))

            try:
                # Create semaphore to limit concurrent repository processing
                semaphore = asyncio.Semaphore(max_concurrent_repos)

                async def process_with_semaphore(repo):
                    async with semaphore:
                        return await self._process_repository(
                            github_service,
                            repo,
                            summarizer,
                            save_markdown,
                            save_json,
                        )

                # Process all repositories concurrently (with semaphore limiting)
                tasks = [process_with_semaphore(repo) for repo in repositories]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                last_run_updates = {}
                cache_entries = []

                for i, result in enumerate(results):
                    if isinstance(result, Exception) or result is None:
                        logger.error("Repository %s failed with exception: %s", repositories[i].name, result)
                        continue

                    repo_name, completion_time, summary, repo_data = result

                    if completion_time:
                        run_key = _get_run_key(self.config_path, repo_name)
                        last_run_updates[run_key] = completion_time

                    # Collect successful summaries for batch caching
                    if summary and self.config.rss:
                        summary_id = f"{repo_name}-{completion_time.isoformat()}"
                        repo_link = f"https://github.com/{repo_name}"

                        cache_entry = {
                            "id": summary_id,
                            "title": f"Summary for {repo_name}",
                            "content": summary,
                            "link": repo_link,
                            "timestamp": completion_time.isoformat(),
                        }
                        cache_entries.append(cache_entry)

                # Batch add all summaries to cache
                if cache_entries:
                    added_count = await add_summaries_to_cache(cache_entries)
                    logger.info("Added %d summaries to cache", added_count)

                # Log rate limit info
                if github_service.rate_limit:
                    logger.info(
                        "Final rate limit: %d/%d remaining",
                        github_service.rate_limit.remaining,
                        github_service.rate_limit.limit,
                    )

                # Regenerate RSS feed from the cache
                if self.config.rss:
                    all_summaries = await load_summaries()
                    if all_summaries:
                        generate_feed_from_summaries(self.config.rss, self.config.output_dir, all_summaries)

                # Batch update last run times (async)
                if last_run_updates:
                    await set_multiple_last_run_times(last_run_updates)
                    logger.info("Updated last run times for %d repositories", len(last_run_updates))

                logger.info("Processing completed for %d repositories", len(repositories))

            except Exception as e:
                logger.error("Unexpected error during processing: %s", e)
                raise typer.Exit(1)


# FastAPI Web Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events for the FastAPI app."""
    config_path = getattr(app.state, "config_path", "config/config.toml")

    # Import here to avoid circular imports
    from github_summary.scheduler import ReportScheduler

    # Ensure output directory exists
    github_app = GitHubSummaryApp(config_path)
    os.makedirs(github_app.config.output_dir, exist_ok=True)

    # Start scheduler
    scheduler = ReportScheduler(config_path)
    await scheduler.start()

    yield

    # Stop scheduler
    await scheduler.stop()


def create_web_app(config_path: str = "config/config.toml") -> FastAPI:
    """Create FastAPI application for RSS server.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="GitHub Summary RSS Server",
        description="Simple RSS server for GitHub repository summaries",
        lifespan=lifespan,
    )

    # Store config_path in app state
    app.state.config_path = config_path

    @app.get("/healthz")
    def health_check() -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse({"status": "ok", "service": "github-summary-rss"})

    @app.get("/")
    def root() -> JSONResponse:
        """Root endpoint with service information."""
        return JSONResponse(
            {
                "service": "GitHub Summary RSS Server",
                "endpoints": {"health": "/healthz", "rss": "/rss.xml", "static": "/*"},
            }
        )

    # Load config to get output directory for static files
    github_app = GitHubSummaryApp(config_path)
    output_dir = github_app.config.output_dir

    # Mount static files (generated summaries and RSS)
    app.mount("/", StaticFiles(directory=output_dir, html=False), name="static")

    return app
