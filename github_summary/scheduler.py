import asyncio
import contextlib
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from github_summary.app import GitHubSummaryApp
from github_summary.config import get_max_concurrent_repos, load_config, load_config_uncached
from github_summary.models import Config

logger = logging.getLogger(__name__)


async def _run_scheduled_job(
    config_path: str,
    repo_names: list[str] | None = None,
    output_dir: str | None = None,
    cache_dir: str | None = None,
    log_dir: str | None = None,
) -> None:
    """Async job function for scheduler."""

    max_concurrent = get_max_concurrent_repos(config_path)

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
        app = GitHubSummaryApp(
            config_path,
            skip_summary=False,
            output_dir=output_dir,
            cache_dir=cache_dir,
            log_dir=log_dir,
        )
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

    def __init__(
        self,
        config_path: str,
        output_dir: str | None = None,
        cache_dir: str | None = None,
        log_dir: str | None = None,
        reload_interval: float = 1.0,
    ):
        self.config_path = config_path
        self.output_dir = output_dir
        self.cache_dir = cache_dir
        self.log_dir = log_dir
        self.reload_interval = reload_interval
        self.scheduler: AsyncIOScheduler | None = None
        self._watch_task: asyncio.Task[None] | None = None
        self._last_seen_signature: tuple[int, int] | None = None

    def _register_jobs(self, scheduler, cfg: Config | None = None, *, replace_existing: bool = False) -> None:
        """Register all cron jobs from configuration."""

        cfg = cfg or load_config(self.config_path)
        report_func = _run_scheduled_job
        jobs: list[dict[str, Any]] = []

        # Register global schedule if enabled
        if cfg.schedule:
            trigger = CronTrigger.from_crontab(cfg.schedule.cron, timezone=cfg.schedule.timezone)
            jobs.append(
                {
                    "func": report_func,
                    "args": (self.config_path, None, self.output_dir, self.cache_dir, self.log_dir),
                    "trigger": trigger,
                    "id": "global_schedule",
                    "name": "Global repository summary",
                }
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
                job_args = (self.config_path, [repo_names[0]], self.output_dir, self.cache_dir, self.log_dir)
            else:
                # Multiple repositories with same schedule
                job_id = f"grouped_repos_{'_'.join(repo_names[:3])}"  # Limit ID length
                if len(repo_names) > 3:
                    job_id += f"_and_{len(repo_names) - 3}_more"
                job_name = f"Summary for {len(repo_names)} repositories"
                job_args = (self.config_path, repo_names, self.output_dir, self.cache_dir, self.log_dir)

            jobs.append({"func": report_func, "args": job_args, "trigger": trigger, "id": job_id, "name": job_name})

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

        job_ids = [job["id"] for job in jobs]
        if len(job_ids) != len(set(job_ids)):
            raise ValueError("Configuration produces duplicate scheduler job IDs")

        if replace_existing:
            scheduler.remove_all_jobs()
        for job in jobs:
            scheduler.add_job(**job)

    def _config_signature(self) -> tuple[int, int] | None:
        """Return a signature that changes when the config file is replaced or edited."""
        try:
            stat = Path(self.config_path).stat()
        except OSError:
            return None
        return stat.st_mtime_ns, stat.st_size

    async def _reload_if_changed(self) -> bool:
        """Reload scheduled jobs when a new valid configuration is observed."""
        signature = await asyncio.to_thread(self._config_signature)
        if signature == self._last_seen_signature:
            return False
        self._last_seen_signature = signature

        try:
            cfg = await asyncio.to_thread(load_config_uncached, self.config_path)
            if self.scheduler is None:
                return False
            self._register_jobs(self.scheduler, cfg, replace_existing=True)
        except Exception as exc:  # noqa: BLE001  # Keep the watcher alive for third-party scheduler errors.
            logger.error("Configuration reload failed; keeping existing schedules: %s", exc)
            return False

        load_config.cache_clear()
        logger.info("Configuration reloaded successfully; scheduler now has %d jobs", len(self.scheduler.get_jobs()))
        return True

    async def _watch_config(self) -> None:
        """Watch the configuration file for changes until the scheduler stops."""
        while True:
            await asyncio.sleep(self.reload_interval)
            await self._reload_if_changed()

    async def start(self) -> None:
        """Start the async scheduler."""
        logger.info("Starting scheduler (PID %d)", os.getpid())

        self.scheduler = AsyncIOScheduler()
        self._register_jobs(self.scheduler)
        self.scheduler.start()
        self._last_seen_signature = await asyncio.to_thread(self._config_signature)
        self._watch_task = asyncio.create_task(self._watch_config(), name="config-reload-watcher")

        if not self.scheduler.get_jobs():
            logger.warning("No schedules configured; watching for configuration changes.")
        logger.info("Scheduler started with %d jobs", len(self.scheduler.get_jobs()))

    async def stop(self) -> None:
        """Stop the async scheduler."""
        if self._watch_task:
            self._watch_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._watch_task
            self._watch_task = None
        if self.scheduler:
            cast(Any, self.scheduler).shutdown(wait=True)
            logger.info("Scheduler stopped")

    async def run_forever(self) -> None:
        """Run scheduler forever for CLI usage."""
        logger.info("Starting async scheduler for CLI mode")

        await self.start()

        if self.scheduler is None:
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
