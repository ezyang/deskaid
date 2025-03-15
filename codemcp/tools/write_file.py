#!/usr/bin/env python3

import asyncio
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


async def detect_file_encoding(file_path: str) -> str:
    """Detect the encoding of a file.

    Args:
        file_path: The path to the file

    Returns:
        The detected encoding, defaulting to 'utf-8'

    """
    # Simple implementation - in a real-world scenario, you might use chardet or similar
    loop = asyncio.get_event_loop()

    def read_file_utf8():
        try:
            with open(file_path, encoding="utf-8") as f:
                f.read()
            return "utf-8"
        except UnicodeDecodeError:
            return "latin-1"  # A safe fallback
        except FileNotFoundError:
            return "utf-8"

    return await loop.run_in_executor(None, read_file_utf8)


async def detect_line_endings(file_path: str) -> str:
    """Detect the line endings of a file.

    Args:
        file_path: The path to the file

    Returns:
        The detected line endings ('\n' or '\r\n')

    """
    loop = asyncio.get_event_loop()

    def read_and_detect():
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            if b"\r\n" in content:
                return "\r\n"
            return "\n"
        except Exception:
            return os.linesep

    return await loop.run_in_executor(None, read_and_detect)


def detect_repo_line_endings(directory: str) -> str:
    """Detect the line endings used in a repository.

    Args:
        directory: The repository directory

    Returns:
        The detected line endings ('\n' or '\r\n')

    """
    # Default to system line endings
    return os.linesep


async def write_file_content(
    file_path: str, content: str, description: str = "", chat_id: str = None, force_commit: bool = False
) -> str:
    """Write content to a file.

    Args:
        file_path: The absolute path to the file to write
        content: The content to write to the file
        description: Short description of the change
        chat_id: The unique ID of the current chat session
        force_commit: Whether to force committing changes, ignoring auto_commit setting

    Returns:
        A success message or an error message

    Note:
        This function allows creating new files that don't exist yet.
        For existing files, it will reject attempts to write to files that are not tracked by git.
        Files must be tracked in the git repository before they can be modified.
        
        By default, this function follows the auto_commit configuration to determine
        whether changes should be automatically committed. Set force_commit=True to
        override this behavior and always commit.

    """
    try:
        # Validate file path and permissions
        is_valid, error_message = await check_file_path_and_permissions(file_path)
        if not is_valid:
            raise ValueError(error_message)

        # Check git tracking for existing files
        is_tracked, track_error = await check_git_tracking_for_existing_file(file_path)
        if not is_tracked:
            raise ValueError(track_error)

        # Determine encoding and line endings
        old_file_exists = os.path.exists(file_path)
        encoding = await detect_file_encoding(file_path) if old_file_exists else "utf-8"

        if old_file_exists:
            line_endings = await detect_line_endings(file_path)
        else:
            line_endings = detect_repo_line_endings(os.path.dirname(file_path))
            # Ensure directory exists for new files
            directory = os.path.dirname(file_path)
            os.makedirs(directory, exist_ok=True)

        # Write the content with proper encoding and line endings
        await write_text_content(file_path, content, encoding, line_endings)

        # Commit the changes
        git_message = ""
        success, message = await commit_changes(file_path, description, chat_id, force_commit=force_commit)
        if success:
            if "not committed" in message:
                git_message = f"\n{message}"
            else:
                git_message = f"\nChanges committed to git: {description}"
        else:
            git_message = f"\nFailed to commit changes to git: {message}"

        return f"Successfully wrote to {file_path}{git_message}"
    except Exception as e:
        return f"Error writing file: {e!s}"
