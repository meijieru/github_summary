import toml
import logging
from dotenv import load_dotenv
from github_summary.models import Config
from pydantic import ValidationError

logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env file


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
