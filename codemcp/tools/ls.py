#!/usr/bin/env python3

import logging
import os

from ..access import check_edit_permission
from ..common import normalize_file_path
from ..git import is_git_repository

__all__ = [
    "ls_directory",
    "list_directory",
    "skip",
    "TreeNode",
    "create_file_tree",
    "print_tree",
    "MAX_FILES",
]

MAX_FILES = 1000
TRUNCATED_MESSAGE = f"There are more than {MAX_FILES} files in the directory. Use more specific paths to explore nested directories. The first {MAX_FILES} files and directories are included below:\n\n"


def ls_directory(directory_path: str) -> str:
    """List the contents of a directory.

    Args:
        directory_path: The absolute path to the directory to list

    Returns:
        A formatted string representation of the directory contents, or an error message

    """
    try:
        # Normalize the directory path
        full_directory_path = normalize_file_path(directory_path)

        # Validate the directory path
        if not os.path.exists(full_directory_path):
            return f"Error: Directory does not exist: {directory_path}"

        if not os.path.isdir(full_directory_path):
            return f"Error: Path is not a directory: {directory_path}"

        # Safety check: Verify the directory is within a git repository with codemcp.toml
        if not is_git_repository(full_directory_path):
            return f"Error: Directory is not in a Git repository: {directory_path}"

        # Check edit permission (which verifies codemcp.toml exists)
        is_permitted, permission_message = check_edit_permission(full_directory_path)
        if not is_permitted:
            return f"Error: {permission_message}"

        # Get the directory contents
        results = list_directory(full_directory_path)

        # Sort the results
        results.sort()

        # Create a file tree and print it
        tree = create_file_tree(results)
        tree_output = print_tree(tree, cwd=full_directory_path)

        # Add safety warning for the assistant

        # Return the result with truncation message if needed
        if len(results) < MAX_FILES:
            return tree_output
        return f"{TRUNCATED_MESSAGE}{tree_output}"
    except Exception as e:
        logging.warning(
            f"Exception suppressed during directory listing: {e!s}", exc_info=True
        )
        return f"Error listing directory: {e!s}"


def list_directory(initial_path: str) -> list[str]:
    """List all files and directories recursively.

    Args:
        initial_path: The path to start listing from

    Returns:
        A list of relative paths to files and directories

    """
    results = []

    queue = [initial_path]
    while queue and len(results) <= MAX_FILES:
        path = queue.pop(0)

        if skip(path) and path != initial_path:
            continue

        if path != initial_path:
            # Add directories with trailing slash
            rel_path = os.path.relpath(path, initial_path)
            if os.path.isdir(path):
                rel_path = f"{rel_path}{os.sep}"
            results.append(rel_path)

        if os.path.isdir(path):
            try:
                children = os.listdir(path)
                for child in children:
                    child_path = os.path.join(path, child)
                    if os.path.isdir(child_path):
                        queue.append(child_path)
                    elif not skip(child_path):
                        rel_path = os.path.relpath(child_path, initial_path)
                        results.append(rel_path)
                        if len(results) > MAX_FILES:
                            return results
            except (PermissionError, OSError):
                # Skip directories we can't access
                continue

    return results


def skip(path: str) -> bool:
    """Determine if a path should be skipped.

    Args:
        path: The path to check

    Returns:
        True if the path should be skipped, False otherwise

    """
    basename = os.path.basename(path)
    if path != "." and basename.startswith("."):
        return True
    if "__pycache__" in path:
        return True
    return False


class TreeNode:
    """A node in a file tree."""

    def __init__(self, name: str, path: str, node_type: str):
        self.name = name
        self.path = path
        self.type = node_type
        self.children = []


def create_file_tree(sorted_paths: list[str]) -> list[TreeNode]:
    """Create a file tree from a list of paths.

    Args:
        sorted_paths: A list of sorted relative paths

    Returns:
        A list of TreeNode objects representing the root of the tree

    """
    root = []

    for path in sorted_paths:
        parts = path.split(os.sep)
        current_level = root
        current_path = ""

        for i, part in enumerate(parts):
            if not part:  # Skip empty parts (trailing slashes)
                continue

            current_path = os.path.join(current_path, part) if current_path else part
            is_last_part = i == len(parts) - 1

            # Check if this node already exists at this level
            existing_node = None
            for node in current_level:
                if node.name == part:
                    existing_node = node
                    break

            if existing_node:
                current_level = existing_node.children
            else:
                # Create a new node
                node_type = (
                    "file"
                    if is_last_part and not path.endswith(os.sep)
                    else "directory"
                )
                new_node = TreeNode(part, current_path, node_type)
                current_level.append(new_node)
                current_level = new_node.children

    return root


def print_tree(
    tree: list[TreeNode],
    level: int = 0,
    prefix: str = "",
    cwd: str = "",
) -> str:
    """Print a file tree.

    Args:
        tree: A list of TreeNode objects
        level: The current level in the tree
        prefix: The prefix to use for indentation
        cwd: The current working directory

    Returns:
        A formatted string representation of the tree

    """
    result = ""

    # Add absolute path at root level
    if level == 0:
        result += f"- {cwd}{os.sep}\n"
        prefix = "  "

    for node in tree:
        # Add the current node to the result
        node_suffix = f"{os.sep}" if node.type == "directory" else ""
        result += f"{prefix}{'-'} {node.name}{node_suffix}\n"

        # Recursively print children
        if node.children:
            result += print_tree(node.children, level + 1, f"{prefix}  ", cwd)

    return result
