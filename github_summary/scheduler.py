import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from github_summary.actions import run_report
from github_summary.config import load_config

logger = logging.getLogger(__name__)


class ReportScheduler:
    """Scheduler for periodic GitHub reports using cron expressions."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.scheduler: Optional[BackgroundScheduler] = None

    def _register_jobs(self, scheduler) -> None:
        """Register all cron jobs from configuration."""
        cfg = load_config(self.config_path)

        # Register global schedule if enabled
        if cfg.schedule:
            trigger = CronTrigger.from_crontab(cfg.schedule.cron, timezone=cfg.schedule.timezone)
            scheduler.add_job(
                func=run_report,
                args=(self.config_path, False, False, False, None),
                trigger=trigger,
                id="global_schedule",
                name="Global repository summary",
            )
            logger.info("Registered global schedule: %s (timezone: %s)", cfg.schedule.cron, cfg.schedule.timezone)

        # Register per-repository schedules
        for repo in cfg.repositories:
            if repo.schedule:
                trigger = CronTrigger.from_crontab(repo.schedule.cron, timezone=repo.schedule.timezone)
                scheduler.add_job(
                    func=run_report,
                    args=(self.config_path, False, False, False, repo.name),
                    trigger=trigger,
                    id=f"repo_{repo.name}",
                    name=f"Summary for {repo.name}",
                )
                logger.info(
                    "Registered schedule for %s: %s (timezone: %s)",
                    repo.name,
                    repo.schedule.cron,
                    repo.schedule.timezone,
                )

    def start(self) -> None:
        """Start the background scheduler."""
        self.scheduler = BackgroundScheduler()
        self._register_jobs(self.scheduler)

        if not self.scheduler.get_jobs():
            logger.warning("No schedules configured.")
            return

        self.scheduler.start()
        logger.info("Scheduler started with %d jobs", len(self.scheduler.get_jobs()))

    def stop(self) -> None:
        """Stop the background scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    def run_forever(self) -> None:
        """Blocking run for CLI usage."""
        scheduler = BlockingScheduler()
        self._register_jobs(scheduler)

        if not scheduler.get_jobs():
            logger.warning("No schedules configured. Exiting.")
            return

        logger.info("Starting scheduler with %d jobs", len(scheduler.get_jobs()))
        try:
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
