import os
from pathlib import Path

APP_STATE_DIR_NAME = "github-summary"


def get_default_run_dir() -> str:
    """Return the default application runtime directory under XDG_STATE_HOME."""
    state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")).expanduser()
    return str(state_home / APP_STATE_DIR_NAME)


def get_default_cache_dir() -> Path:
    """Return the default cache directory inside the application runtime directory."""
    return Path(get_default_run_dir()) / "cache"
