import logging
from datetime import datetime
from pathlib import Path

from feedgen.feed import FeedGenerator
from markdown_it import MarkdownIt

from github_summary.models import RssConfig

logger = logging.getLogger(__name__)


def generate_feed_from_summaries(rss_config: RssConfig, output_dir: str, summaries: list[dict]):
    """
    Generates and saves an RSS feed from a list of summary dictionaries.

    Args:
        rss_config: The RSS configuration.
        output_dir: The directory to save the feed in.
        summaries: A list of summary dictionaries, each with 'id', 'title', 'content', 'link', and 'timestamp'.
    """
    logger.info("Generating RSS feed from %d summaries.", len(summaries))
    md = MarkdownIt()
    feed = FeedGenerator()
    feed.title(rss_config.title)
    feed.link(href=rss_config.link, rel="alternate")
    feed.description(rss_config.description)

    # Sort summaries by timestamp, oldest first.
    # Assuming feed.add_entry() prepends, this will result in a newest-to-oldest feed.
    sorted_summaries = sorted(summaries, key=lambda x: datetime.fromisoformat(x["timestamp"]))

    for summary_data in sorted_summaries:
        html_content = md.render(summary_data["content"])
        entry = feed.add_entry()
        entry.id(summary_data["id"])
        entry.title(summary_data["title"])
        entry.link(href=summary_data["link"])
        entry.content(html_content, type="CDATA")
        entry.pubDate(datetime.fromisoformat(summary_data["timestamp"]))

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / rss_config.filename
    feed.rss_file(str(file_path))
    logger.info("RSS feed saved to %s", file_path)
