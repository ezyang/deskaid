#!/usr/bin/env python3

import logging
import os
import subprocess

import toml

from .shell import run_command

__all__ = [
    "get_git_base_dir",
    "check_edit_permission",
]


def get_git_base_dir(file_path: str) -> str | None:
    """Get the base directory of the git repository containing the file.

    Args:
        file_path: The path to the file or directory

    Returns:
        The base directory of the git repository, or None if not in a git repository

    """
    try:
        # First normalize the path to resolve any .. or symlinks
        normalized_path = os.path.normpath(os.path.abspath(file_path))

        # Get the directory containing the file - handle non-existent files
        if os.path.exists(normalized_path):
            directory = (
                os.path.dirname(normalized_path)
                if os.path.isfile(normalized_path)
                else normalized_path
            )
        else:
            # For non-existent files, get the parent directory
            directory = os.path.dirname(normalized_path)

            # If trying to access a directory outside of the repo via path traversal,
            # we should detect it by checking if the directory exists after normalization
            if not os.path.exists(directory):
                # Store the original parent for security check
                os.path.dirname(normalized_path)

                # Walk up the directory tree until we find an existing directory
                while directory and not os.path.exists(directory):
                    logging.debug(f"Directory doesn't exist, walking up: {directory}")
                    parent = os.path.dirname(directory)
                    # If we've reached the root directory and it doesn't exist, stop
                    if parent == directory:
                        logging.debug(
                            f"Reached root directory and it doesn't exist: {directory}"
                        )
                        return None
                    directory = parent

                # If we couldn't find an existing parent directory, stop
                if not directory or not os.path.exists(directory):
                    logging.debug(
                        f"Could not find an existing parent directory for: {normalized_path}"
                    )
                    return None

                logging.debug(f"Found existing parent directory: {directory}")

        # Run git command to get the top-level directory of the repository
        result = run_command(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=directory,
            capture_output=True,
            check=True,
            text=True,
        )

        # Return the path
        git_base_dir = result.stdout.strip()
        logging.debug(f"Git base directory: {git_base_dir}")

        # SECURITY CHECK: Ensure file_path is within the git repository
        # This prevents path traversal across repositories

        # Handle symlinked paths (on macOS /tmp links to /private/tmp)
        normalized_git_base = os.path.normpath(os.path.realpath(git_base_dir))
        normalized_path = os.path.normpath(os.path.realpath(normalized_path))

        # Perform path traversal check - ensure target path is inside git repo
        try:
            # Check if the path is within the git repo by calculating the relative path
            rel_path = os.path.relpath(normalized_path, normalized_git_base)

            # If the relative path starts with "..", it's outside the git repo
            if rel_path.startswith("..") or rel_path == "..":
                logging.debug(
                    f"Path traversal check: {normalized_path} is outside git repo {normalized_git_base}"
                )

                # Special case: On macOS, check for /private/tmp vs /tmp differences
                # If either path contains the other after normalization, they might be the same location
                if (
                    normalized_git_base in normalized_path
                    or normalized_path in normalized_git_base
                ):
                    logging.debug(
                        f"Path might be the same location after symlinks: {normalized_path}, {normalized_git_base}"
                    )
                else:
                    logging.warning(
                        f"File path {file_path} is outside git repository {git_base_dir}"
                    )
                    return None
        except (ValueError, OSError) as e:
            logging.warning(
                f"File path {normalized_path} cannot be compared with git repository {normalized_git_base}: {e}"
            )
            return None

        return git_base_dir
    except (subprocess.SubprocessError, OSError) as e:
        logging.debug(f"Error finding git base directory: {e!s}")
        return None


def check_edit_permission(file_path: str) -> tuple[bool, str]:
    """Check if editing the file is permitted based on the presence of codemcp.toml
    in the git repository's root directory.

    Args:
        file_path: The path to the file to edit

    Returns:
        A tuple of (is_permitted, message)

    """
    # Get the git base directory
    git_base_dir = get_git_base_dir(file_path)

    # If not in a git repository, deny access
    if not git_base_dir:
        return False, "File is not in a git repository. Permission denied."

    # Check for codemcp.toml in the git base directory
    config_path = os.path.join(git_base_dir, "codemcp.toml")
    if not os.path.exists(config_path):
        return False, (
            "Permission denied: codemcp.toml file not found in the git repository root. "
            "Please create a codemcp.toml file in the root directory of your project "
            "to enable editing files with codemcp."
        )

    # Optionally, verify the content of the codemcp.toml file
    try:
        toml.load(config_path)
        # You can add more sophisticated permission checks here based on the config
        # For example, check for allowed_directories, deny_patterns, etc.
        return True, "Permission granted."
    except Exception as e:
        logging.warning(
            f"Exception suppressed when parsing codemcp.toml: {e!s}", exc_info=True
        )
        return False, f"Error parsing codemcp.toml file: {e!s}"
