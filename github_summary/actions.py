"""
Actions module for GitHub summary generation using async implementation by default.
"""

import asyncio
import functools
import json
import logging
import os
from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Tuple

import typer
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
from github_summary.rss import RSSFeedManager, add_entry_to_feed
from github_summary.summarizer import Summarizer

logger = logging.getLogger(__name__)


def setup_logging(log_level: str) -> None:
    """Set up logging with console and file handlers."""
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
        level=getattr(logging, log_level.upper(), logging.INFO),
        handlers=[console_handler, file_handler],
    )


def create_summarizer(config: Config):
    """Create async summarizer if LLM config exists."""
    if not config.llm:
        return None

    llm_client = AsyncLLMClient(
        api_key=config.llm.api_key if config.llm.api_key else "",  # Should not be empty due to config validation
        base_url=config.llm.base_url,
        model_name=config.llm.model_name,
        retries=config.llm.retries,
        retry_delay=config.llm.retry_delay,
        max_concurrent=config.performance.max_concurrent_llm,
    )
    return Summarizer(
        llm_client=llm_client,
        system_prompt=config.llm.system_prompt,
        language=config.llm.language,
        timezone=config.timezone,
    )


def merge_filters(repo: RepoConfig, global_filters: FilterConfig) -> FilterConfig:
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


async def fetch_repo_data(github_service, repo: RepoConfig, config: Config, since: datetime) -> dict:
    """Fetch all data for a repository using async GitHub service."""
    logger.info("Fetching data for repository: %s", repo.name)

    filters = merge_filters(repo, config.global_filters)

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


async def calculate_since_time_for_repo_async(config: Config, config_path: str, repo_name: str) -> datetime:
    """Async version of calculate_since_time_for_repo."""
    fallback_since = datetime.now(UTC) - timedelta(days=config.fallback_lookback_days)

    if not config.since_last_run:
        return fallback_since

    # Try per-repository last run time first
    last_run_time = await get_last_run_time(config_path, repo_name)
    if last_run_time:
        return last_run_time

    # Fall back to global last run time for backward compatibility
    global_last_run_time = await get_last_run_time(config_path)
    if global_last_run_time:
        return global_last_run_time

    logger.warning("No last run time found for %s, falling back to %s days.", repo_name, config.fallback_lookback_days)
    return fallback_since


async def generate_summary(repo_data: dict, summarizer, since: datetime) -> str:
    """Generate summary from repository data using async summarizer."""
    if not summarizer:
        return ""

    logger.info("Generating summary with LLM for %s", repo_data.get("repo", "unknown"))
    summary = await summarizer.summarize(repo_data, since)
    logger.debug("Generated summary for %s (%d characters)", repo_data.get("repo", "unknown"), len(summary))
    return summary


async def save_markdown_summary(repo_name: str, summary: str, output_dir: str) -> None:
    """Async save summary as markdown file."""
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
    file_path = await loop.run_in_executor(None, functools.partial(_write_markdown, repo_name, summary, output_dir))

    logger.info("Summary saved to %s", file_path)


async def save_json_report(repo_name: str, repo_data: dict, output_dir: str) -> None:
    """Async save repository data as JSON file."""

    def _write_json(repo_name, repo_data, output_dir):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        file_name = f"{repo_name.replace('/', '_')}_summary.json"
        file_path = output_path / file_name

        with open(file_path, "w") as f:
            json.dump(repo_data, f, indent=2)

        return file_path

    loop = asyncio.get_event_loop()
    file_path = await loop.run_in_executor(None, functools.partial(_write_json, repo_name, repo_data, output_dir))

    logger.info("Report saved to %s", file_path)


def filter_repositories(config: Config, repo_name: str | None) -> list[RepoConfig]:
    """Filter repositories based on repo_name parameter."""
    if not repo_name:
        return config.repositories

    filtered = [repo for repo in config.repositories if repo.name == repo_name]
    if not filtered:
        raise ValueError(f"Repository '{repo_name}' not found in configuration.")

    return filtered


async def process_repository(
    github_service,
    repo: RepoConfig,
    summarizer,
    config: Config,
    config_path: str,
    save_markdown: bool,
    save_json: bool,
) -> Tuple[str, datetime | None, str, dict]:
    """Process a single repository asynchronously.

    Returns:
        Tuple of (repo_name, completion_time, summary, repo_data)
    """
    logger.info("Processing repository: %s", repo.name)
    completion_time = None

    try:
        # Calculate since time for this specific repository
        since = await calculate_since_time_for_repo_async(config, config_path, repo.name)

        # Fetch data
        repo_data = await fetch_repo_data(github_service, repo, config, since)

        # Generate summary
        summary = await generate_summary(repo_data, summarizer, since)

        # Save outputs asynchronously
        if save_markdown:
            await save_markdown_summary(repo.name, summary, config.output_dir)

        if save_json:
            await save_json_report(repo.name, repo_data, config.output_dir)

        # Record completion time for batch last run time update
        if config.since_last_run:
            completion_time = datetime.now(UTC)

        logger.info("Completed processing repository: %s", repo.name)
        return repo.name, completion_time, summary, repo_data

    except Exception as e:
        logger.error("Failed to process repository %s: %s", repo.name, e)
        # Return empty results but don't crash
        return repo.name, completion_time, "", {}


async def run_report(
    config_path: str,
    save: bool,
    save_markdown: bool,
    skip_summary: bool,
    repo_name: str | None = None,
    max_concurrent_repos: int | None = None,
) -> None:
    """Generate GitHub repository reports asynchronously.

    Args:
        config_path: Path to the configuration file.
        save: If True, saves the report to a JSON file.
        save_markdown: If True, saves the summary to a Markdown file.
        skip_summary: If True, skips generating and printing the LLM-based summary.
        repo_name: If provided, only runs the report for this specific repository.
        max_concurrent_repos: Maximum number of concurrent repository operations. If None, uses config value.
    """

    # Load configuration
    try:
        config = load_config(config_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error("Configuration error: %s", e)
        raise typer.Exit(1)

    # Use config value if not overridden
    if max_concurrent_repos is None:
        max_concurrent_repos = config.performance.max_concurrent_repos

    # Allow environment variable override
    env_concurrent = os.environ.get("GHSUM_CONCURRENT_REPOS")
    if env_concurrent:
        try:
            max_concurrent_repos = int(env_concurrent)
            logger.info("Using GHSUM_CONCURRENT_REPOS environment variable: %d", max_concurrent_repos)
        except ValueError:
            logger.warning("Invalid GHSUM_CONCURRENT_REPOS value: %s, using config/default", env_concurrent)

    logger.info("Starting report generation with max %d concurrent repositories.", max_concurrent_repos)
    # Setup logging
    setup_logging(config.log_level)

    # Validate GitHub token
    github_token = config.github.token or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN not found in config or environment variables.")
        raise typer.Exit(1)

    # Create services
    try:
        github_service = GitHubService(github_token)
        summarizer = create_summarizer(config) if not skip_summary else None
    except Exception as e:
        logger.error("Service creation error: %s", e)
        raise typer.Exit(1)

    # Validate LLM config if needed
    if not skip_summary and not summarizer:
        logger.error("LLM configuration not found in config.toml.")
        raise typer.Exit(1)

    # Filter repositories
    try:
        repositories = filter_repositories(config, repo_name)
    except ValueError as e:
        logger.error(str(e))
        raise typer.Exit(1)

    if len(repositories) == 1:
        logger.info("Processing single repository.")
    else:
        logger.info("Processing %d repositories concurrently.", len(repositories))

    # Process repositories
    try:
        # Use RSS context manager if configured, otherwise None
        rss_manager = RSSFeedManager(config.rss, config.output_dir) if config.rss else None

        with rss_manager or nullcontext() as feed:
            async with github_service as gh_service:
                # Create semaphore to limit concurrent repository processing
                semaphore = asyncio.Semaphore(max_concurrent_repos)

                async def process_with_semaphore(repo):
                    async with semaphore:
                        return await process_repository(
                            gh_service,
                            repo,
                            summarizer,
                            config,
                            config_path,
                            save_markdown,
                            save,
                        )

                # Process all repositories concurrently (with semaphore limiting)
                tasks = [process_with_semaphore(repo) for repo in repositories]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                last_run_updates = {}
                summaries_for_rss = []

                for i, result in enumerate(results):
                    if isinstance(result, Exception) or result is None:
                        logger.error("Repository %s failed with exception: %s", repositories[i].name, result)
                        continue

                    repo_name, completion_time, summary, repo_data = result

                    # Collect last run time updates for batch processing
                    if completion_time:
                        run_key = _get_run_key(config_path, repo_name)
                        last_run_updates[run_key] = completion_time

                    # Collect summaries for RSS
                    if summary and feed:
                        summaries_for_rss.append((summary, repo_name))

                # Log rate limit info
                if gh_service.rate_limit:
                    logger.info(
                        "Final rate limit: %d/%d remaining",
                        gh_service.rate_limit.remaining,
                        gh_service.rate_limit.limit,
                    )

            # Add all summaries to RSS feed after processing completes
            if feed:
                for summary, repo_name in summaries_for_rss:
                    add_entry_to_feed(feed, summary, repo_name)

            # Batch update last run times (async)
            if last_run_updates:
                await set_multiple_last_run_times(last_run_updates)
                logger.info("Updated last run times for %d repositories", len(last_run_updates))

        logger.info("Processing completed for %d repositories", len(repositories))

    except Exception as e:
        logger.error("Unexpected error during processing: %s", e)
        raise typer.Exit(1)
