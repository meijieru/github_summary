import threading
import time
from typing import Optional

import schedule

from github_summary.actions import run_report
from github_summary.config import load_config


class ReportScheduler:
    """Isolated scheduler for periodic GitHub reports."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self._scheduler = schedule.Scheduler()
        self._stop_evt: threading.Event = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._jobs_registered: bool = False

    def _register_jobs(self) -> None:
        cfg = load_config(self.config_path)
        self._scheduler.clear()
        self._jobs_registered = False
        if cfg.schedule and cfg.schedule.enabled:
            for run_time in cfg.schedule.run_at:
                # Do not save artifacts; do not skip summary
                self._scheduler.every().day.at(run_time).do(run_report, self.config_path, False, False, False)
                self._jobs_registered = True

    def _loop(self) -> None:
        while not self._stop_evt.is_set():
            self._scheduler.run_pending()
            # Wake at most once per minute to keep CPU usage low
            self._stop_evt.wait(60)

    def start(self) -> None:
        """Start the background scheduling thread."""
        self._register_jobs()
        if not self._jobs_registered:
            return
        self._worker = threading.Thread(target=self._loop, daemon=True)
        self._worker.start()

    def stop(self, timeout: float = 10.0) -> None:
        """Stop the background scheduling thread."""
        self._stop_evt.set()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=timeout)

    def run_forever(self) -> None:
        """Blocking run for CLI usage."""
        self._register_jobs()
        while True:
            self._scheduler.run_pending()
            time.sleep(60)
