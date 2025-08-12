from unittest.mock import Mock, patch

import pytest

from github_summary.actions import run_report
from github_summary.models import Config, GitHubConfig, RepoConfig, ScheduleConfig
from github_summary.scheduler import ReportScheduler


def test_repo_config_with_cron_schedule():
    """Test that RepoConfig can have a cron-based schedule."""
    schedule_config = ScheduleConfig(cron="0 9 * * 1", timezone="UTC")
    repo_config = RepoConfig(name="owner/repo", schedule=schedule_config)

    assert repo_config.schedule is not None
    assert repo_config.schedule.cron == "0 9 * * 1"
    assert repo_config.schedule.timezone == "UTC"


def test_repo_config_without_schedule():
    """Test that RepoConfig works without a schedule (default None)."""
    repo_config = RepoConfig(name="owner/repo")
    assert repo_config.schedule is None


def test_schedule_config_defaults():
    """Test ScheduleConfig default values."""
    schedule_config = ScheduleConfig()
    assert schedule_config.cron == "0 6 * * *"  # Daily at 6 AM
    assert schedule_config.timezone is None


def test_schedule_config_validation_valid_cron():
    """Test that valid cron expressions pass validation."""
    valid_crons = [
        "0 9 * * *",  # Daily at 9 AM
        "0 9,17 * * *",  # Daily at 9 AM and 5 PM
        "0 9 * * 1",  # Every Monday at 9 AM
        "0 9-17 * * 1-5",  # Hourly during business hours
        "*/15 * * * *",  # Every 15 minutes
        "0 0 1 * *",  # First day of month
    ]

    for cron in valid_crons:
        schedule_config = ScheduleConfig(cron=cron)
        # Should not raise an exception
        assert schedule_config.cron == cron


def test_schedule_config_validation_invalid_cron():
    """Test that invalid cron expressions raise validation errors."""
    invalid_crons = [
        "0 9 * *",  # Too few fields
        "0 9 * * * *",  # Too many fields
        "60 9 * * *",  # Invalid minute (>59)
        "0 25 * * *",  # Invalid hour (>23)
        "0 9 32 * *",  # Invalid day (>31)
        "0 9 * 13 *",  # Invalid month (>12)
        "0 9 * * 8",  # Invalid weekday (>7)
    ]

    for cron in invalid_crons:
        with pytest.raises(ValueError):
            ScheduleConfig(cron=cron)


@patch("github_summary.scheduler.load_config")
def test_scheduler_registers_cron_jobs(mock_load_config):
    """Test that the scheduler registers cron jobs correctly."""
    repo1 = RepoConfig(
        name="owner/repo1",
        schedule=ScheduleConfig(cron="0 9 * * 1"),  # Monday at 9 AM
    )

    config = Config(github=GitHubConfig(token="test_token"), repositories=[repo1])
    mock_load_config.return_value = config

    scheduler = ReportScheduler("test_config.toml")
    scheduler._register_jobs()

    # Should have registered one job
    assert len(scheduler._jobs) == 1
    assert scheduler._jobs[0]["cron_expr"] == "0 9 * * 1"
    assert scheduler._jobs[0]["repo_name"] == "owner/repo1"


@patch("github_summary.scheduler.load_config")
def test_scheduler_registers_both_global_and_repo_schedules(mock_load_config):
    """Test that the scheduler registers both global and per-repo cron schedules."""
    repo1 = RepoConfig(
        name="owner/repo1",
        schedule=ScheduleConfig(cron="0 10 * * *"),  # Daily at 10 AM
    )

    config = Config(
        github=GitHubConfig(token="test_token"),
        repositories=[repo1],
        schedule=ScheduleConfig(cron="0 6 * * *"),  # Global daily at 6 AM
    )

    mock_load_config.return_value = config

    scheduler = ReportScheduler("test_config.toml")
    scheduler._register_jobs()

    # Should have registered both schedules
    assert len(scheduler._jobs) == 2

    # Check that both jobs are registered
    cron_exprs = [job["cron_expr"] for job in scheduler._jobs]
    assert "0 6 * * *" in cron_exprs  # Global schedule
    assert "0 10 * * *" in cron_exprs  # Per-repo schedule


@patch("github_summary.scheduler.load_config")
def test_scheduler_with_timezone(mock_load_config):
    """Test scheduler handles timezone configuration."""
    repo1 = RepoConfig(name="owner/repo1", schedule=ScheduleConfig(cron="0 9 * * 1", timezone="America/New_York"))

    config = Config(github=GitHubConfig(token="test_token"), repositories=[repo1])
    mock_load_config.return_value = config

    scheduler = ReportScheduler("test_config.toml")
    scheduler._register_jobs()

    # Should register the job with timezone info
    assert len(scheduler._jobs) == 1
    assert scheduler._jobs[0]["timezone"] is not None


@patch("github_summary.scheduler.load_config")
def test_scheduler_handles_invalid_timezone(mock_load_config):
    """Test scheduler handles invalid timezone gracefully."""
    repo1 = RepoConfig(name="owner/repo1", schedule=ScheduleConfig(cron="0 9 * * 1", timezone="Invalid/Timezone"))

    config = Config(github=GitHubConfig(token="test_token"), repositories=[repo1])
    mock_load_config.return_value = config

    scheduler = ReportScheduler("test_config.toml")
    scheduler._register_jobs()

    # Should still register the job but with None timezone (falls back to system timezone)
    assert len(scheduler._jobs) == 1
    assert scheduler._jobs[0]["timezone"] is None


@patch("github_summary.scheduler.run_report")
@patch("github_summary.scheduler.load_config")
def test_scheduler_executes_jobs(mock_load_config, mock_run_report):
    """Test that scheduler executes jobs when they're due."""
    from datetime import datetime, timedelta

    repo1 = RepoConfig(
        name="owner/repo1",
        schedule=ScheduleConfig(cron="* * * * *"),  # Every minute
    )

    config = Config(github=GitHubConfig(token="test_token"), repositories=[repo1])
    mock_load_config.return_value = config

    scheduler = ReportScheduler("test_config.toml")
    scheduler._register_jobs()

    # Manually set the next run time to the past to trigger execution
    scheduler._jobs[0]["next_run"] = datetime.now() - timedelta(seconds=30)

    # Run the check
    scheduler._check_and_run_jobs()

    # Should have called run_report
    mock_run_report.assert_called_once()


@patch("github_summary.actions._get_services")
@patch("github_summary.actions._get_repo_data")
def test_run_report_with_specific_repo(mock_get_repo_data, mock_get_services):
    """Test that run_report works with a specific repository name."""
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


def test_cron_field_validation_edge_cases():
    """Test edge cases in cron field validation."""
    # Test step values
    schedule = ScheduleConfig(cron="*/15 * * * *")  # Every 15 minutes
    assert schedule.cron == "*/15 * * * *"

    # Test ranges
    schedule = ScheduleConfig(cron="0 9-17 * * 1-5")  # Business hours
    assert schedule.cron == "0 9-17 * * 1-5"

    # Test lists
    schedule = ScheduleConfig(cron="0 9,12,17 * * 1,3,5")  # Multiple times and days
    assert schedule.cron == "0 9,12,17 * * 1,3,5"
