import asyncio
import logging
import os
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from github_summary.actions import run_report
from github_summary.config import load_config

logger = logging.getLogger(__name__)


async def _run_report_job(config_path, save, save_markdown, skip_summary, repo_name):
    """Async job function for scheduler."""
    max_concurrent = int(os.environ.get("GHSUM_CONCURRENT_REPOS", "4"))
    logger.info("Running async report job with %d concurrent repos", max_concurrent)

    try:
        await run_report(config_path, save, save_markdown, skip_summary, repo_name, max_concurrent)
        logger.info("Scheduled report job completed successfully")
    except Exception as e:
        logger.error("Report job failed: %s", e)
        raise


class ReportScheduler:
    """Async scheduler for periodic GitHub reports using cron expressions."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.scheduler: Optional[AsyncIOScheduler] = None

    def _register_jobs(self, scheduler) -> None:
        """Register all cron jobs from configuration."""

        cfg = load_config(self.config_path)
        report_func = _run_report_job

        # Register global schedule if enabled
        if cfg.schedule:
            trigger = CronTrigger.from_crontab(cfg.schedule.cron, timezone=cfg.schedule.timezone)
            scheduler.add_job(
                func=report_func,
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
                    func=report_func,
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

    async def start(self) -> None:
        """Start the async scheduler."""
        logger.info("Starting scheduler (PID %d)", os.getpid())

        self.scheduler = AsyncIOScheduler()
        self._register_jobs(self.scheduler)

        if not self.scheduler.get_jobs():
            logger.warning("No schedules configured.")
            return

        self.scheduler.start()
        logger.info("Scheduler started with %d jobs", len(self.scheduler.get_jobs()))

    async def stop(self) -> None:
        """Stop the async scheduler."""
        if self.scheduler:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")

    async def run_forever(self) -> None:
        """Run scheduler forever for CLI usage."""
        logger.info("Starting async scheduler for CLI mode")

        await self.start()

        if not self.scheduler or not self.scheduler.get_jobs():
            logger.warning("No schedules configured. Exiting.")
            return

        logger.info("Scheduler running with %d jobs. Press Ctrl+C to stop.", len(self.scheduler.get_jobs()))
        try:
            # Keep the scheduler running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        finally:
            await self.stop()
