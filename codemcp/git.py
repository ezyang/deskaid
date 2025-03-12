#!/usr/bin/env python3

import logging
import os
import subprocess

from .common import normalize_file_path
from .shell import run_command

__all__ = [
    "is_git_repository",
    "commit_pending_changes",
    "commit_changes",
]


def is_git_repository(path: str) -> bool:
    """Check if the path is within a Git repository.

    Args:
        path: The file path to check

    Returns:
        True if path is in a Git repository, False otherwise

    """
    try:
        # Get the directory containing the file or use the path itself if it's a directory
        directory = os.path.dirname(path) if os.path.isfile(path) else path

        # Get the absolute path to ensure consistency
        directory = os.path.abspath(directory)

        # Run git command to verify this is a git repository
        run_command(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=directory,
            check=True,
            capture_output=True,
            text=True,
        )

        # Also get the repository root to use for all git operations
        try:
            run_command(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            # Store the repository root in a global or class variable if needed
            # This could be used to ensure all git operations use the same root

            return True
        except (subprocess.SubprocessError, OSError):
            # If we can't get the repo root, it's not a proper git repository
            return False
    except (subprocess.SubprocessError, OSError):
        return False


def commit_pending_changes(file_path: str) -> tuple[bool, str]:
    """Commit any pending changes in the repository, excluding the target file.

    Args:
        file_path: The path to the file to exclude from committing

    Returns:
        A tuple of (success, message)

    """
    try:
        # First, check if this is a git repository
        if not is_git_repository(file_path):
            return False, "File is not in a Git repository"

        directory = os.path.dirname(file_path)

        # Check if the file is tracked by git
        file_status = run_command(
            ["git", "ls-files", "--error-unmatch", file_path],
            cwd=directory,
            capture_output=True,
            text=True,
            check=False,
        )

        file_is_tracked = file_status.returncode == 0

        # If the file is not tracked, return an error
        if not file_is_tracked:
            return (
                False,
                "File is not tracked by git. Please add the file to git tracking first using 'git add <file>'",
            )

        # Check if working directory has uncommitted changes
        status_result = run_command(
            ["git", "status", "--porcelain"],
            cwd=directory,
            capture_output=True,
            check=True,
            text=True,
        )

        # If there are uncommitted changes (besides our target file), commit them first
        if status_result.stdout and file_is_tracked:
            # Get list of changed files
            changed_files = []
            for line in status_result.stdout.splitlines():
                # Skip empty lines
                if not line.strip():
                    continue

                # git status --porcelain output format: XY filename
                # where X is status in staging area, Y is status in working tree
                # There are at least 2 spaces before the filename
                parts = line.strip().split(" ", 1)
                if len(parts) > 1:
                    # Extract the filename, removing any leading spaces
                    filename = parts[1].lstrip()
                    full_path = normalize_file_path(os.path.join(directory, filename))
                    # Skip our target file
                    if full_path != normalize_file_path(file_path):
                        changed_files.append(filename)

            if changed_files:
                # Commit other changes first with a default message
                run_command(
                    ["git", "add", "."],
                    cwd=directory,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                run_command(
                    ["git", "commit", "-m", "Snapshot before codemcp change"],
                    cwd=directory,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                return True, "Committed pending changes"

        return True, "No pending changes to commit"
    except Exception as e:
        logging.warning(
            f"Exception suppressed when committing pending changes: {e!s}",
            exc_info=True,
        )
        return False, f"Error committing pending changes: {e!s}"


def commit_changes(path: str, description: str) -> tuple[bool, str]:
    """Commit changes to a file or directory in Git.

    Args:
        path: The path to the file or directory to commit
        description: Commit message describing the change

    Returns:
        A tuple of (success, message)

    """
    try:
        # First, check if this is a git repository
        if not is_git_repository(path):
            return False, f"Path '{path}' is not in a Git repository"

        # Get absolute paths for consistency
        abs_path = os.path.abspath(path)

        # Get the directory - if path is a file, use its directory, otherwise use the path itself
        directory = os.path.dirname(abs_path) if os.path.isfile(abs_path) else abs_path

        # Try to get the git repository root for more reliable operations
        try:
            repo_root = run_command(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            # Use the repo root as the working directory for git commands
            git_cwd = repo_root
        except (subprocess.SubprocessError, OSError):
            # Fall back to the directory if we can't get the repo root
            git_cwd = directory

        # If it's a file, check if it exists
        if os.path.isfile(abs_path) and not os.path.exists(abs_path):
            return False, f"File does not exist: {abs_path}"

        # Add the path to git - could be a file or directory
        try:
            # If path is a directory, do git add .
            add_command = (
                ["git", "add", "."]
                if os.path.isdir(abs_path)
                else ["git", "add", abs_path]
            )

            add_result = run_command(
                add_command,
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception as e:
            return False, f"Failed to add to Git: {str(e)}"

        if add_result.returncode != 0:
            return False, f"Failed to add to Git: {add_result.stderr}"

        # First check if there's already a commit in the repository
        has_commits = False
        rev_parse_result = run_command(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=git_cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        has_commits = rev_parse_result.returncode == 0

        # Check if there are any staged changes to commit
        if has_commits:
            # Check if there are any changes to commit after git add
            diff_result = run_command(
                ["git", "diff-index", "--cached", "--quiet", "HEAD"],
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=False,
            )

            # If diff-index returns 0, there are no changes to commit
            if diff_result.returncode == 0:
                return (
                    True,
                    "No changes to commit (changes already committed or no changes detected)",
                )

        # Commit the change
        commit_result = run_command(
            ["git", "commit", "-m", description],
            cwd=git_cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        if commit_result.returncode != 0:
            return False, f"Failed to commit changes: {commit_result.stderr}"

        return True, "Changes committed successfully"
    except Exception as e:
        logging.warning(
            f"Exception suppressed when committing changes: {e!s}", exc_info=True
        )
        return False, f"Error committing changes: {e!s}"
