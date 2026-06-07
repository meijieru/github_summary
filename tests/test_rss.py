import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta

import pytest

from github_summary.models import RssConfig
from github_summary.rss import generate_feed_from_summaries


def _required_child(element: ET.Element, tag: str) -> ET.Element:
    child = element.find(tag)
    assert child is not None
    return child


@pytest.fixture
def rss_config():
    """Return a sample RssConfig object."""
    return RssConfig(
        title="Test RSS Feed",
        link="http://example.com/rss",
        description="A test feed for summaries.",
        filename="test_feed.xml",
    )


@pytest.fixture
def summaries_data():
    """Return a list of sample summary dictionaries."""
    return [
        {
            "id": "test/repo-1",
            "title": "Summary for test/repo-1",
            "content": "# Summary 1\n- Point 1",
            "link": "http://example.com/repo-1",
            "timestamp": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        },
        {
            "id": "test/repo-2",
            "title": "Summary for test/repo-2",
            "content": "Summary 2",
            "link": "http://example.com/repo-2",
            "timestamp": datetime.now(UTC).isoformat(),  # Newest
        },
    ]


@pytest.mark.unit
def test_generate_feed(rss_config, summaries_data, tmp_path):
    """Test that a basic RSS feed is generated correctly."""
    output_dir = str(tmp_path)
    generate_feed_from_summaries(rss_config, output_dir, summaries_data)

    rss_file = tmp_path / rss_config.filename
    assert rss_file.exists()

    # Parse the XML to verify its contents
    tree = ET.parse(str(rss_file))
    root = tree.getroot()
    channel = root.find("channel")

    assert channel is not None
    assert _required_child(channel, "title").text == rss_config.title
    assert _required_child(channel, "link").text == rss_config.link
    assert _required_child(channel, "description").text == rss_config.description

    items = channel.findall("item")
    assert len(items) == 2


@pytest.mark.unit
def test_feed_sorting(rss_config, summaries_data, tmp_path):
    """Test that entries in the feed are sorted by timestamp."""
    output_dir = str(tmp_path)
    generate_feed_from_summaries(rss_config, output_dir, summaries_data)

    rss_file = tmp_path / rss_config.filename
    tree = ET.parse(str(rss_file))
    root = tree.getroot()
    channel = root.find("channel")
    assert channel is not None
    items = channel.findall("item")

    # The newest item should be first
    assert _required_child(items[0], "title").text == "Summary for test/repo-2"
    assert _required_child(items[1], "title").text == "Summary for test/repo-1"


@pytest.mark.unit
def test_markdown_rendering(rss_config, summaries_data, tmp_path):
    """Test that markdown in the summary content is rendered to HTML."""
    output_dir = str(tmp_path)
    generate_feed_from_summaries(rss_config, output_dir, summaries_data)

    rss_file = tmp_path / rss_config.filename
    assert rss_file.exists()

    # Read the file as plain text and check for rendered HTML content
    with open(rss_file, "r") as f:
        content = f.read()

    assert "<h1>Summary 1</h1>" in content
    assert "<li>Point 1</li>" in content


@pytest.mark.unit
def test_markdown_table_rendering(rss_config, tmp_path):
    output_dir = str(tmp_path)
    summaries = [
        {
            "id": "test/repo-table",
            "title": "Summary for test/repo-table",
            "content": "| Area | Change |\n| --- | --- |\n| API | Added links |",
            "link": "http://example.com/repo-table",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    ]

    generate_feed_from_summaries(rss_config, output_dir, summaries)

    rss_file = tmp_path / rss_config.filename
    with open(rss_file, "r") as f:
        content = f.read()

    assert "<table>" in content
    assert "<td>API</td>" in content


@pytest.mark.unit
def test_generate_feed_empty_summaries(rss_config, tmp_path):
    """Test that an empty feed is generated if there are no summaries."""
    output_dir = str(tmp_path)
    generate_feed_from_summaries(rss_config, output_dir, [])

    rss_file = tmp_path / rss_config.filename
    assert rss_file.exists()

    tree = ET.parse(str(rss_file))
    root = tree.getroot()
    channel = root.find("channel")
    assert channel is not None
    items = channel.findall("item")

    assert len(items) == 0
