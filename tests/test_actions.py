from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from github_summary.actions import (
    fetch_repo_data,
    generate_summary,
    process_repository,
)
from github_summary.models import Config, GitHubConfig, LLMConfig, RepoConfig


@pytest.fixture
def mock_repo_config():
    """Create a test repository configuration."""
    return RepoConfig(name="test/repo")


@pytest.fixture
def mock_config(mock_repo_config):
    """Create a test application configuration."""
    return Config(
        github=GitHubConfig(token="test_token"),
        repositories=[mock_repo_config],
        llm=LLMConfig(
            api_key="test_api_key",
            base_url="https://api.openai.com/v1",
            model_name="gpt-4",
        ),
    )


class TestAsyncActions:
    """Test cases for async actions functions."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_repo_data(self, mock_repo_config, mock_config):
        """Test async repository data fetching."""
        mock_github_service = AsyncMock()
        mock_github_service.get_commits.return_value = []
        mock_github_service.get_pull_requests.return_value = []
        mock_github_service.get_issues.return_value = []
        mock_github_service.get_discussions.return_value = []

        since = datetime.now(UTC) - timedelta(days=1)

        result = await fetch_repo_data(mock_github_service, mock_repo_config, mock_config, since)

        assert result["repo"] == "test/repo"
        assert "commits" in result
        assert "pull_requests" in result
        assert "issues" in result
        assert "discussions" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_summary(self):
        """Test async summary generation."""
        mock_summarizer = AsyncMock()
        mock_summarizer.summarize.return_value = "Test summary"

        repo_data = {
            "repo": "test/repo",
            "commits": [{"sha": "abc123"}],
            "pull_requests": [],
            "issues": [],
            "discussions": [],
        }

        since = datetime.now(UTC) - timedelta(days=1)

        result = await generate_summary(repo_data, mock_summarizer, since)

        assert result == "Test summary"
        mock_summarizer.summarize.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_repository(self, mock_config, mock_repo_config):
        """Test async repository processing."""
        mock_github_service = AsyncMock()
        mock_summarizer = AsyncMock()

        # Mock fetch_repo_data
        with patch("github_summary.actions.fetch_repo_data") as mock_fetch:
            mock_fetch.return_value = {
                "repo": "test/repo",
                "commits": [],
                "pull_requests": [],
                "issues": [],
                "discussions": [],
            }

            # Mock generate_summary
            with patch("github_summary.actions.generate_summary") as mock_gen_summary:
                mock_gen_summary.return_value = "Test summary"

                # Mock file operations
                with (
                    patch("github_summary.actions.save_markdown_summary"),
                    patch("github_summary.actions.save_json_report"),
                ):
                    result = await process_repository(
                        mock_github_service,
                        mock_repo_config,
                        mock_summarizer,
                        mock_config,
                        "test_config.toml",
                        True,  # save_markdown
                        True,  # save_json
                    )

                    repo_name, completion_time, summary, repo_data = result

                    assert repo_name == "test/repo"
                    assert completion_time is not None
                    assert summary == "Test summary"
                    assert repo_data["repo"] == "test/repo"
