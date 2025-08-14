"""
Tests for the CLI interface.
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from github_summary.cli import app


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_config():
    """Create a temporary configuration file."""
    config_content = """
[github]
token = "test_token"

[[repositories]]
name = "test/repo"

output_dir = "test_output"
log_level = "ERROR"  # Reduce noise in tests
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(config_content)
        config_path = f.name

    yield config_path

    # Cleanup
    Path(config_path).unlink(missing_ok=True)


class TestCLICommands:
    """Test CLI command interface."""

    def test_cli_help(self, runner):
        """Test main CLI help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "GitHub Repository Summary Tool" in result.stdout
        assert "run" in result.stdout
        assert "serve" in result.stdout
        assert "schedule" in result.stdout
        assert "utils" in result.stdout

    def test_run_help(self, runner):
        """Test run command help."""
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "Generate repository summaries" in result.stdout
        assert "--repo" in result.stdout
        assert "--config" in result.stdout
        assert "--save-json" in result.stdout
        assert "--save-markdown" in result.stdout
        assert "--skip-summary" in result.stdout

    def test_serve_help(self, runner):
        """Test serve command help."""
        result = runner.invoke(app, ["serve", "--help"])
        assert result.exit_code == 0
        assert "Start RSS web server" in result.stdout
        assert "--host" in result.stdout
        assert "--port" in result.stdout
        assert "--reload" in result.stdout

    def test_schedule_help(self, runner):
        """Test schedule command help."""
        result = runner.invoke(app, ["schedule", "--help"])
        assert result.exit_code == 0
        assert "Run scheduler daemon" in result.stdout

    def test_utils_help(self, runner):
        """Test utils subcommand help."""
        result = runner.invoke(app, ["utils", "--help"])
        assert result.exit_code == 0
        assert "Utility commands" in result.stdout
        assert "validate-config" in result.stdout

    @patch("github_summary.cli.GitHubSummaryApp")
    def test_run_command_basic(self, mock_app_class, runner, temp_config):
        """Test basic run command."""
        # Mock the app
        mock_app = AsyncMock()
        mock_app_class.return_value = mock_app
        mock_app.run.return_value = None

        result = runner.invoke(app, ["run", "--config", temp_config, "--skip-summary"])

        assert result.exit_code == 0
        mock_app_class.assert_called_once_with(temp_config, skip_summary=True)
        mock_app.run.assert_called_once()

    @patch("github_summary.cli.GitHubSummaryApp")
    def test_run_command_with_repo(self, mock_app_class, runner, temp_config):
        """Test run command with specific repository."""
        mock_app = AsyncMock()
        mock_app_class.return_value = mock_app
        mock_app.run.return_value = None

        result = runner.invoke(
            app,
            [
                "run",
                "--config",
                temp_config,
                "--repo",
                "owner/repo",
                "--save-json",
                "--save-markdown",
                "--skip-summary",
            ],
        )

        assert result.exit_code == 0
        mock_app_class.assert_called_once_with(temp_config, skip_summary=True)
        mock_app.run.assert_called_once_with(
            repo_names=["owner/repo"], save_json=True, save_markdown=True, max_concurrent_repos=None
        )

    @patch("github_summary.cli.uvicorn")
    @patch("github_summary.cli.create_web_app")
    def test_serve_command(self, mock_create_app, mock_uvicorn, runner, temp_config):
        """Test serve command."""
        mock_web_app = object()  # Dummy app object
        mock_create_app.return_value = mock_web_app

        result = runner.invoke(app, ["serve", "--config", temp_config, "--host", "127.0.0.1", "--port", "9000"])

        assert result.exit_code == 0
        mock_create_app.assert_called_once_with(temp_config)
        mock_uvicorn.run.assert_called_once_with(mock_web_app, host="127.0.0.1", port=9000, reload=False)

    @patch("github_summary.cli.uvicorn")
    @patch.dict("os.environ", {}, clear=True)
    def test_serve_command_reload(self, mock_uvicorn, runner, temp_config):
        """Test serve command with reload."""
        import os

        result = runner.invoke(app, ["serve", "--config", temp_config, "--reload"])

        assert result.exit_code == 0
        # Check that config path was set in environment
        assert os.environ.get("GHSUM_CONFIG_PATH") == temp_config
        mock_uvicorn.run.assert_called_once_with(
            "github_summary.app:create_web_app", host="0.0.0.0", port=8000, reload=True, factory=True
        )

    @patch("github_summary.scheduler.ReportScheduler")
    def test_schedule_command(self, mock_scheduler_class, runner, temp_config):
        """Test schedule command."""
        mock_scheduler = AsyncMock()
        mock_scheduler_class.return_value = mock_scheduler
        mock_scheduler.run_forever.return_value = None

        result = runner.invoke(app, ["schedule", "--config", temp_config])

        assert result.exit_code == 0
        mock_scheduler_class.assert_called_once_with(temp_config)
        mock_scheduler.run_forever.assert_called_once()


class TestUtilsCommands:
    """Test utility commands."""

    def test_validate_config_valid(self, runner, temp_config):
        """Test config validation with valid config."""
        result = runner.invoke(app, ["utils", "validate-config", "--config", temp_config])

        assert result.exit_code == 0
        assert "Configuration file" in result.stdout
        assert "is valid" in result.stdout

    def test_validate_config_invalid(self, runner):
        """Test config validation with invalid config."""
        result = runner.invoke(app, ["utils", "validate-config", "--config", "nonexistent.toml"])

        assert result.exit_code == 1
        # The error message might be in stderr or not captured due to typer handling
        # Just check that it exits with error code 1


class TestCLIIntegration:
    """Integration tests for CLI."""

    def test_main_function_import(self):
        """Test that main function can be imported."""
        from github_summary.cli import main

        assert callable(main)

    def test_app_commands_exist(self):
        """Test that all expected commands exist."""
        # Test that the app has registered commands
        assert len(app.registered_commands) > 0
        # This is a basic smoke test - the CLI help tests above verify the commands exist

    def test_error_handling_invalid_config(self, runner):
        """Test error handling with invalid configuration."""
        result = runner.invoke(app, ["run", "--config", "nonexistent.toml"])

        # Should exit with error code
        assert result.exit_code != 0


if __name__ == "__main__":
    pytest.main([__file__])
