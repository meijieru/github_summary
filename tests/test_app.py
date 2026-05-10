"""
Tests for the core GitHubSummaryApp class.
"""

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer

from github_summary.app import GitHubSummaryApp, create_web_app
from github_summary.models import Commit
from github_summary.paths import get_default_run_dir


@pytest.fixture
def temp_config():
    """Create a temporary configuration file with RSS enabled."""
    config_content = """
output_dir = "test_output"
cache_dir = "test_cache"
log_dir = "test_log"
log_level = "INFO"
since_last_run = true
fallback_lookback_days = 7

[github]
token = "test_token"

[[repositories]]
name = "test/repo"
include_commits = true
include_pull_requests = false
include_issues = false
include_discussions = false

[llm]
api_key = "test_api_key"

[rss]
title = "Test Feed"
link = "http://example.com"
description = "Test Desc"
filename = "feed.xml"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(config_content)
        config_path = f.name

    yield config_path

    # Cleanup
    Path(config_path).unlink(missing_ok=True)


@pytest.fixture
def minimal_config():
    """Create a minimal configuration file."""
    config_content = """
output_dir = "test_output"
cache_dir = "test_cache"
log_dir = "test_log"

[github]
token = "test_token"

[[repositories]]
name = "test/repo"
include_commits = true
include_pull_requests = false
include_issues = false
include_discussions = false
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(config_content)
        config_path = f.name

    yield config_path

    # Cleanup
    Path(config_path).unlink(missing_ok=True)


class TestGitHubSummaryApp:
    """Test cases for GitHubSummaryApp."""

    def test_app_creation(self, temp_config):
        """Test that app can be created with valid config."""
        app = GitHubSummaryApp(temp_config, skip_summary=True)
        assert app.config_path == temp_config

    def test_directory_overrides(self, temp_config):
        """Test output and cache directories can be overridden at runtime."""
        app = GitHubSummaryApp(
            temp_config,
            skip_summary=True,
            output_dir="custom-output",
            cache_dir="custom-cache",
            log_dir="custom-log",
        )

        run_dir = Path(get_default_run_dir())
        assert app.config.output_dir == str((run_dir / "custom-output").resolve())
        assert app.config.cache_dir == str((run_dir / "custom-cache").resolve())
        assert app.config.log_dir == str((run_dir / "custom-log").resolve())

    @pytest.mark.asyncio
    async def test_run_with_skip_summary(self, minimal_config):
        """Test running with summary skipped."""
        with patch("github_summary.app.GitHubService") as mock_gh_service:
            mock_instance = AsyncMock()
            mock_gh_service.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.get_commits.return_value = []
            mock_instance.rate_limit = None

            app = GitHubSummaryApp(minimal_config, skip_summary=True)
            await app.run()

    @pytest.mark.asyncio
    async def test_run_with_invalid_repo(self, temp_config):
        """Test running with invalid repository name."""
        app = GitHubSummaryApp(temp_config, skip_summary=True)
        with pytest.raises(typer.Exit):
            await app.run(repo_names=["invalid/repo"])


class TestWebApp:
    """Test cases for the web application."""

    def test_create_web_app(self, minimal_config):
        """Test creating FastAPI web app."""
        web_app = create_web_app(minimal_config)
        assert web_app is not None
        assert web_app.state.config_path == minimal_config
        assert web_app.state.output_dir is None
        assert web_app.state.cache_dir is None
        assert web_app.state.log_dir is None

    def test_create_web_app_creates_output_dir(self, minimal_config, tmp_path):
        """Test creating FastAPI web app creates the static output directory."""
        output_dir = tmp_path / "web-output"

        web_app = create_web_app(minimal_config, output_dir=str(output_dir))

        assert web_app is not None
        assert output_dir.exists()


class TestIntegration:
    """Integration tests for the complete application pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_mocks(self, temp_config):
        """Test complete pipeline with mocked services and new RSS flow."""
        with (
            patch("github_summary.app.GitHubService") as mock_gh_service,
            patch("github_summary.app.Summarizer") as mock_summarizer,
            patch("github_summary.app.add_summaries_to_cache", new_callable=AsyncMock) as mock_add_to_cache,
            patch("github_summary.app.load_summaries", new_callable=AsyncMock) as mock_load_summaries,
            patch("github_summary.app.generate_feed_from_summaries") as mock_generate_feed,
            patch("github_summary.app.set_multiple_last_run_times", new_callable=AsyncMock) as mock_set_last_run,
        ):
            # 1. Mock external services and helpers
            mock_gh_instance = AsyncMock()
            mock_gh_service.return_value = mock_gh_instance
            mock_gh_instance.__aenter__.return_value = mock_gh_instance
            mock_gh_instance.get_commits.return_value = [
                Commit(sha="1", author="a", message="m", date="2025-01-01T12:00:00Z", html_url="url")
            ]
            mock_gh_instance.rate_limit = MagicMock(remaining=5000, limit=5000)

            mock_summarizer_instance = AsyncMock()
            mock_summarizer.return_value = mock_summarizer_instance
            mock_summarizer_instance.summarize.return_value = "Test summary content"

            # Mock the cache and RSS functions
            cached_summary = {
                "id": "test/repo-1",
                "content": "Test summary content",
                "title": "Summary for test/repo-1",
                "link": "http://example.com/repo-1",
                "timestamp": datetime.now(UTC).isoformat(),
            }
            mock_load_summaries.return_value = [cached_summary]

            # 2. Run the app
            app = GitHubSummaryApp(temp_config, skip_summary=False)
            await app.run(repo_names=["test/repo"])

            # 3. Assertions
            # Assert that a summary was generated
            mock_summarizer_instance.summarize.assert_called_once()

            # Assert that the new summary was added to the cache
            mock_add_to_cache.assert_called_once()
            call_args = mock_add_to_cache.call_args[0][0]  # First arg is the list of summaries
            assert len(call_args) == 1  # Should have one summary
            assert call_args[0]["title"] == "Summary for test/repo"
            assert call_args[0]["content"] == "Test summary content"

            # Assert that summaries were loaded from cache to generate the feed
            mock_load_summaries.assert_called_once_with(str((Path(get_default_run_dir()) / "test_cache").resolve()))

            # Assert that the RSS feed was generated with the loaded summaries
            mock_generate_feed.assert_called_once()
            generate_args = mock_generate_feed.call_args[0]
            assert generate_args[2] == [cached_summary]  # Check it passed the loaded summaries

            # Assert that the last run time was updated
            mock_set_last_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_without_rss_config(self, minimal_config):
        """Test that RSS functions are not called when config is missing."""
        with (
            patch("github_summary.app.GitHubService") as mock_gh_service,
            patch("github_summary.app.Summarizer") as mock_summarizer,
            patch("github_summary.summary_cache.load_summaries", new_callable=AsyncMock) as mock_load_summaries,
            patch("github_summary.app.generate_feed_from_summaries") as mock_generate_feed,
        ):
            mock_gh_instance = AsyncMock()
            mock_gh_service.return_value = mock_gh_instance
            mock_gh_instance.__aenter__.return_value = mock_gh_instance
            mock_gh_instance.get_commits.return_value = [
                Commit(sha="1", author="a", message="m", date="2025-01-01T12:00:00Z", html_url="url")
            ]
            mock_gh_instance.rate_limit = None

            mock_summarizer_instance = AsyncMock()
            mock_summarizer.return_value = mock_summarizer_instance
            mock_summarizer_instance.summarize.return_value = "A summary"

            # Run app with a config that has no [rss] section
            app = GitHubSummaryApp(minimal_config, skip_summary=False)
            await app.run()

            # Assert that none of the cache or RSS functions were called
            mock_load_summaries.assert_not_called()
            mock_generate_feed.assert_not_called()
