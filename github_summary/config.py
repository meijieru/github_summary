import functools
import logging
import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from github_summary.models import Config

logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env file


def _resolve_runtime_path(path: str, base_dir: Path | None = None) -> str:
    """Resolve a configured runtime path to an absolute path."""
    runtime_path = Path(path).expanduser()
    if not runtime_path.is_absolute():
        runtime_path = (base_dir or Path.cwd()) / runtime_path
    return str(runtime_path.resolve())


def resolve_runtime_paths(config: Config, base_dir: Path | None = None) -> Config:
    """Return a config copy with runtime directories resolved to absolute paths."""
    run_dir = _resolve_runtime_path(config.run_dir, base_dir)
    runtime_base = Path(run_dir)
    return config.model_copy(
        update={
            "run_dir": run_dir,
            "output_dir": _resolve_runtime_path(config.output_dir, runtime_base),
            "cache_dir": _resolve_runtime_path(config.cache_dir, runtime_base),
            "log_dir": _resolve_runtime_path(config.log_dir, runtime_base),
        }
    )


@functools.lru_cache(maxsize=8)
def load_config(path: str | Path = "config/config.toml") -> Config:
    """Loads the configuration from a TOML file and validates it against the Config model.

    Args:
        path: The path to the configuration TOML file.

    Returns:
        A Config object containing the loaded configuration.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If the configuration is invalid (malformed TOML or schema validation error).
    """
    config_path = Path(path)
    try:
        logger.info("Loading configuration from %s", config_path)
        with config_path.open("rb") as f:
            data = tomllib.load(f)
        logger.info("Configuration loaded successfully.")
        return resolve_runtime_paths(Config(**data), Path.cwd())
    except FileNotFoundError:
        logger.error("Configuration file not found at: %s", config_path)
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    except tomllib.TOMLDecodeError as e:
        logger.error("Failed to parse TOML file at %s: %s", config_path, e)
        raise ValueError(f"Invalid TOML configuration at {config_path}: {e}")
    except ValidationError as e:
        logger.error("Invalid configuration schema: %s", e)
        raise ValueError(f"Invalid configuration schema: {e}")


def get_max_concurrent_repos(config_path: str | Path, override: int | None = None) -> int:
    """Get max concurrent repos from config with environment variable override.

    Args:
        config_path: Path to the configuration file.
        override: Optional override value that takes precedence.

    Returns:
        The maximum number of concurrent repositories to process.
    """
    if override is not None:
        return override

    try:
        config = load_config(config_path)
        max_concurrent = config.performance.max_concurrent_repos
    except (FileNotFoundError, ValueError):
        # Fallback if config cannot be loaded, though ideally we should fail or log
        logger.warning("Could not load config for concurrency settings, defaulting to 4")
        max_concurrent = 4

    # Allow environment variable override
    env_concurrent = os.environ.get("GHSUM_CONCURRENT_REPOS")
    if env_concurrent:
        try:
            max_concurrent = int(env_concurrent)
            logger.info("Using GHSUM_CONCURRENT_REPOS environment variable: %d", max_concurrent)
        except ValueError:
            logger.warning("Invalid GHSUM_CONCURRENT_REPOS value: %s, using config value", env_concurrent)

    return max_concurrent
