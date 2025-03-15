"""Configuration module for codemcp.

This module provides access to user configuration stored in ~/.codemcprc in TOML format.
"""

from pathlib import Path
from typing import Any, Optional
import os

import tomli

__all__ = [
    "get_config_path",
    "load_config",
    "get_logger_verbosity",
    "get_auto_commit",
    "load_project_config",
]

# Default configuration values
DEFAULT_CONFIG = {
    "logger": {
        "verbosity": "INFO",  # Default logging level
    },
    "git": {
        "auto_commit": True,  # Default to auto-commit
    },
}


def get_config_path() -> Path:
    """Return the path to the user's config file."""
    return Path.home() / ".codemcprc"


def load_config() -> dict[str, Any]:
    """Load configuration from ~/.codemcprc file.

    Returns:
        Dict containing the merged configuration (defaults + user config).

    """
    config = DEFAULT_CONFIG.copy()
    config_path = get_config_path()

    if config_path.exists():
        try:
            with open(config_path, "rb") as f:
                user_config = tomli.load(f)

            # Merge user config with defaults
            _merge_configs(config, user_config)
        except Exception as e:
            print(f"Error loading config from {config_path}: {e}")

    return config


def _merge_configs(base: dict[str, Any], override: dict[str, Any]) -> None:
    """Recursively merge override dict into base dict.

    Args:
        base: The base configuration dictionary to merge into.
        override: The override configuration dictionary to merge from.

    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _merge_configs(base[key], value)
        else:
            base[key] = value


def get_logger_verbosity() -> str:
    """Get the configured logger verbosity level.

    Returns:
        String representing the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    """
    config = load_config()
    return config["logger"]["verbosity"]


def load_project_config(project_path: str) -> dict[str, Any]:
    """Load project-specific configuration from codemcp.toml in the project directory.

    Args:
        project_path: The path to the project directory.

    Returns:
        Dict containing the project configuration.
    """
    config = {}
    config_path = os.path.join(project_path, "codemcp.toml")

    if os.path.exists(config_path):
        try:
            with open(config_path, "rb") as f:
                config = tomli.load(f)
        except Exception as e:
            print(f"Error loading project config from {config_path}: {e}")

    return config


def get_auto_commit(project_path: Optional[str] = None) -> bool:
    """Get the auto_commit setting for git operations.

    The function follows this precedence order:
    1. CODEMCP_AUTO_COMMIT environment variable (if set)
    2. Project-specific codemcp.toml (if project_path is provided)
    3. User's ~/.codemcprc
    4. Default (True)

    Args:
        project_path: Optional path to the project directory.

    Returns:
        Boolean indicating whether changes should be auto-committed.
    """
    # Check environment variable first
    env_auto_commit = os.environ.get("CODEMCP_AUTO_COMMIT")
    if env_auto_commit is not None:
        return env_auto_commit.lower() in ("true", "1", "yes", "y")

    # Check project config if provided
    if project_path:
        project_config = load_project_config(project_path)
        if "git" in project_config and "auto_commit" in project_config["git"]:
            return bool(project_config["git"]["auto_commit"])

    # Fallback to user config
    user_config = load_config()
    return user_config["git"].get("auto_commit", True)
