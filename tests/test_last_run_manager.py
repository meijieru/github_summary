from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from github_summary.last_run_manager import (
    get_last_run_time,
    set_multiple_last_run_times,
)


class TestLastRunManager:
    """Test cases for last run time management."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_multiple_last_run_times(self):
        """Test async batch last run time updates."""
        updates = {
            "config.toml::repo1": datetime.now(UTC),
            "config.toml::repo2": datetime.now(UTC),
        }

        with (
            patch("github_summary.last_run_manager._read_last_run_times") as mock_read,
            patch("github_summary.last_run_manager._write_last_run_times") as mock_write,
        ):
            mock_read.return_value = {}

            from github_summary.last_run_manager import set_multiple_last_run_times

            await set_multiple_last_run_times(updates)

            mock_write.assert_called_once()
            written_data = mock_write.call_args[0][0]
            assert len(written_data) == 2

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_per_repository_last_run_times(self):
        """Test per-repository last run time tracking."""
        config_path = "test_config.toml"
        repo_name = "test/repo"

        with (
            patch("github_summary.last_run_manager._read_last_run_times") as mock_read,
            patch("github_summary.last_run_manager._write_last_run_times") as mock_write,
        ):
            # Test setting
            mock_read.return_value = {}
            await set_multiple_last_run_times({f"{config_path}::{repo_name}": datetime.now(UTC)})

            mock_write.assert_called_once()
            written_data = mock_write.call_args[0][0]
            assert f"{config_path}::{repo_name}" in written_data

            # Test getting
            mock_read.return_value = {f"{config_path}::{repo_name}": datetime.now(UTC).isoformat()}

            result = await get_last_run_time(config_path, repo_name)
            assert result is not None
