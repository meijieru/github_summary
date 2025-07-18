from github_summary.models import RssConfig
from github_summary.rss import add_entry_to_feed, create_rss_feed, save_rss_feed


def test_create_rss_feed():
    rss_config = RssConfig(
        enabled=True,
        title="Test Feed",
        link="http://example.com/rss",
        description="Test feed description",
        filename="test.xml",
    )
    feed = create_rss_feed(rss_config)
    assert feed.title() == "Test Feed"
    assert feed.link() == [{"href": "http://example.com/rss", "rel": "alternate"}]
    assert feed.description() == "Test feed description"


def test_add_entry_to_feed():
    rss_config = RssConfig()
    feed = create_rss_feed(rss_config)
    add_entry_to_feed(feed, "Test summary", "owner/repo")
    assert len(feed.entry()) == 1
    entry = feed.entry()[0]
    assert entry.title() == "Summary for owner/repo"
    assert entry.description() == "Test summary"


def test_save_rss_feed(tmp_path):
    rss_config = RssConfig(filename="test.xml")
    feed = create_rss_feed(rss_config)
    output_dir = tmp_path / "output"
    save_rss_feed(feed, rss_config, str(output_dir))
    rss_file = output_dir / "test.xml"
    assert rss_file.exists()
    with open(rss_file) as f:
        content = f.read()
        assert "<title>GitHub Repository Summaries</title>" in content
