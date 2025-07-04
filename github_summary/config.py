import toml
from dotenv import load_dotenv
from github_summary.models import Config
from pydantic import ValidationError

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
        with open(path) as f:
            data = toml.load(f)
        return Config(**data)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at: {path}")
    except ValidationError as e:
        raise ValueError(f"Invalid configuration: {e}")
