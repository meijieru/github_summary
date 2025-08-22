import functools
import logging
import os

import toml
from dotenv import load_dotenv
from pydantic import ValidationError

from github_summary.models import Config

logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env file


@functools.lru_cache(maxsize=8)
def load_config(path: str = "config/config.toml") -> Config:
    """Loads the configuration from a TOML file and validates it against the Config model.

    Args:
        path: The path to the configuration TOML file.

    Returns:
        A Config object containing the loaded configuration.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If the configuration is invalid according to the Config model.
    """
    try:
        logger.info("Loading configuration from %s", path)
        with open(path) as f:
            data = toml.load(f)
        logger.info("Configuration loaded successfully.")
        return Config(**data)
    except FileNotFoundError:
        logger.error("Configuration file not found at: %s", path)
        raise FileNotFoundError(f"Configuration file not found at: {path}")
    except ValidationError as e:
        logger.error("Invalid configuration: %s", e)
        raise ValueError(f"Invalid configuration: {e}")


def get_max_concurrent_repos(config_path: str, override: int | None = None) -> int:
    """Get max concurrent repos from config with environment variable override.

    Args:
        config_path: Path to the configuration file.
        override: Optional override value that takes precedence.

    Returns:
        The maximum number of concurrent repositories to process.
    """
    if override is not None:
        return override

    config = load_config(config_path)
    max_concurrent = config.performance.max_concurrent_repos

    # Allow environment variable override
    env_concurrent = os.environ.get("GHSUM_CONCURRENT_REPOS")
    if env_concurrent:
        try:
            max_concurrent = int(env_concurrent)
            logger.info("Using GHSUM_CONCURRENT_REPOS environment variable: %d", max_concurrent)
        except ValueError:
            logger.warning("Invalid GHSUM_CONCURRENT_REPOS value: %s, using config value", env_concurrent)

    return max_concurrent
