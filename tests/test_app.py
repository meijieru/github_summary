"""
Tests for the core GitHubSummaryApp class.
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer

from github_summary.app import GitHubSummaryApp, create_web_app


@pytest.fixture
def temp_config():
    """Create a temporary configuration file."""
    config_content = """
[github]
token = "test_token"

[[repositories]]
name = "test/repo"
include_commits = true
include_pull_requests = true
include_issues = true
include_discussions = false

[llm]
api_key = "test_api_key"
base_url = "https://api.openai.com/v1"
model_name = "gpt-4o-mini"
language = "English"

[performance]
max_concurrent_repos = 2
max_concurrent_llm = 1

output_dir = "test_output"
log_level = "INFO"
since_last_run = false
fallback_lookback_days = 7
timezone = "UTC"
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
[github]
token = "test_token"

[[repositories]]
name = "test/repo"

output_dir = "test_output"
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
        assert app.skip_summary is True
        assert app._config is None  # Lazy loading

    def test_config_loading(self, temp_config):
        """Test configuration loading and caching."""
        app = GitHubSummaryApp(temp_config)

        # First access loads config
        config = app.config
        assert config is not None
        assert len(config.repositories) == 1
        assert config.repositories[0].name == "test/repo"

        # Second access uses cached config
        config2 = app.config
        assert config is config2  # Same object

    def test_invalid_config_path(self):
        """Test handling of invalid config path."""
        app = GitHubSummaryApp("nonexistent.toml")

        with pytest.raises((SystemExit, typer.Exit)):  # typer.Exit can raise different exceptions
            _ = app.config

    @pytest.mark.asyncio
    async def test_context_manager(self, minimal_config):
        """Test app as async context manager."""
        async with GitHubSummaryApp(minimal_config, skip_summary=True) as app:
            assert app is not None
            config = app.config
            assert config is not None

    def test_logging_setup(self, temp_config):
        """Test logging initialization."""
        app = GitHubSummaryApp(temp_config)

        # Logging should be initialized once
        assert not app._logging_initialized
        app._setup_logging()
        assert app._logging_initialized

        # Second call should be no-op
        app._setup_logging()
        assert app._logging_initialized

    def test_max_concurrent_repos_default(self, temp_config):
        """Test default max concurrent repos from config."""
        app = GitHubSummaryApp(temp_config)
        max_concurrent = app._get_max_concurrent_repos()
        assert max_concurrent == 2  # From config

    def test_max_concurrent_repos_override(self, temp_config):
        """Test max concurrent repos with override."""
        app = GitHubSummaryApp(temp_config)
        max_concurrent = app._get_max_concurrent_repos(override=5)
        assert max_concurrent == 5

    @patch.dict("os.environ", {"GHSUM_CONCURRENT_REPOS": "8"})
    def test_max_concurrent_repos_env_var(self, temp_config):
        """Test max concurrent repos with environment variable."""
        app = GitHubSummaryApp(temp_config)
        max_concurrent = app._get_max_concurrent_repos()
        assert max_concurrent == 8

    def test_filter_repositories_all(self, temp_config):
        """Test filtering all repositories."""
        app = GitHubSummaryApp(temp_config)
        repositories = app._filter_repositories(None)
        assert len(repositories) == 1
        assert repositories[0].name == "test/repo"

    def test_filter_repositories_specific(self, temp_config):
        """Test filtering specific repository."""
        app = GitHubSummaryApp(temp_config)
        repositories = app._filter_repositories("test/repo")
        assert len(repositories) == 1
        assert repositories[0].name == "test/repo"

    def test_filter_repositories_not_found(self, temp_config):
        """Test filtering non-existent repository."""
        app = GitHubSummaryApp(temp_config)
        with pytest.raises(ValueError, match="Repository 'nonexistent/repo' not found"):
            app._filter_repositories("nonexistent/repo")

    @pytest.mark.asyncio
    async def test_run_with_skip_summary(self, minimal_config):
        """Test running with summary skipped."""
        with patch("github_summary.app.GitHubService") as mock_gh_service:
            # Mock GitHub service
            mock_instance = AsyncMock()
            mock_gh_service.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            # Mock methods
            mock_instance.get_commits.return_value = []
            mock_instance.get_pull_requests.return_value = []
            mock_instance.get_issues.return_value = []
            mock_instance.get_discussions.return_value = []
            mock_instance.rate_limit = None

            app = GitHubSummaryApp(minimal_config, skip_summary=True)

            # Should not raise exceptions
            await app.run()

    @pytest.mark.asyncio
    async def test_run_specific_repositories(self, temp_config):
        """Test running with specific repositories."""
        with patch("github_summary.app.GitHubService") as mock_gh_service:
            # Mock GitHub service
            mock_instance = AsyncMock()
            mock_gh_service.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            # Mock methods
            mock_instance.get_commits.return_value = []
            mock_instance.get_pull_requests.return_value = []
            mock_instance.get_issues.return_value = []
            mock_instance.get_discussions.return_value = []
            mock_instance.rate_limit = None

            app = GitHubSummaryApp(temp_config, skip_summary=True)

            # Test with specific repo names
            await app.run(repo_names=["test/repo"])

    @pytest.mark.asyncio
    async def test_run_with_invalid_repo(self, temp_config):
        """Test running with invalid repository name."""
        app = GitHubSummaryApp(temp_config, skip_summary=True)

        with pytest.raises((SystemExit, typer.Exit)):  # typer.Exit
            await app.run(repo_names=["invalid/repo"])


class TestWebApp:
    """Test cases for the web application."""

    def test_create_web_app(self, minimal_config):
        """Test creating FastAPI web app."""
        web_app = create_web_app(minimal_config)

        assert web_app is not None
        assert hasattr(web_app, "routes")
        assert web_app.state.config_path == minimal_config

    def test_web_app_default_config(self):
        """Test creating web app with default config path."""
        # Should not crash even if config doesn't exist
        # (will fail at runtime when trying to access config)
        web_app = create_web_app()
        assert web_app is not None


class TestIntegration:
    """Integration tests for the complete application."""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_mocks(self, temp_config):
        """Test complete pipeline with mocked services."""
        with (
            patch("github_summary.app.GitHubService") as mock_gh_service,
            patch("github_summary.app.AsyncLLMClient") as mock_llm_client,
            patch("github_summary.app.Summarizer") as mock_summarizer,
        ):
            # Mock GitHub service
            mock_gh_instance = AsyncMock()
            mock_gh_service.return_value = mock_gh_instance
            mock_gh_instance.__aenter__.return_value = mock_gh_instance
            mock_gh_instance.__aexit__.return_value = None

            # Mock data
            mock_gh_instance.get_commits.return_value = []
            mock_gh_instance.get_pull_requests.return_value = []
            mock_gh_instance.get_issues.return_value = []
            mock_gh_instance.get_discussions.return_value = []
            mock_gh_instance.rate_limit = MagicMock(remaining=5000, limit=5000)

            # Mock LLM and summarizer
            mock_llm_instance = MagicMock()
            mock_llm_client.return_value = mock_llm_instance

            mock_summarizer_instance = AsyncMock()
            mock_summarizer.return_value = mock_summarizer_instance
            mock_summarizer_instance.summarize.return_value = "Test summary"

            # Run the app
            app = GitHubSummaryApp(temp_config, skip_summary=False)
            await app.run(repo_names=["test/repo"], save_json=False, save_markdown=False, max_concurrent_repos=1)

            # Verify calls were made
            mock_gh_service.assert_called_once()
            mock_summarizer_instance.summarize.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self, temp_config):
        """Test error handling in the pipeline."""
        with patch("github_summary.app.GitHubService") as mock_gh_service:
            # Mock GitHub service to raise an error
            mock_gh_service.side_effect = Exception("GitHub API error")

            app = GitHubSummaryApp(temp_config, skip_summary=True)

            # Should raise typer.Exit due to service creation error
            with pytest.raises((SystemExit, typer.Exit)):
                await app.run()


if __name__ == "__main__":
    pytest.main([__file__])
