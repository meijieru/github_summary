import json
import logging
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

LAST_RUN_TIMES_FILE = Path("log/last_run_times.json")


def _read_last_run_times() -> dict[str, str]:
    """Reads the last run times from the JSON file."""
    if LAST_RUN_TIMES_FILE.exists():
        try:
            with open(LAST_RUN_TIMES_FILE) as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Could not decode last_run_times.json. Starting with empty data.")
            return {}
    return {}


def _write_last_run_times(data: dict[str, str]) -> None:
    """Writes the last run times to the JSON file."""
    LAST_RUN_TIMES_FILE.parent.mkdir(exist_ok=True)
    with open(LAST_RUN_TIMES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _get_run_key(config_path: str, repo_name: str | None = None) -> str:
    """Generate a unique key for tracking last run times."""
    if repo_name:
        return f"{config_path}::{repo_name}"
    return config_path


def get_last_run_time(config_path: str, repo_name: str | None = None) -> datetime | None:
    """Gets the last run time for a specific config file or repository.
    
    Args:
        config_path: Path to the configuration file.
        repo_name: Optional repository name. If provided, gets per-repo last run time.
    """
    data = _read_last_run_times()
    run_key = _get_run_key(config_path, repo_name)
    if run_key in data:
        try:
            return datetime.fromisoformat(data[run_key]).astimezone(UTC)
        except ValueError:
            logger.warning("Invalid datetime format for %s in last_run_times.json", run_key)
            return None
    return None


def set_last_run_time(config_path: str, repo_name: str | None = None) -> None:
    """Sets the last run time for a specific config file or repository to the current UTC time.
    
    Args:
        config_path: Path to the configuration file.
        repo_name: Optional repository name. If provided, sets per-repo last run time.
    """
    data = _read_last_run_times()
    run_key = _get_run_key(config_path, repo_name)
    data[run_key] = datetime.now(UTC).isoformat()
    _write_last_run_times(data)
