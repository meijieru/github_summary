import json
import logging
import os
from datetime import UTC, datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

import typer
from rich.logging import RichHandler

from github_summary.config import load_config
from github_summary.github_client import GitHubService
from github_summary.last_run_manager import get_last_run_time, set_last_run_time
from github_summary.llm_client import OpenAICompatibleLLMClient
from github_summary.models import (
    Commit,
    Config,
    Discussion,
    FilterConfig,
    Issue,
    PullRequest,
    RepoConfig,
)
from github_summary.rss import add_entry_to_feed, create_rss_feed, save_rss_feed
from github_summary.summarizer import Summarizer

logger = logging.getLogger(__name__)


def _setup_logging(log_level: str):
    log_dir = Path("log")
    log_dir.mkdir(exist_ok=True)

    # Console handler
    console_handler = RichHandler(
        rich_tracebacks=True,
        tracebacks_show_locals=False,
    )
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    # File handler
    file_handler = RotatingFileHandler(log_dir / "github_summary.log", maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        handlers=[console_handler, file_handler],
    )


def _get_services(config_path: str) -> tuple[Config, GitHubService, Summarizer | None]:
    """Loads the configuration and initializes GitHubService and an optional LLM client and Summarizer.

    Args:
        config_path: The path to the configuration file.

    Returns:
        A tuple containing the loaded Config, GitHubService instance, and an optional Summarizer instance.

    Raises:
        typer.Exit: If the configuration file is not found, is invalid, or if the GitHub token is missing.
    """
    try:
        config = load_config(config_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error("Error loading configuration: %s", e)
        raise typer.Exit(1)

    github_token = config.github.token or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN not found in config or environment variables.")
        raise typer.Exit(1)

    service = GitHubService(token=github_token)

    llm_client = None
    summarizer = None
    if config.llm:
        llm_client = OpenAICompatibleLLMClient(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            model_name=config.llm.model_name,
            retries=config.llm.retries,
            retry_delay=config.llm.retry_delay,
        )
        summarizer = Summarizer(
            llm_client=llm_client,
            system_prompt=config.llm.system_prompt,
            language=config.llm.language,
            timezone=config.timezone,
        )
    return config, service, summarizer


def _get_repo_data(
    repo: RepoConfig,
    service: GitHubService,
    config: Config,
    since: datetime,
) -> tuple[list[Commit], list[PullRequest], list[Issue], list[Discussion]]:
    """Fetches repository data (commits, pull requests, issues, discussions) based on provided filters.

    Args:
        repo: The repository configuration.
        service: The GitHubService instance.
        config: The overall application configuration.
        since: A datetime object indicating the start time for fetching data.

    Returns:
        A tuple containing lists of Commit, PullRequest, Issue, and Discussion objects.
    """
    logger.info("Fetching data for repository: %s", repo.name)
    merged_filters = config.global_filters.model_copy(deep=True) if config.global_filters else FilterConfig()

    if repo.filters:
        for field in ["commits", "pull_requests", "issues", "discussions"]:
            repo_filter_subconfig = getattr(repo.filters, field)
            if repo_filter_subconfig:
                current_merged_subconfig = getattr(merged_filters, field)
                if current_merged_subconfig:
                    setattr(
                        merged_filters,
                        field,
                        current_merged_subconfig.model_copy(
                            update=repo_filter_subconfig.model_dump(exclude_unset=True)
                        ),
                    )
                else:
                    setattr(merged_filters, field, repo_filter_subconfig)

    commits = service.get_commits(repo, merged_filters, since)
    pull_requests = service.get_pull_requests(repo, merged_filters, since)
    issues = service.get_issues(repo, merged_filters, since)
    discussions = service.get_discussions(repo, merged_filters, since)

    return commits, pull_requests, issues, discussions


def run_report(
    config_path: str,
    save: bool,
    save_markdown: bool,
    skip_summary: bool,
    repo_name: str | None = None,
):
    """Runs the GitHub activity report, fetching data and optionally generating a summary.

    Args:
        config_path: Path to the configuration file.
        save: If True, saves the report to a JSON file.
        save_markdown: If True, saves the summary to a Markdown file.
        skip_summary: If True, skips generating and printing the LLM-based summary.
        repo_name: If provided, only runs the report for this specific repository.
    """
    logger.info("Starting report generation.")
    config, service, summarizer = _get_services(config_path)
    _setup_logging(config.log_level)

    if not skip_summary and not summarizer:
        logger.error("LLM configuration not found in config.toml.")
        raise typer.Exit(1)

    since = datetime.now(UTC) - timedelta(days=config.fallback_lookback_days)
    if config.since_last_run:
        last_run_time = get_last_run_time(config_path)

        if not last_run_time:
            logger.warning("No last run time found, falling back to %s days.", config.fallback_lookback_days)
        else:
            since = last_run_time

    if config.rss and config.rss.enabled:
        feed = create_rss_feed(config.rss)

    # Filter repositories if a specific repo is requested
    repositories = config.repositories
    if repo_name:
        repositories = [repo for repo in config.repositories if repo.name == repo_name]
        if not repositories:
            logger.error("Repository '%s' not found in configuration.", repo_name)
            raise typer.Exit(1)

    for repo in repositories:
        logger.info("Generating full report for %s", repo.name)
        logger.info("Processing repository: %s", repo.name)
        commits, pull_requests, issues, discussions = _get_repo_data(repo, service, config, since)

        output_data = {
            "repo": repo.name,
            "commits": [c.model_dump() for c in commits],
            "pull_requests": [pr.model_dump() for pr in pull_requests],
            "issues": [i.model_dump() for i in issues],
            "discussions": [d.model_dump() for d in discussions],
        }
        summary = ""
        if not skip_summary and summarizer:
            if not commits and not pull_requests and not issues and not discussions:
                logger.info("No new updates found.")
                summary = "No new updates."
            else:
                logger.info("Generating summary with LLM")
                summary = summarizer.summarize(output_data, since)
                logger.debug(summary)

            if config.rss and config.rss.enabled:
                add_entry_to_feed(feed, summary, repo.name)

        if save_markdown and summary:
            output_dir = Path(config.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            file_name = f"{repo.name.replace('/', '_')}_summary.md"
            file_path = output_dir / file_name
            with open(file_path, "w") as f:
                f.write(f"## Summary for {repo.name}\n\n{summary}")
            logger.info("Summary saved to %s", file_path)

        if save:
            output_dir = Path(config.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            file_name = f"{repo.name.replace('/', '_')}_summary.json"
            file_path = output_dir / file_name
            with open(file_path, "w") as f:
                json.dump(output_data, f, indent=2)
            logger.info("Report saved to %s", file_path)

    if config.since_last_run:
        set_last_run_time(config_path)

    if config.rss and config.rss.enabled:
        save_rss_feed(feed, config.rss, config.output_dir)
