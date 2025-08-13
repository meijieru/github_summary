from unittest.mock import patch

import pytest

from github_summary.models import Config, GitHubConfig, RepoConfig, ScheduleConfig
from github_summary.scheduler import ReportScheduler


@pytest.mark.unit
def test_repo_config_with_cron_schedule():
    """Test that RepoConfig can have a cron-based schedule."""
    schedule_config = ScheduleConfig(cron="0 9 * * 1", timezone="UTC")
    repo_config = RepoConfig(name="owner/repo", schedule=schedule_config)

    assert repo_config.schedule is not None
    assert repo_config.schedule.cron == "0 9 * * 1"
    assert repo_config.schedule.timezone == "UTC"


@pytest.mark.unit
def test_repo_config_without_schedule():
    """Test that RepoConfig works without a schedule (default None)."""
    repo_config = RepoConfig(name="owner/repo")
    assert repo_config.schedule is None


@pytest.mark.unit
def test_schedule_config_defaults():
    """Test ScheduleConfig default values."""
    schedule_config = ScheduleConfig()
    assert schedule_config.cron == "0 6 * * *"  # Daily at 6 AM
    assert schedule_config.timezone is None


@pytest.mark.unit
@pytest.mark.parametrize(
    "cron_expr,description",
    [
        ("0 9 * * *", "Daily at 9 AM"),
        ("0 9,17 * * *", "Daily at 9 AM and 5 PM"),
        ("0 9 * * 1", "Every Monday at 9 AM"),
        ("0 9-17 * * 1-5", "Hourly during business hours"),
        ("*/15 * * * *", "Every 15 minutes"),
        ("0 0 1 * *", "First day of month"),
    ],
)
def test_schedule_config_accepts_valid_cron(cron_expr, description):
    """Test that ScheduleConfig accepts valid cron expressions."""
    schedule_config = ScheduleConfig(cron=cron_expr)
    assert schedule_config.cron == cron_expr


@pytest.mark.integration
@patch("github_summary.scheduler.load_config")
def test_scheduler_registers_global_schedule(mock_load_config):
    """Test that the scheduler registers global cron jobs correctly."""
    config = Config(
        github=GitHubConfig(token="test_token"),
        repositories=[RepoConfig(name="owner/repo1")],
        schedule=ScheduleConfig(cron="0 9 * * *"),
    )
    mock_load_config.return_value = config

    scheduler = ReportScheduler("test_config.toml")

    # Use BackgroundScheduler for testing
    from apscheduler.schedulers.background import BackgroundScheduler

    test_scheduler = BackgroundScheduler()
    scheduler._register_jobs(test_scheduler)

    jobs = test_scheduler.get_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == "global_schedule"


@pytest.mark.integration
@patch("github_summary.scheduler.load_config")
def test_scheduler_registers_repo_specific_schedule(mock_load_config):
    """Test that the scheduler registers per-repository schedules."""
    repo1 = RepoConfig(
        name="owner/repo1",
        schedule=ScheduleConfig(cron="0 10 * * *"),
    )

    config = Config(
        github=GitHubConfig(token="test_token"),
        repositories=[repo1],
    )
    mock_load_config.return_value = config

    scheduler = ReportScheduler("test_config.toml")

    from apscheduler.schedulers.background import BackgroundScheduler

    test_scheduler = BackgroundScheduler()
    scheduler._register_jobs(test_scheduler)

    jobs = test_scheduler.get_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == "repo_owner/repo1"


@pytest.mark.integration
@patch("github_summary.scheduler.load_config")
def test_scheduler_handles_no_schedules(mock_load_config):
    """Test scheduler behavior when no schedules are configured."""
    config = Config(
        github=GitHubConfig(token="test_token"),
        repositories=[RepoConfig(name="owner/repo1")],
    )
    mock_load_config.return_value = config

    scheduler = ReportScheduler("test_config.toml")

    from apscheduler.schedulers.background import BackgroundScheduler

    test_scheduler = BackgroundScheduler()
    scheduler._register_jobs(test_scheduler)

    jobs = test_scheduler.get_jobs()
    assert len(jobs) == 0


@pytest.mark.integration
@patch("github_summary.actions.run_report")
@patch("github_summary.scheduler.load_config")
def test_scheduler_with_timezone(mock_load_config, mock_run_report):
    """Test scheduler handles timezone configuration."""
    repo1 = RepoConfig(name="owner/repo1", schedule=ScheduleConfig(cron="0 9 * * 1", timezone="America/New_York"))

    config = Config(github=GitHubConfig(token="test_token"), repositories=[repo1])
    mock_load_config.return_value = config

    scheduler = ReportScheduler("test_config.toml")

    from apscheduler.schedulers.background import BackgroundScheduler

    test_scheduler = BackgroundScheduler()
    scheduler._register_jobs(test_scheduler)

    jobs = test_scheduler.get_jobs()
    assert len(jobs) == 1
    # APScheduler handles timezone validation internally
