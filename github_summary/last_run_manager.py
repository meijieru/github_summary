import asyncio
import functools
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

LAST_RUN_TIMES_FILE = Path("log/last_run_times.json")

# Async lock for write operations
_async_lock = asyncio.Lock()


async def _read_last_run_times() -> dict[str, str]:
    """Async read of last run times from the JSON file."""
    if LAST_RUN_TIMES_FILE.exists():
        try:

            def _read_file():
                with open(LAST_RUN_TIMES_FILE) as f:
                    return json.load(f)

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, functools.partial(_read_file))
        except json.JSONDecodeError:
            logger.warning("Could not decode last_run_times.json. Starting with empty data.")
            return {}
    return {}


async def _write_last_run_times(data: dict[str, str]) -> None:
    """Async write of last run times to the JSON file."""
    LAST_RUN_TIMES_FILE.parent.mkdir(exist_ok=True)

    def _write_file(data_to_write):
        with open(LAST_RUN_TIMES_FILE, "w") as f:
            json.dump(data_to_write, f, indent=2)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _write_file, data)


def _get_run_key(config_path: str, repo_name: str | None = None) -> str:
    """Generate a unique key for tracking last run times."""
    if repo_name:
        return f"{config_path}::{repo_name}"
    return config_path


async def get_last_run_time(config_path: str, repo_name: str | None = None) -> datetime | None:
    """Async get of last run time for a specific config file or repository.

    Args:
        config_path: Path to the configuration file.
        repo_name: Optional repository name. If provided, gets per-repo last run time.
    """
    data = await _read_last_run_times()
    run_key = _get_run_key(config_path, repo_name)
    if run_key in data:
        try:
            return datetime.fromisoformat(data[run_key]).astimezone(UTC)
        except ValueError:
            logger.warning("Invalid datetime format for %s in last_run_times.json", run_key)
            return None
    return None


async def set_multiple_last_run_times(updates: Dict[str, datetime]) -> None:
    """Async set of multiple last run times atomically.

    Args:
        updates: Dictionary mapping run keys to datetime objects.
    """
    async with _async_lock:
        data = await _read_last_run_times()
        for run_key, timestamp in updates.items():
            data[run_key] = timestamp.isoformat()
        await _write_last_run_times(data)
