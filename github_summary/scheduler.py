import logging
import threading
import time
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from croniter import croniter

from github_summary.actions import run_report
from github_summary.config import load_config

logger = logging.getLogger(__name__)


class ReportScheduler:
    """Scheduler for periodic GitHub reports using cron expressions."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self._stop_evt: threading.Event = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._jobs: list = []

    def _register_jobs(self) -> None:
        """Register all cron jobs from configuration."""
        cfg = load_config(self.config_path)
        self._jobs.clear()

        # Register global schedule if enabled
        if cfg.schedule:
            self._add_cron_job(cfg.schedule.cron, cfg.schedule.timezone, None)

        # Register per-repository schedules
        for repo in cfg.repositories:
            if repo.schedule:
                self._add_cron_job(repo.schedule.cron, repo.schedule.timezone, repo.name)

    def _add_cron_job(self, cron_expr: str, timezone_str: str | None, repo_name: str | None) -> None:
        """Add a cron job to the job list."""
        try:
            # Parse timezone
            tz = None
            if timezone_str:
                try:
                    tz = ZoneInfo(timezone_str)
                except Exception as e:
                    logger.warning("Invalid timezone '%s': %s. Using system timezone.", timezone_str, e)

            # Create croniter instance to validate and calculate next run
            base_time = datetime.now(tz) if tz else datetime.now()
            cron_iter = croniter(cron_expr, base_time)

            job = {
                "cron_expr": cron_expr,
                "timezone": tz,
                "repo_name": repo_name,
                "croniter": cron_iter,
                "next_run": cron_iter.get_next(datetime),
            }

            self._jobs.append(job)

            timezone_info = f" (timezone: {timezone_str})" if timezone_str else ""
            logger.info("Registered cron job '%s'%s for %s", cron_expr, timezone_info, repo_name or "all repositories")

        except Exception as e:
            logger.error("Failed to register cron job '%s' for %s: %s", cron_expr, repo_name or "all repositories", e)

    def _check_and_run_jobs(self) -> None:
        """Check if any jobs should run and execute them."""
        current_time = datetime.now()

        for job in self._jobs:
            # Convert to appropriate timezone for comparison
            if job["timezone"]:
                current_time_tz = current_time.astimezone(job["timezone"])
                next_run = job["next_run"]
            else:
                current_time_tz = current_time
                next_run = job["next_run"]

            if current_time_tz >= next_run:
                try:
                    # Run the job
                    logger.info("Running scheduled job for %s", job["repo_name"] or "all repositories")
                    run_report(self.config_path, False, False, False, job["repo_name"])

                    # Calculate next run time
                    job["next_run"] = job["croniter"].get_next(datetime)
                    logger.debug(
                        "Next run scheduled for %s: %s", job["repo_name"] or "all repositories", job["next_run"]
                    )

                except Exception as e:
                    logger.error("Failed to run scheduled job for %s: %s", job["repo_name"] or "all repositories", e)

    def _loop(self) -> None:
        """Main scheduler loop."""
        while not self._stop_evt.is_set():
            self._check_and_run_jobs()
            # Check every 30 seconds for better timing accuracy
            self._stop_evt.wait(30)

    def start(self) -> None:
        """Start the background scheduling thread."""
        self._register_jobs()
        if not self._jobs:
            logger.warning("No schedules configured.")
            return

        self._worker = threading.Thread(target=self._loop, daemon=True)
        self._worker.start()
        logger.info("Scheduler started with %d jobs", len(self._jobs))

    def stop(self, timeout: float = 10.0) -> None:
        """Stop the background scheduling thread."""
        self._stop_evt.set()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=timeout)
        logger.info("Scheduler stopped")

    def run_forever(self) -> None:
        """Blocking run for CLI usage."""
        self._register_jobs()
        if not self._jobs:
            logger.warning("No schedules configured. Exiting.")
            return

        logger.info("Starting scheduler with %d jobs", len(self._jobs))
        while True:
            self._check_and_run_jobs()
            time.sleep(30)
