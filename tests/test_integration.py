"""
Integration tests for the GitHubSummaryApp.
"""

from unittest.mock import AsyncMock, patch

import pytest

from github_summary.app import GitHubSummaryApp
from github_summary.models import (
    Commit,
    Config,
    GitHubConfig,
    LLMConfig,
    RepoConfig,
)


@pytest.fixture
def mock_config():
    """Create a test application configuration."""
    return Config(
        github=GitHubConfig(token="test_token"),
        repositories=[RepoConfig(name="test/repo", include_commits=True)],
        llm=LLMConfig(
            api_key="test_api_key",
            base_url="https://api.openai.com/v1",
            model_name="gpt-4",
        ),
    )


class TestIntegration:
    """Integration test cases for the new GitHubSummaryApp."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_async_workflow_new_app(self, mock_config):
        """Test complete async workflow integration with new GitHubSummaryApp."""
        with (
            patch("github_summary.app.GitHubService") as mock_github_service_class,
            patch("github_summary.app.AsyncLLMClient") as mock_llm_client,
            patch("github_summary.app.Summarizer") as mock_summarizer_class,
            patch("github_summary.app.set_multiple_last_run_times") as mock_set_times,
            patch("github_summary.config.load_config") as mock_load_config,
        ):
            # Setup mocks
            mock_load_config.return_value = mock_config

            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.__aexit__.return_value = None
            mock_service.get_commits.return_value = [
                Commit(sha="1", author="a", message="m", date="2025-01-01T12:00:00Z", html_url="url")
            ]
            mock_service.get_pull_requests.return_value = []
            mock_service.get_issues.return_value = []
            mock_service.get_discussions.return_value = []
            mock_service.rate_limit = None
            mock_github_service_class.return_value = mock_service

            mock_llm_instance = AsyncMock()
            mock_llm_client.return_value = mock_llm_instance

            mock_summarizer = AsyncMock()
            mock_summarizer.summarize.return_value = "Test summary"
            mock_summarizer_class.return_value = mock_summarizer

            mock_set_times.return_value = None

            # Create and run app
            app = GitHubSummaryApp("test_config.toml", skip_summary=False)
            # Mock the app's config property to avoid file loading
            app._config = mock_config

            await app.run(repo_names=["test/repo"], save_json=False, save_markdown=False, max_concurrent_repos=1)

            # Verify interactions
            mock_github_service_class.assert_called_once()
            mock_summarizer.summarize.assert_called_once()
