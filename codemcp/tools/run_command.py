#!/usr/bin/env python3

from typing import List, Optional

from .code_command import get_command_from_config, run_code_command

__all__ = [
    "run_command",
]


def run_command(
    project_dir: str, command: str, arguments: Optional[List[str]] = None
) -> str:
    """Run a command that is configured in codemcp.toml.

    Args:
        project_dir: The directory path containing the codemcp.toml file
        command: The type of command to run (e.g., "format", "lint", "test")
        arguments: Optional list of arguments to pass to the command

    Returns:
        A string containing the result of the command operation
    """
    command_list = get_command_from_config(project_dir, command)

    # If arguments are provided, extend the command with them
    if arguments and command_list:
        command_list = command_list.copy()
        command_list.extend(arguments)

    return run_code_command(
        project_dir, command, command_list, f"Auto-commit {command} changes"
    )
