import json
from datetime import datetime, UTC
from pathlib import Path
import logging

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


def get_last_run_time(config_path: str) -> datetime | None:
    """Gets the last run time for a specific config file."""
    data = _read_last_run_times()
    if config_path in data:
        try:
            return datetime.fromisoformat(data[config_path]).astimezone(UTC)
        except ValueError:
            logger.warning("Invalid datetime format for %s in last_run_times.json", config_path)
            return None
    return None


def set_last_run_time(config_path: str) -> None:
    """Sets the last run time for a specific config file to the current UTC time."""
    data = _read_last_run_times()
    data[config_path] = datetime.now(UTC).isoformat()
    _write_last_run_times(data)
