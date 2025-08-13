import logging
from pathlib import Path

from feedgen.feed import FeedGenerator
from markdown_it import MarkdownIt

from github_summary.models import RssConfig

logger = logging.getLogger(__name__)


class RSSFeedManager:
    """Context manager for handling RSS feed creation, management, and saving."""

    def __init__(self, rss_config: RssConfig, output_dir: str):
        """Initialize the RSS feed manager.

        Args:
            rss_config: The RSS configuration.
            output_dir: The directory to save the feed in.
        """
        self.rss_config = rss_config
        self.output_dir = output_dir
        self.feed: FeedGenerator | None = None

    def __enter__(self) -> FeedGenerator:
        """Create and return the RSS feed."""
        self.feed = FeedGenerator()
        self.feed.title(self.rss_config.title)
        self.feed.link(href=self.rss_config.link, rel="alternate")
        self.feed.description(self.rss_config.description)
        return self.feed

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Save the RSS feed on exit."""
        if self.feed:
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            file_path = output_path / self.rss_config.filename
            self.feed.rss_file(str(file_path))
            logger.info("RSS feed saved to %s", file_path)


def add_entry_to_feed(feed: FeedGenerator, summary: str, repo_name: str):
    """Adds a new entry to the RSS feed.

    Args:
        feed: The FeedGenerator instance.
        summary: The summary text to add.
        repo_name: The name of the repository.
    """
    md = MarkdownIt()
    html_summary = md.render(summary)

    entry = feed.add_entry()
    entry.title(f"Summary for {repo_name}")
    entry.description(summary)
    entry.content(html_summary, type="html")
