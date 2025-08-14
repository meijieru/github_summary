import asyncio
import logging
import os
from collections import defaultdict
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from github_summary.config import load_config

logger = logging.getLogger(__name__)


async def _run_scheduled_job(config_path: str, repo_names: list[str] | None = None):
    """Async job function for scheduler."""
    from github_summary.app import GitHubSummaryApp

    max_concurrent = int(os.environ.get("GHSUM_CONCURRENT_REPOS", "4"))

    if repo_names is None:
        # Global job (all repositories)
        logger.info("Running scheduled job for all repositories with %d max concurrent", max_concurrent)
    elif len(repo_names) == 1:
        # Single repository
        logger.info("Running scheduled job for repository: %s", repo_names[0])
    else:
        # Multiple repositories (grouped)
        logger.info("Running scheduled job for %d repositories: %s", len(repo_names), ", ".join(repo_names))

    try:
        app = GitHubSummaryApp(config_path, skip_summary=False)
        await app.run(
            repo_names=repo_names,
            save_json=False,  # Scheduler jobs don't save JSON by default
            save_markdown=False,  # Scheduler jobs don't save markdown by default
            max_concurrent_repos=max_concurrent,
        )
        logger.info("Scheduled job completed successfully")
    except Exception as e:
        logger.error("Scheduled job failed: %s", e)
        raise


class ReportScheduler:
    """Async scheduler for periodic GitHub reports using cron expressions."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.scheduler: Optional[AsyncIOScheduler] = None

    def _register_jobs(self, scheduler) -> None:
        """Register all cron jobs from configuration."""

        cfg = load_config(self.config_path)
        report_func = _run_scheduled_job

        # Register global schedule if enabled
        if cfg.schedule:
            trigger = CronTrigger.from_crontab(cfg.schedule.cron, timezone=cfg.schedule.timezone)
            scheduler.add_job(
                func=report_func,
                args=(self.config_path, None),  # None means all repositories
                trigger=trigger,
                id="global_schedule",
                name="Global repository summary",
            )
            logger.info("Registered global schedule: %s (timezone: %s)", cfg.schedule.cron, cfg.schedule.timezone)

        # Group repositories by schedule (cron + timezone)
        schedule_groups = defaultdict(list)
        for repo in cfg.repositories:
            if repo.schedule:
                schedule_key = (repo.schedule.cron, repo.schedule.timezone)
                schedule_groups[schedule_key].append(repo.name)

        # Register grouped schedules
        for (cron_expr, timezone), repo_names in schedule_groups.items():
            trigger = CronTrigger.from_crontab(cron_expr, timezone=timezone)

            if len(repo_names) == 1:
                # Single repository
                job_id = f"repo_{repo_names[0]}"
                job_name = f"Summary for {repo_names[0]}"
                job_args = (self.config_path, [repo_names[0]])
            else:
                # Multiple repositories with same schedule
                job_id = f"grouped_repos_{'_'.join(repo_names[:3])}"  # Limit ID length
                if len(repo_names) > 3:
                    job_id += f"_and_{len(repo_names) - 3}_more"
                job_name = f"Summary for {len(repo_names)} repositories"
                job_args = (self.config_path, repo_names)

            scheduler.add_job(
                func=report_func,
                args=job_args,
                trigger=trigger,
                id=job_id,
                name=job_name,
            )

            if len(repo_names) == 1:
                logger.info(
                    "Registered schedule for %s: %s (timezone: %s)",
                    repo_names[0],
                    cron_expr,
                    timezone,
                )
            else:
                logger.info(
                    "Registered grouped schedule for %d repositories [%s]: %s (timezone: %s)",
                    len(repo_names),
                    ", ".join(repo_names),
                    cron_expr,
                    timezone,
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
