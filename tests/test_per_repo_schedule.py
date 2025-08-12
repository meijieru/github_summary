from unittest.mock import Mock, patch

import pytest

from github_summary.actions import run_report
from github_summary.models import Config, GitHubConfig, RepoConfig, ScheduleConfig
from github_summary.scheduler import ReportScheduler


def test_repo_config_with_schedule():
    """Test that RepoConfig can have an optional schedule."""
    schedule_config = ScheduleConfig(enabled=True, run_at=["08:00", "16:00"])
    repo_config = RepoConfig(name="owner/repo", schedule=schedule_config)

    assert repo_config.schedule is not None
    assert repo_config.schedule.enabled is True
    assert repo_config.schedule.run_at == ["08:00", "16:00"]


def test_repo_config_without_schedule():
    """Test that RepoConfig works without a schedule (default None)."""
    repo_config = RepoConfig(name="owner/repo")
    assert repo_config.schedule is None


@patch("github_summary.scheduler.load_config")
@patch("schedule.Scheduler.every")
def test_scheduler_registers_per_repo_schedules(mock_every, mock_load_config):
    """Test that the scheduler registers jobs for repositories with individual schedules."""
    # Create a mock config with per-repo schedules
    repo1 = RepoConfig(name="owner/repo1", schedule=ScheduleConfig(enabled=True, run_at=["09:00"]))
    repo2 = RepoConfig(name="owner/repo2", schedule=ScheduleConfig(enabled=True, run_at=["15:00"]))
    repo3 = RepoConfig(name="owner/repo3")  # No schedule

    config = Config(github=GitHubConfig(token="test_token"), repositories=[repo1, repo2, repo3])

    mock_load_config.return_value = config

    # Mock the schedule chain
    mock_day = Mock()
    mock_at = Mock()
    mock_do = Mock()

    mock_every.return_value.day = mock_day
    mock_day.at.return_value = mock_at
    mock_at.do = mock_do

    scheduler = ReportScheduler("test_config.toml")
    scheduler._register_jobs()

    # Should be called twice (once for each repo with a schedule)
    assert mock_every.call_count == 2
    assert mock_day.at.call_count == 2
    assert mock_do.call_count == 2

    # Verify the correct times and repo names are used
    mock_day.at.assert_any_call("09:00")
    mock_day.at.assert_any_call("15:00")


@patch("github_summary.scheduler.load_config")
@patch("schedule.Scheduler.every")
def test_scheduler_registers_both_global_and_per_repo_schedules(mock_every, mock_load_config):
    """Test that the scheduler registers both global and per-repo schedules."""
    repo1 = RepoConfig(name="owner/repo1", schedule=ScheduleConfig(enabled=True, run_at=["10:00"]))

    config = Config(
        github=GitHubConfig(token="test_token"),
        repositories=[repo1],
        schedule=ScheduleConfig(enabled=True, run_at=["06:00"]),
    )

    mock_load_config.return_value = config

    # Mock the schedule chain
    mock_day = Mock()
    mock_at = Mock()
    mock_do = Mock()

    mock_every.return_value.day = mock_day
    mock_day.at.return_value = mock_at
    mock_at.do = mock_do

    scheduler = ReportScheduler("test_config.toml")
    scheduler._register_jobs()

    # Should be called twice (once for global, once for per-repo)
    assert mock_every.call_count == 2
    assert mock_day.at.call_count == 2
    assert mock_do.call_count == 2

    # Verify the correct times are used
    mock_day.at.assert_any_call("06:00")  # Global schedule
    mock_day.at.assert_any_call("10:00")  # Per-repo schedule


@patch("github_summary.actions._get_services")
@patch("github_summary.actions._get_repo_data")
def test_run_report_with_specific_repo(mock_get_repo_data, mock_get_services):
    """Test that run_report works with a specific repository name."""
    # Setup mocks
    repo1 = RepoConfig(name="owner/repo1")
    repo2 = RepoConfig(name="owner/repo2")

    config = Config(github=GitHubConfig(token="test_token"), repositories=[repo1, repo2], since_last_run=False)

    mock_service = Mock()
    mock_summarizer = None
    mock_get_services.return_value = (config, mock_service, mock_summarizer)
    mock_get_repo_data.return_value = ([], [], [], [])  # Empty data

    # Run report for specific repo
    with patch("github_summary.actions.set_last_run_time"):
        run_report("test_config.toml", False, False, True, "owner/repo1")

    # Should only call _get_repo_data once for the specific repo
    assert mock_get_repo_data.call_count == 1

    # Verify it was called with the correct repo
    call_args = mock_get_repo_data.call_args[0]
    assert call_args[0].name == "owner/repo1"


@patch("github_summary.actions._get_services")
def test_run_report_with_nonexistent_repo(mock_get_services):
    """Test that run_report raises an error for non-existent repository."""
    repo1 = RepoConfig(name="owner/repo1")

    config = Config(github=GitHubConfig(token="test_token"), repositories=[repo1])

    mock_service = Mock()
    mock_summarizer = None
    mock_get_services.return_value = (config, mock_service, mock_summarizer)

    # Should raise typer.Exit for non-existent repo
    with pytest.raises(Exception):  # typer.Exit
        run_report("test_config.toml", False, False, True, "owner/nonexistent")
