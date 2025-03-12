#!/usr/bin/env python3

import os

from ..git import commit_changes
from .file_utils import (
    check_file_path_and_permissions,
    check_git_tracking_for_existing_file,
    write_text_content,
)

__all__ = [
    "write_file_content",
    "detect_file_encoding",
    "detect_line_endings",
    "detect_repo_line_endings",
]


def detect_file_encoding(file_path: str) -> str:
    """Detect the encoding of a file.

    Args:
        file_path: The path to the file

    Returns:
        The detected encoding, defaulting to 'utf-8'

    """
    # Simple implementation - in a real-world scenario, you might use chardet or similar
    try:
        # Try to read the file with utf-8 encoding
        with open(file_path, encoding="utf-8") as f:
            f.read()
        return "utf-8"
    except UnicodeDecodeError:
        # If utf-8 fails, default to binary mode
        return "latin-1"  # A safe fallback
    except FileNotFoundError:
        # For non-existent files, default to utf-8
        return "utf-8"


def detect_line_endings(file_path: str) -> str:
    """Detect the line endings of a file.

    Args:
        file_path: The path to the file

    Returns:
        The detected line endings ('\n' or '\r\n')

    """
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        if b"\r\n" in content:
            return "\r\n"
        return "\n"
    except Exception:
        return os.linesep


def detect_repo_line_endings(directory: str) -> str:
    """Detect the line endings used in a repository.

    Args:
        directory: The repository directory

    Returns:
        The detected line endings ('\n' or '\r\n')

    """
    # Default to system line endings
    return os.linesep


def write_file_content(file_path: str, content: str, description: str = "") -> str:
    """Write content to a file.

    Args:
        file_path: The absolute path to the file to write
        content: The content to write to the file
        description: Short description of the change

    Returns:
        A success message or an error message

    Note:
        This function allows creating new files that don't exist yet.
        For existing files, it will reject attempts to write to files that are not tracked by git.
        Files must be tracked in the git repository before they can be modified.

    """
    try:
        # Validate file path and permissions
        is_valid, error_message = check_file_path_and_permissions(file_path)
        if not is_valid:
            return error_message

        # Check git tracking for existing files
        is_tracked, track_error = check_git_tracking_for_existing_file(file_path)
        if not is_tracked:
            return f"Error: {track_error}"

        # Determine encoding and line endings
        old_file_exists = os.path.exists(file_path)
        encoding = detect_file_encoding(file_path) if old_file_exists else "utf-8"

        if old_file_exists:
            line_endings = detect_line_endings(file_path)
        else:
            line_endings = detect_repo_line_endings(os.path.dirname(file_path))
            # Ensure directory exists for new files
            directory = os.path.dirname(file_path)
            os.makedirs(directory, exist_ok=True)

        # Write the content with proper encoding and line endings
        write_text_content(file_path, content, encoding, line_endings)

        # Commit the changes
        git_message = ""
        success, message = commit_changes(file_path, description)
        if success:
            git_message = f"\nChanges committed to git: {description}"
        else:
            git_message = f"\nFailed to commit changes to git: {message}"

        return f"Successfully wrote to {file_path}{git_message}"
    except Exception as e:
        return f"Error writing file: {e!s}"
