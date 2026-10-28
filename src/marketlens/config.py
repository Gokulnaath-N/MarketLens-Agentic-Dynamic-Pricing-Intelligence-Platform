"""Configuration loader module for MarketLens AI.

Resolves project directories reliably and safely loads YAML configuration files
with environment variable overrides and rigorous error handling.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

import yaml

try:
    from dotenv import load_dotenv

    # Load environment variables from .env if present
    load_dotenv()
except ImportError:
    pass


class ConfigurationError(Exception):
    """Raised when a configuration file cannot be found, read, or parsed."""

    pass


def get_project_root() -> Path:
    """Return the absolute Path to the project root directory.

    Resolves relative to this file's location: src/marketlens/config.py -> root.
    """
    return Path(__file__).resolve().parent.parent.parent


def get_configs_dir() -> Path:
    """Return the Path to the standard configs directory."""
    return get_project_root() / "configs"


def load_yaml_config(
    filename: str | Path,
    configs_dir: str | Path | None = None,
    allow_empty: bool = True,
) -> dict[str, Any]:
    """Load and parse a YAML configuration file from configs/ or custom directory.

    Args:
        filename: Name of the YAML file (e.g. 'app.yaml') or relative/absolute path.
        configs_dir: Optional directory override. Defaults to project `configs/`.
        allow_empty: If True, empty files return an empty dict `{}`.
                     If False, raises ConfigurationError for empty files.

    Returns:
        A dictionary representing the parsed YAML configuration.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ConfigurationError: If the YAML content is malformed or invalid.
    """
    file_path = Path(filename)
    if not file_path.is_absolute():
        if file_path.exists():
            file_path = file_path.resolve()
        elif (get_project_root() / file_path).exists():
            file_path = (get_project_root() / file_path).resolve()
        else:
            base_dir = Path(configs_dir) if configs_dir is not None else get_configs_dir()
            file_path = (base_dir / file_path).resolve()

    if not file_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: '{file_path}'. "
            f"Expected file in '{configs_dir or get_configs_dir()}'."
        )

    if not file_path.is_file():
        raise ConfigurationError(f"Configuration path is not a file: '{file_path}'")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ConfigurationError(
            f"Failed to parse YAML file '{file_path.name}': {exc}"
        ) from exc
    except Exception as exc:
        raise ConfigurationError(
            f"Unexpected error reading configuration file '{file_path.name}': {exc}"
        ) from exc

    if content is None:
        if allow_empty:
            return {}
        raise ConfigurationError(f"Configuration file '{file_path.name}' is empty.")

    if not isinstance(content, dict):
        raise ConfigurationError(
            f"Expected top-level dictionary in '{file_path.name}', got {type(content).__name__}."
        )

    return content


def get_env_var(name: str, default: str | None = None, required: bool = False) -> str | None:
    """Safely retrieve an environment variable.

    Args:
        name: Name of the environment variable.
        default: Default value if not set.
        required: If True, raises ConfigurationError when missing and no default.

    Returns:
        The environment variable value or default.

    Raises:
        ConfigurationError: When a required environment variable is not set.
    """
    value = os.getenv(name, default)
    if required and (value is None or value.strip() == ""):
        raise ConfigurationError(
            f"Required environment variable '{name}' is not set or empty."
        )
    return value
