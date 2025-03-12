#!/usr/bin/env python3

import logging
import os

from ..access import check_edit_permission
from ..git import commit_pending_changes

__all__ = [
    "check_file_path_and_permissions",
    "check_git_tracking_for_existing_file",
    "ensure_directory_exists",
    "write_text_content",
]


def check_file_path_and_permissions(file_path: str) -> tuple[bool, str | None]:
    """Check if the file path is valid and has the necessary permissions.

    Args:
        file_path: The absolute path to the file

    Returns:
        A tuple of (is_valid, error_message)
        If is_valid is True, error_message will be None

    """
    # Check that the path is absolute
    if not os.path.isabs(file_path):
        return False, f"Error: File path must be absolute, not relative: {file_path}"

    # Check if we have permission to edit this file
    is_permitted, permission_message = check_edit_permission(file_path)
    if not is_permitted:
        return False, f"Error: {permission_message}"

    return True, None


def check_git_tracking_for_existing_file(file_path: str) -> tuple[bool, str | None]:
    """Check if an existing file is tracked by git. Skips check for non-existent files.

    Args:
        file_path: The absolute path to the file

    Returns:
        A tuple of (success, error_message)
        If success is True, error_message will be None

    """
    # Check if the file exists
    file_exists = os.path.exists(file_path)

    if file_exists:
        # Only check commit_pending_changes for existing files
        commit_success, commit_message = commit_pending_changes(file_path)
        if not commit_success:
            logging.debug(f"Failed to commit pending changes: {commit_message}")
            # Check if the file is not tracked by git
            if "not tracked by git" in commit_message:
                return False, commit_message
        else:
            logging.debug(f"Pending changes status: {commit_message}")

    return True, None


def ensure_directory_exists(file_path: str) -> None:
    """Ensure the directory for the file exists, creating it if necessary.

    Args:
        file_path: The absolute path to the file

    """
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def write_text_content(
    file_path: str,
    content: str,
    encoding: str = "utf-8",
    line_endings: str = None,
) -> None:
    """Write text content to a file with specified encoding and line endings.

    Args:
        file_path: The path to the file
        content: The content to write
        encoding: The encoding to use
        line_endings: The line endings to use ('CRLF', 'LF', '\r\n', or '\n')

    """
    # Handle different line ending formats: string constants or actual characters
    if isinstance(line_endings, str):
        if line_endings.upper() == "CRLF":
            actual_line_endings = "\r\n"
        elif line_endings.upper() == "LF":
            actual_line_endings = "\n"
        else:
            # Assume it's already the character sequence
            actual_line_endings = line_endings
    else:
        # Default to system line endings if None
        actual_line_endings = os.linesep

    # First normalize all line endings to \n
    normalized_content = content.replace("\r\n", "\n")

    # Then replace with the desired line endings if different from \n
    if actual_line_endings != "\n":
        final_content = normalized_content.replace("\n", actual_line_endings)
    else:
        final_content = normalized_content

    # Ensure directory exists
    ensure_directory_exists(file_path)

    # Write the content
    with open(file_path, "w", encoding=encoding) as f:
        f.write(final_content)
