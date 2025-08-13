from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from github_summary.actions import run_report
from github_summary.models import Config, GitHubConfig, LLMConfig, RepoConfig


@pytest.fixture
def mock_config():
    """Create a test application configuration."""
    return Config(
        github=GitHubConfig(token="test_token"),
        repositories=[RepoConfig(name="test/repo")],
        llm=LLMConfig(
            api_key="test_api_key",
            base_url="https://api.openai.com/v1",
            model_name="gpt-4",
        ),
    )


class TestIntegration:
    """Integration test cases."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_async_workflow(self, mock_config):
        """Test complete async workflow integration."""
        with (
            patch("github_summary.actions.GitHubService") as mock_github_service_class,
            patch("github_summary.actions.create_summarizer") as mock_create_summarizer,
            patch("github_summary.actions.setup_logging"),
            patch("github_summary.actions.filter_repositories") as mock_filter_repos,
            patch("github_summary.actions.set_multiple_last_run_times") as mock_set_times,
            patch("github_summary.actions.load_config") as mock_load_config,
        ):
            # Setup mocks
            mock_load_config.return_value = mock_config

            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.__aexit__.return_value = None
            mock_github_service_class.return_value = mock_service

            mock_summarizer = AsyncMock()
            mock_create_summarizer.return_value = mock_summarizer

            mock_filter_repos.return_value = [RepoConfig(name="test/repo")]

            # Mock process_repository
            with patch("github_summary.actions.process_repository") as mock_process:
                mock_process.return_value = ("test/repo", datetime.now(UTC), "Test summary", {})

                # Run the async workflow
                await run_report(
                    config_path="test_config.toml",
                    save=False,
                    save_markdown=False,
                    skip_summary=False,
                    repo_name=None,
                    max_concurrent_repos=2,
                )

                # Verify calls
                mock_github_service_class.assert_called_once()
                mock_process.assert_called_once()
                mock_set_times.assert_called_once()
