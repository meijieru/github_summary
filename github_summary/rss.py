import logging
from pathlib import Path

from feedgen.feed import FeedGenerator

from github_summary.models import RssConfig

logger = logging.getLogger(__name__)


def create_rss_feed(rss_config: RssConfig) -> FeedGenerator:
    """Initializes and returns a new FeedGenerator instance based on the provided configuration.

    Args:
        rss_config: The RSS configuration.

    Returns:
        A FeedGenerator instance.
    """
    feed = FeedGenerator()
    feed.title(rss_config.title)
    feed.link(href=rss_config.link, rel="alternate")
    feed.description(rss_config.description)
    return feed


def add_entry_to_feed(feed: FeedGenerator, summary: str, repo_name: str):
    """Adds a new entry to the RSS feed.

    Args:
        feed: The FeedGenerator instance.
        summary: The summary text to add.
        repo_name: The name of the repository.
    """
    entry = feed.add_entry()
    entry.title(f"Summary for {repo_name}")
    entry.description(summary)


def save_rss_feed(feed: FeedGenerator, rss_config: RssConfig, output_dir: str):
    """Saves the RSS feed to a file.

    Args:
        feed: The FeedGenerator instance.
        rss_config: The RSS configuration.
        output_dir: The directory to save the feed in.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / rss_config.filename
    feed.rss_file(str(file_path))
    logger.info("RSS feed saved to %s", file_path)
