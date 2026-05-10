import asyncio
import json
import logging
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from github_summary.paths import get_default_cache_dir

logger = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = get_default_cache_dir()
LAST_RUN_TIMES_FILE = DEFAULT_CACHE_DIR / "last_run_times.json"

# Async lock for write operations
_async_lock = asyncio.Lock()


def _last_run_times_file(cache_dir: str | os.PathLike[str] | None = None) -> Path:
    """Return the last-run state file for a cache directory."""
    if cache_dir is None:
        return LAST_RUN_TIMES_FILE
    return Path(cache_dir) / "last_run_times.json"


async def _read_last_run_times(cache_dir: str | os.PathLike[str] | None = None) -> dict[str, str]:
    """Async read of last run times from the JSON file."""
    last_run_file = _last_run_times_file(cache_dir)
    if last_run_file.exists():
        try:

            def _read_file():
                with open(last_run_file) as f:
                    return json.load(f)

            return _read_file()
        except json.JSONDecodeError:
            logger.warning("Could not decode last_run_times.json. Starting with empty data.")
            return {}
    return {}


async def _write_last_run_times(data: dict[str, str], cache_dir: str | os.PathLike[str] | None = None) -> None:
    """Async write of last run times to the JSON file."""
    last_run_file = _last_run_times_file(cache_dir)
    last_run_file.parent.mkdir(parents=True, exist_ok=True)

    def _write_file(data_to_write):
        with tempfile.NamedTemporaryFile("w", dir=last_run_file.parent, delete=False) as f:
            json.dump(data_to_write, f, indent=2)
            temp_file = Path(f.name)
        os.replace(temp_file, last_run_file)

    _write_file(data)


def _get_run_key(config_path: str | os.PathLike[str], repo_name: str | None = None) -> str:
    """Generate a unique key for tracking last run times."""
    if repo_name:
        return f"{config_path}::{repo_name}"
    return str(config_path)


async def get_last_run_time(
    config_path: str | os.PathLike[str],
    repo_name: str | None = None,
    cache_dir: str | os.PathLike[str] | None = None,
) -> datetime | None:
    """Async get of last run time for a specific config file or repository.

    Args:
        config_path: Path to the configuration file.
        repo_name: Optional repository name. If provided, gets per-repo last run time.
    """
    data = await _read_last_run_times(cache_dir)
    run_key = _get_run_key(config_path, repo_name)
    if run_key in data:
        try:
            return datetime.fromisoformat(data[run_key]).astimezone(UTC)
        except ValueError:
            logger.warning("Invalid datetime format for %s in last_run_times.json", run_key)
            return None
    return None


async def set_multiple_last_run_times(
    updates: dict[str, datetime],
    cache_dir: str | os.PathLike[str] | None = None,
) -> None:
    """Async set of multiple last run times atomically.

    Args:
        updates: Dictionary mapping run keys to datetime objects.
    """
    async with _async_lock:
        data = await _read_last_run_times(cache_dir)
        for run_key, timestamp in updates.items():
            data[run_key] = timestamp.isoformat()
        await _write_last_run_times(data, cache_dir)
