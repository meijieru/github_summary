import json
import logging
import os
from contextlib import nullcontext
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
    Config,
    FilterConfig,
    RepoConfig,
)
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


def create_github_service(config: Config, enable_retry: bool = True) -> GitHubService:
    """Create GitHub service with token from config or environment."""
    github_token = config.github.token or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN not found in config or environment variables.")
    return GitHubService(token=github_token, enable_retry=enable_retry)


def create_summarizer(config: Config) -> Summarizer | None:
    """Create summarizer if LLM config exists."""
    if not config.llm:
        return None

    llm_client = OpenAICompatibleLLMClient(
        api_key=config.llm.api_key,
        base_url=config.llm.base_url,
        model_name=config.llm.model_name,
        retries=config.llm.retries,
        retry_delay=config.llm.retry_delay,
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


def fetch_repo_data(repo: RepoConfig, github_service: GitHubService, config: Config, since: datetime) -> dict:
    """Fetch all data for a repository."""
    logger.info("Fetching data for repository: %s", repo.name)

    filters = merge_filters(repo, config.global_filters)

    commits = github_service.get_commits(repo, filters, since)
    pull_requests = github_service.get_pull_requests(repo, filters, since)
    issues = github_service.get_issues(repo, filters, since)
    discussions = github_service.get_discussions(repo, filters, since)

    return {
        "repo": repo.name,
        "commits": [c.model_dump() for c in commits],
        "pull_requests": [pr.model_dump() for pr in pull_requests],
        "issues": [i.model_dump() for i in issues],
        "discussions": [d.model_dump() for d in discussions],
    }


def calculate_since_time(config: Config, config_path: str) -> datetime:
    """Calculate the 'since' time based on config and last run."""
    fallback_since = datetime.now(UTC) - timedelta(days=config.fallback_lookback_days)

    if not config.since_last_run:
        return fallback_since

    last_run_time = get_last_run_time(config_path)
    if last_run_time:
        return last_run_time

    logger.warning("No last run time found, falling back to %s days.", config.fallback_lookback_days)
    return fallback_since


def calculate_since_time_for_repo(config: Config, config_path: str, repo_name: str) -> datetime:
    """Calculate the 'since' time for a specific repository based on config and last run."""
    fallback_since = datetime.now(UTC) - timedelta(days=config.fallback_lookback_days)

    if not config.since_last_run:
        return fallback_since

    # Try per-repository last run time first
    last_run_time = get_last_run_time(config_path, repo_name)
    if last_run_time:
        return last_run_time

    # Fall back to global last run time for backward compatibility
    global_last_run_time = get_last_run_time(config_path)
    if global_last_run_time:
        return global_last_run_time

    logger.warning("No last run time found for %s, falling back to %s days.", repo_name, config.fallback_lookback_days)
    return fallback_since


def filter_repositories(config: Config, repo_name: str | None) -> list[RepoConfig]:
    """Filter repositories based on repo_name parameter."""
    if not repo_name:
        return config.repositories

    filtered = [repo for repo in config.repositories if repo.name == repo_name]
    if not filtered:
        raise ValueError(f"Repository '{repo_name}' not found in configuration.")

    return filtered


def generate_summary(repo_data: dict, summarizer: Summarizer | None, since: datetime) -> str:
    """Generate summary from repository data."""
    if not summarizer:
        return ""

    has_data = any(repo_data[key] for key in ["commits", "pull_requests", "issues", "discussions"])
    if not has_data:
        logger.info("No new updates found.")
        return "No new updates."

    logger.info("Generating summary with LLM")
    summary = summarizer.summarize(repo_data, since)
    logger.debug(summary)
    return summary


def save_markdown_summary(repo_name: str, summary: str, output_dir: str) -> None:
    """Save summary as markdown file."""
    if not summary:
        return

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_name = f"{repo_name.replace('/', '_')}_summary.md"
    file_path = output_path / file_name

    with open(file_path, "w") as f:
        f.write(f"## Summary for {repo_name}\n\n{summary}")

    logger.info("Summary saved to %s", file_path)


def save_json_report(repo_name: str, repo_data: dict, output_dir: str) -> None:
    """Save repository data as JSON file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_name = f"{repo_name.replace('/', '_')}_summary.json"
    file_path = output_path / file_name

    with open(file_path, "w") as f:
        json.dump(repo_data, f, indent=2)

    logger.info("Report saved to %s", file_path)


def process_repository(
    repo: RepoConfig,
    github_service: GitHubService,
    summarizer: Summarizer | None,
    config: Config,
    config_path: str,
    feed,
    save_markdown: bool,
    save_json: bool,
) -> None:
    """Process a single repository: fetch data, generate summary, save results."""
    logger.info("Processing repository: %s", repo.name)

    # Calculate since time for this specific repository
    since = calculate_since_time_for_repo(config, config_path, repo.name)

    # Fetch data
    repo_data = fetch_repo_data(repo, github_service, config, since)

    # Generate summary
    summary = generate_summary(repo_data, summarizer, since)

    # Add to RSS feed
    if feed and summary:
        add_entry_to_feed(feed, summary, repo.name)

    # Save outputs
    if save_markdown:
        save_markdown_summary(repo.name, summary, config.output_dir)

    if save_json:
        save_json_report(repo.name, repo_data, config.output_dir)

    # Update last run time for this repository if since_last_run is enabled
    if config.since_last_run:
        set_last_run_time(config_path, repo.name)


def run_report(
    config_path: str,
    save: bool,
    save_markdown: bool,
    skip_summary: bool,
    repo_name: str | None = None,
) -> None:
    """Runs the GitHub activity report, fetching data and optionally generating a summary.

    Args:
        config_path: Path to the configuration file.
        save: If True, saves the report to a JSON file.
        save_markdown: If True, saves the summary to a Markdown file.
        skip_summary: If True, skips generating and printing the LLM-based summary.
        repo_name: If provided, only runs the report for this specific repository.
    """
    # Load config
    logger.info("Starting report generation.")
    # Load configuration
    try:
        config = load_config(config_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error("Configuration error: %s", e)
        raise typer.Exit(1)

    setup_logging(config.log_level)

    # Create services
    try:
        github_service = create_github_service(config)
        summarizer = create_summarizer(config) if not skip_summary else None
    except ValueError as e:
        logger.error("Service creation error: %s", e)
        raise typer.Exit(1)

    # Validate LLM config if needed
    if not skip_summary and not summarizer:
        logger.error("LLM configuration not found in config.toml.")
        raise typer.Exit(1)

    # Calculate time range and filter repos
    try:
        repositories = filter_repositories(config, repo_name)
    except ValueError as e:
        logger.error(str(e))
        raise typer.Exit(1)

    # Process all repositories
    try:
        # Use RSS context manager if configured, otherwise None
        rss_manager = RSSFeedManager(config.rss, config.output_dir) if config.rss else None

        with rss_manager or nullcontext() as feed:
            for repo in repositories:
                process_repository(
                    repo=repo,
                    github_service=github_service,
                    summarizer=summarizer if not skip_summary else None,
                    config=config,
                    config_path=config_path,
                    feed=feed,
                    save_markdown=save_markdown,
                    save_json=save,
                )

    except Exception as e:
        logger.error("Unexpected error: %s", e)
        raise typer.Exit(1)
