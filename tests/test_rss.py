from github_summary.models import RssConfig
from github_summary.rss import RSSFeedManager, add_entry_to_feed


def test_rss_context_manager(tmp_path):
    """Test RSS context manager"""
    rss_config = RssConfig(title="Context Test", filename="context_test.xml")
    output_dir = tmp_path / "output"

    with RSSFeedManager(rss_config, str(output_dir)) as feed:
        # Add an entry to test the feed works
        add_entry_to_feed(feed, "Test summary", "owner/repo")

    # After context exits, file should be saved
    rss_file = output_dir / "context_test.xml"
    assert rss_file.exists()
    with open(rss_file) as f:
        content = f.read()
        assert "Context Test" in content
        assert "Summary for owner/repo" in content


def test_create_rss_feed(tmp_path):
    """Test RSS feed creation via RSSFeedManager"""
    rss_config = RssConfig(
        title="Test Feed",
        link="http://example.com/rss",
        description="Test feed description",
        filename="test.xml",
    )

    with RSSFeedManager(rss_config, str(tmp_path)) as feed:
        assert feed.title() == "Test Feed"
        assert feed.link() == [{"href": "http://example.com/rss", "rel": "alternate"}]
        assert feed.description() == "Test feed description"


def test_add_entry_to_feed(tmp_path):
    """Test adding entries to RSS feed via RSSFeedManager"""
    rss_config = RssConfig()

    with RSSFeedManager(rss_config, str(tmp_path)) as feed:
        add_entry_to_feed(feed, "Test summary", "owner/repo")
        assert len(feed.entry()) == 1
        entry = feed.entry()[0]
        assert entry.title() == "Summary for owner/repo"
        assert entry.description() == "Test summary"


def test_add_entry_to_feed_with_markdown(tmp_path):
    """Test adding markdown entries to RSS feed via RSSFeedManager"""
    rss_config = RssConfig()

    with RSSFeedManager(rss_config, str(tmp_path)) as feed:
        markdown_summary = """# Heading

- Item 1
- Item 2"""
        add_entry_to_feed(feed, markdown_summary, "owner/repo")
        assert len(feed.entry()) == 1
        entry = feed.entry()[0]
        assert entry.title() == "Summary for owner/repo"
        assert entry.description() == markdown_summary
        # Content should be rendered HTML
        content = entry.content()["content"]
        assert "<h1>Heading</h1>" in content
        assert "<li>Item 1</li>" in content


def test_save_rss_feed(tmp_path):
    """Test RSS feed saving via RSSFeedManager"""
    rss_config = RssConfig(title="Save Test", filename="test.xml")

    with RSSFeedManager(rss_config, str(tmp_path)) as feed:
        add_entry_to_feed(feed, "Save test content", "save/repo")

    # File should be automatically saved on context exit
    rss_file = tmp_path / "test.xml"
    assert rss_file.exists()
    with open(rss_file) as f:
        content = f.read()
        assert "Save Test" in content
        assert "save/repo" in content
