#!/usr/bin/env python3

import logging
import os
import subprocess
from typing import List, Optional

import tomli

from ..common import normalize_file_path
from ..git import commit_changes, is_git_repository
from ..shell import run_command

__all__ = [
    "get_command_from_config",
    "check_for_changes",
    "run_code_command",
]


def get_command_from_config(project_dir: str, command_name: str) -> Optional[List[str]]:
    """Get a command from the codemcp.toml file.

    Args:
        project_dir: The directory path containing the codemcp.toml file
        command_name: The name of the command to retrieve (e.g., "lint", "format")

    Returns:
        A list of command parts if configured, None otherwise
    """
    try:
        full_dir_path = normalize_file_path(project_dir)
        config_path = os.path.join(full_dir_path, "codemcp.toml")

        if not os.path.exists(config_path):
            logging.warning(f"Config file not found: {config_path}")
            return None

        with open(config_path, "rb") as f:
            config = tomli.load(f)

        if "commands" in config and command_name in config["commands"]:
            cmd_config = config["commands"][command_name]
            # Handle both direct command lists and dictionaries with 'command' field
            if isinstance(cmd_config, list):
                return cmd_config
            elif isinstance(cmd_config, dict) and "command" in cmd_config:
                return cmd_config["command"]

        return None
    except Exception as e:
        logging.error(f"Error loading {command_name} command: {e}")
        return None


def check_for_changes(project_dir: str) -> bool:
    """Check if an operation made any changes to the code.

    Args:
        project_dir: The directory path to check

    Returns:
        True if changes were detected, False otherwise
    """
    try:
        # Get the git repository root for reliable status checking
        try:
            repo_root = run_command(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            # Use the repo root as working directory for git commands
            git_cwd = repo_root
        except (subprocess.SubprocessError, OSError) as e:
            logging.error(f"Error getting git repository root: {e}")
            # Fall back to the project directory
            git_cwd = project_dir

        # Check if working directory has uncommitted changes
        status_result = run_command(
            ["git", "status", "--porcelain"],
            cwd=git_cwd,
            check=True,
            capture_output=True,
            text=True,
        )

        # If status output is not empty, there are changes
        return bool(status_result.stdout.strip())
    except Exception as e:
        logging.error(f"Error checking for git changes: {e}")
        return False


def run_code_command(
    project_dir: str, command_name: str, command: List[str], commit_message: str
) -> str:
    """Run a code command (lint, format, etc.) and handle git operations.

    Args:
        project_dir: The directory path containing the code to process
        command_name: The name of the command for logging and messages (e.g., "lint", "format")
        command: The command to run
        commit_message: The commit message to use if changes are made

    Returns:
        A string containing the result of the operation
    """
    try:
        full_dir_path = normalize_file_path(project_dir)

        if not os.path.exists(full_dir_path):
            return f"Error: Directory does not exist: {project_dir}"

        if not os.path.isdir(full_dir_path):
            return f"Error: Path is not a directory: {project_dir}"

        if not command:
            # Map the command_name to keep backward compatibility with existing tests
            command_key = command_name
            if command_name == "linting":
                command_key = "lint"
            elif command_name == "formatting":
                command_key = "format"

            return f"Error: No {command_key} command configured in codemcp.toml"

        # Check if directory is in a git repository
        is_git_repo = is_git_repository(full_dir_path)

        # If it's a git repo, commit any pending changes before running the command
        if is_git_repo:
            logging.info(f"Committing any pending changes before {command_name}")
            commit_result = commit_changes(
                full_dir_path, f"Snapshot before auto-{command_name}"
            )
            if not commit_result[0]:
                logging.warning(f"Failed to commit pending changes: {commit_result[1]}")

        # Run the command
        try:
            result = run_command(
                command,
                cwd=full_dir_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Additional logging is already done by run_command

            # If it's a git repo, commit any changes made by the command
            if is_git_repo:
                has_changes = check_for_changes(full_dir_path)
                if has_changes:
                    logging.info(f"Changes detected after {command_name}, committing")
                    success, commit_result_message = commit_changes(
                        full_dir_path, commit_message
                    )

                    if success:
                        return f"Code {command_name} successful and changes committed:\n{result.stdout}"
                    else:
                        logging.warning(
                            f"Failed to commit {command_name} changes: {commit_result_message}"
                        )
                        return f"Code {command_name} successful but failed to commit changes:\n{result.stdout}\nCommit error: {commit_result_message}"

            return f"Code {command_name} successful:\n{result.stdout}"
        except subprocess.CalledProcessError as e:
            # Map the command_name to keep backward compatibility with existing tests
            command_key = command_name.title()
            if command_name == "linting":
                command_key = "Lint"
            elif command_name == "formatting":
                command_key = "Format"

            # Include both stdout and stderr in the error message
            stdout_info = f"STDOUT:\n{e.output}" if e.output else "STDOUT: <empty>"
            stderr_info = f"STDERR:\n{e.stderr}" if e.stderr else "STDERR: <empty>"
            error_msg = f"{command_key} command failed with exit code {e.returncode}:\n{stdout_info}\n{stderr_info}"

            # Note: run_command already logs the command and stderr at debug level
            # We just need to log the error summary at error level
            logging.error(
                f"{command_name.title()} command failed with exit code {e.returncode}"
            )
            return f"Error: {error_msg}"

    except Exception as e:
        error_msg = f"Error during {command_name}: {e}"
        logging.error(error_msg)
        return f"Error: {error_msg}"
