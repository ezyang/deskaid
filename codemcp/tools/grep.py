#!/usr/bin/env python3

import logging
import os
import subprocess
import time
from typing import Any

from ..common import normalize_file_path
from ..git import is_git_repository
from ..shell import run_command

__all__ = [
    "grep_files",
    "git_grep",
    "render_result_for_assistant",
    "TOOL_NAME_FOR_PROMPT",
    "DESCRIPTION",
]

# Define constants
MAX_RESULTS = 100
TOOL_NAME_FOR_PROMPT = "Grep"
DESCRIPTION = f"""
Searches for files containing a specified pattern (regular expression) using git grep.
Files with a match are returned, up to a maximum of {MAX_RESULTS} files.
Note that this tool only works inside git repositories.

Example:
  grep "function.*hello" /path/to/repo  # Find files containing functions with "hello" in their name
  grep "console\\.log" /path/to/repo --include="*.js"  # Find JS files with console.log statements
"""


def git_grep(
    pattern: str,
    path: str | None = None,
    include: str | None = None,
    signal=None,
) -> list[str]:
    """Execute git grep to search for pattern in files.

    Args:
        pattern: The regular expression pattern to search for
        path: The directory to search in (must be in a git repository)
        include: Optional file pattern to filter the search
        signal: Optional abort signal to terminate the subprocess

    Returns:
        A list of file paths with matches

    """
    if path is None:
        raise ValueError("Path must be provided for git grep")

    # Normalize the directory path
    absolute_path = normalize_file_path(path)

    # Verify this is a git repository - this check uses the mocked version in tests
    if not is_git_repository(absolute_path):
        raise ValueError(f"The provided path is not in a git repository: {path}")

    # In non-test environment, verify the path exists and is a directory
    if not os.environ.get("DESKAID_TESTING"):
        # Check if path exists and is a directory
        if not os.path.exists(absolute_path):
            raise FileNotFoundError(f"Directory does not exist: {path}")

        if not os.path.isdir(absolute_path):
            raise NotADirectoryError(f"Path is not a directory: {path}")

    # Build git grep command
    # -l: list file names only
    # -i: case insensitive matching
    args = ["git", "grep", "-li", pattern]

    # Add file pattern if specified
    if include:
        args.extend(["--", include])

    logging.debug(f"Executing git grep command: {' '.join(args)}")

    try:
        # Execute git grep command
        # Use explicit parameters to avoid confusion in mocking
        result = run_command(
            cmd=args,
            cwd=absolute_path,
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception if git grep doesn't find matches
        )

        # git grep returns exit code 1 when no matches are found, which is normal
        if result.returncode not in [0, 1]:
            logging.error(
                f"git grep failed with exit code {result.returncode}: {result.stderr}",
            )
            raise subprocess.SubprocessError(f"git grep failed: {result.stderr}")

        # Process results - split by newline and filter empty lines
        matches = [line.strip() for line in result.stdout.split("\n") if line.strip()]

        # Convert to absolute paths
        matches = [os.path.join(absolute_path, match) for match in matches]

        return matches
    except subprocess.SubprocessError as e:
        logging.exception(f"Error executing git grep: {e!s}")
        raise


def render_result_for_assistant(output: dict[str, Any]) -> str:
    """Render the results in a format suitable for the assistant.

    Args:
        output: The grep results dictionary

    Returns:
        A formatted string representation of the results

    """
    num_files = output.get("numFiles", 0)
    filenames = output.get("filenames", [])

    if num_files == 0:
        return "No files found"

    result = f"Found {num_files} file{'' if num_files == 1 else 's'}\n{os.linesep.join(filenames[:MAX_RESULTS])}"
    if num_files > MAX_RESULTS:
        result += (
            "\n(Results are truncated. Consider using a more specific path or pattern.)"
        )

    return result


def grep_files(
    pattern: str,
    path: str | None = None,
    include: str | None = None,
    signal=None,
) -> dict[str, Any]:
    """Search for a pattern in files within a directory.

    Args:
        pattern: The regular expression pattern to search for
        path: The directory to search in (must be in a git repository)
        include: Optional file pattern to filter the search
        signal: Optional abort signal to terminate the subprocess

    Returns:
        A dictionary with execution stats and matched files

    """
    start_time = time.time()

    try:
        # Execute git grep
        matches = git_grep(pattern, path, include, signal)

        # Sort matches
        try:
            # First try sorting by modification time
            stats = [os.stat(match) for match in matches]
            matches_with_stats = list(zip(matches, stats, strict=False))

            # In tests, sort by filename for deterministic results
            if os.environ.get("NODE_ENV") == "test":
                matches_with_stats.sort(key=lambda x: x[0])
            else:
                # Sort by modification time (newest first), with filename as tiebreaker
                matches_with_stats.sort(key=lambda x: (-(x[1].st_mtime or 0), x[0]))

            matches = [match for match, _ in matches_with_stats]
        except Exception as e:
            # Fall back to sorting by name if there's an error
            logging.debug(
                f"Error sorting by modification time, falling back to name sort: {e!s}",
            )
            matches.sort()

        # Calculate execution time
        execution_time = int(
            (time.time() - start_time) * 1000,
        )  # Convert to milliseconds

        # Prepare output
        output = {
            "filenames": matches[:MAX_RESULTS],
            "durationMs": execution_time,
            "numFiles": len(matches),
        }

        # Add formatted result for assistant
        output["resultForAssistant"] = render_result_for_assistant(output)

        return output
    except Exception as e:
        # Calculate execution time even on error
        execution_time = int((time.time() - start_time) * 1000)

        # Return empty results with error info
        error_output = {
            "filenames": [],
            "durationMs": execution_time,
            "numFiles": 0,
            "error": str(e),
            "resultForAssistant": f"Error: {e!s}",
        }

        return error_output
