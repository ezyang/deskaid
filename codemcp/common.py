#!/usr/bin/env python3

import os

# Constants
MAX_LINES_TO_READ = 1000
MAX_LINE_LENGTH = 1000
MAX_OUTPUT_SIZE = 0.25 * 1024 * 1024  # 0.25MB in bytes

__all__ = [
    "MAX_LINES_TO_READ",
    "MAX_LINE_LENGTH",
    "MAX_OUTPUT_SIZE",
    "is_image_file",
    "get_image_format",
    "normalize_file_path",
    "get_edit_snippet",
]


def is_image_file(file_path: str) -> bool:
    """Check if a file is an image based on its MIME type."""
    # Stub implementation - we don't care about image support
    return False


def get_image_format(file_path: str) -> str:
    """Get the format of an image file."""
    # Stub implementation - we don't care about image support
    return "png"


def normalize_file_path(file_path: str) -> str:
    """Normalize a file path to an absolute path."""
    if not os.path.isabs(file_path):
        return os.path.abspath(os.path.join(os.getcwd(), file_path))
    return os.path.abspath(file_path)


def get_edit_snippet(
    original_text: str,
    old_str: str,
    new_str: str,
    context_lines: int = 4,
) -> str:
    """Generate a snippet of the edited file showing the changes with line numbers.

    Args:
        original_text: The original file content
        old_str: The text that was replaced
        new_str: The new text that replaced old_str
        context_lines: Number of lines to show before and after the change

    Returns:
        A formatted string with line numbers and the edited content

    """
    # Find where the edit occurs
    before_text = original_text.split(old_str)[0]
    before_lines = before_text.split("\n")
    replacement_line = len(before_lines)

    # Get the edited content
    edited_text = original_text.replace(old_str, new_str)
    edited_lines = edited_text.split("\n")

    # Calculate the start and end line numbers for the snippet
    start_line = max(0, replacement_line - context_lines)
    end_line = min(
        len(edited_lines),
        replacement_line + context_lines + len(new_str.split("\n")),
    )

    # Extract the snippet lines
    snippet_lines = edited_lines[start_line:end_line]

    # Format with line numbers
    result = []
    for i, line in enumerate(snippet_lines):
        line_num = start_line + i + 1
        result.append(f"{line_num:4d} | {line}")

    return "\n".join(result)
