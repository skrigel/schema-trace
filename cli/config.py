from pathlib import Path
import json
from typing import Optional
from pydantic import BaseModel
import os


class CLIConfig(BaseModel):
    """
    CLI configuration schema.

    Stored in ~/.schematrace/config.json

    Attributes:
        api_url: Base URL for SchemaTrace API
        api_key: API key for authentication (optional)
        default_project: Default project name to use when not specified
    """
    api_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    default_project: Optional[str] = None


CONFIG_DIR = Path.home() / ".schematrace"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> CLIConfig:
    """
    Load configuration with priority:
    1. Environment variables (highest priority)
    2. Config file (~/.schematrace/config.json)
    3. Defaults (lowest priority)

    Returns:
        CLIConfig instance with merged configuration
    """
    # Start with empty dict
    config_data = {}

    # Load from file if it exists
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
        except json.JSONDecodeError:
            # Ignore malformed config file, use defaults
            pass

    # Create config with file data (or defaults)
    config = CLIConfig(**config_data)

    # Environment variable overrides
    if api_url := os.getenv("SCHEMATRACE_API_URL"):
        config.api_url = api_url

    if api_key := os.getenv("SCHEMATRACE_API_KEY"):
        config.api_key = api_key

    if default_project := os.getenv("SCHEMATRACE_DEFAULT_PROJECT"):
        config.default_project = default_project

    return config


def save_config(config: CLIConfig) -> None:
    """
    Save configuration to file.

    Creates config directory if it doesn't exist.

    Args:
        config: Configuration to save
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_FILE, 'w') as f:
        json.dump(config.model_dump(), f, indent=2)


def get_api_key(config: CLIConfig) -> str:
    """
    Get API key with helpful error if not configured.

    Args:
        config: Configuration instance

    Returns:
        API key string

    Raises:
        ValueError: If API key is not configured
    """
    if config.api_key:
        return config.api_key

    raise ValueError(
        "API key not configured. Set it via:\n"
        "  1. Environment variable: export SCHEMATRACE_API_KEY=your-key\n"
        "  2. Config file: schematrace config --set-api-key your-key\n"
    )
