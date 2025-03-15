#!/usr/bin/env python3

import logging
import os
import subprocess

from .config import get_auto_commit
from .git_message import (
    append_metadata_to_message,
    update_commit_message_with_description,
)
from .git_query import (
    get_head_commit_chat_id,
    get_head_commit_hash,
    get_head_commit_message,
    is_git_repository,
)
from .shell import run_command

__all__ = ["commit_changes", "create_commit_reference"]

log = logging.getLogger(__name__)


async def create_commit_reference(
    path: str,
    description: str,
    chat_id: str,
    ref_name: str = None,
    custom_message: str = None,
) -> tuple[bool, str, str]:
    """Create a Git commit without advancing HEAD and store it in a reference.

    This function creates a commit using Git plumbing commands and stores it in
    a reference (refs/codemcp/<chat_id>) without changing HEAD.

    Args:
        path: The path to the file or directory to commit
        description: Commit message describing the change
        chat_id: The unique ID of the current chat session
        ref_name: Optional custom reference name (defaults to refs/codemcp/<chat_id>)
        custom_message: Optional custom commit message (overrides description)

    Returns:
        A tuple of (success, message, commit_hash)
    """
    log.debug(
        "create_commit_reference(%s, %s, %s, %s)", path, description, chat_id, ref_name
    )
    try:
        # First, check if this is a git repository
        if not await is_git_repository(path):
            return False, f"Path '{path}' is not in a Git repository", ""

        # Get absolute paths for consistency
        abs_path = os.path.abspath(path)

        # Get the directory - if path is a file, use its directory, otherwise use the path itself
        directory = os.path.dirname(abs_path) if os.path.isfile(abs_path) else abs_path

        # Try to get the git repository root for more reliable operations
        try:
            repo_root = (
                await run_command(
                    ["git", "rev-parse", "--show-toplevel"],
                    cwd=directory,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            ).stdout.strip()

            # Use the repo root as the working directory for git commands
            git_cwd = repo_root
        except (subprocess.SubprocessError, OSError):
            # Fall back to the directory if we can't get the repo root
            git_cwd = directory

        # Use the default reference name if none provided
        if ref_name is None:
            ref_name = f"refs/codemcp/{chat_id}"

        # Create the tree object for the empty commit
        # Get the tree from HEAD or create a new empty tree if no HEAD exists
        tree_hash = ""
        has_commits = False
        rev_parse_result = await run_command(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=git_cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        if rev_parse_result.returncode == 0:
            has_commits = True
            tree_result = await run_command(
                ["git", "show", "-s", "--format=%T", "HEAD"],
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=True,
            )
            tree_hash = tree_result.stdout.strip()
        else:
            # Create an empty tree if no HEAD exists
            empty_tree_result = await run_command(
                ["git", "mktree"],
                cwd=git_cwd,
                input="",
                capture_output=True,
                text=True,
                check=True,
            )
            tree_hash = empty_tree_result.stdout.strip()

        # Prepare the commit message with metadata
        if custom_message:
            # Use our updated function to prepare the message
            commit_message = update_commit_message_with_description(
                current_commit_message=custom_message,
                description="",  # Empty because we're not adding a description
                chat_id=chat_id,
            )
        else:
            # Start with the description and add chat_id
            commit_message = description
            if chat_id:
                commit_message = append_metadata_to_message(
                    commit_message, {"codemcp-id": chat_id}
                )

        # Get parent commit if we have HEAD
        parent_arg = []
        if has_commits:
            head_hash_result = await run_command(
                ["git", "rev-parse", "HEAD"],
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=True,
            )
            head_hash = head_hash_result.stdout.strip()
            parent_arg = ["-p", head_hash]

        # Create the commit object
        commit_result = await run_command(
            ["git", "commit-tree", tree_hash, *parent_arg, "-m", commit_message],
            cwd=git_cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = commit_result.stdout.strip()

        # Update the reference to point to the new commit
        await run_command(
            ["git", "update-ref", ref_name, commit_hash],
            cwd=git_cwd,
            capture_output=True,
            text=True,
            check=True,
        )

        return (
            True,
            f"Created commit reference {ref_name} -> {commit_hash}",
            commit_hash,
        )
    except Exception as e:
        logging.warning(
            f"Exception when creating commit reference: {e!s}", exc_info=True
        )
        return False, f"Error creating commit reference: {e!s}", ""


async def commit_changes(
    path: str = None,
    description: str = "",
    chat_id: str = None,
    allow_empty: bool = False,
    custom_message: str = None,
    commit_all: bool = False,
    force_commit: bool = False,
) -> tuple[bool, str]:
    """Commit changes to a file, directory, or all files in Git.

    This function will either create a new commit with the chat_id metadata,
    or amend the HEAD commit if it belongs to the same chat session.

    If HEAD doesn't have the right chat_id but there's a commit reference for this
    chat_id, it will cherry-pick that reference first to create the initial commit
    and then proceed with the changes.

    If commit_all is True, all changes in the repository will be committed.
    When commit_all is True, path can be None.

    The function respects the auto_commit configuration setting, which can be set in:
    1. Environment variable CODEMCP_AUTO_COMMIT
    2. Project's codemcp.toml file under [git] auto_commit = true/false
    3. User's ~/.codemcprc file
    Set force_commit=True to override this setting.

    Args:
        path: The path to the file or directory to commit (optional if commit_all is True)
        description: Commit message describing the change
        chat_id: The unique ID of the current chat session
        allow_empty: Whether to allow empty commits (no changes)
        custom_message: Optional custom commit message (overrides description)
        commit_all: Whether to commit all changes in the repository
        force_commit: Whether to force committing changes, ignoring auto_commit setting

    Returns:
        A tuple of (success, message)

    """
    log.debug(
        "commit_changes(%s, %s, %s, commit_all=%s, force_commit=%s)",
        path,
        description,
        chat_id,
        commit_all,
        force_commit,
    )
    
    # Check auto_commit setting based on project path
    repo_path = path
    if path and os.path.isfile(path):
        repo_path = os.path.dirname(path)
    
    # Skip commit based on auto_commit setting, unless force_commit is True
    if not force_commit and not get_auto_commit(repo_path):
        return True, "Auto-commit is disabled. Changes were not committed."
    try:
        # Need either a path or commit_all=True
        if path is None and not commit_all:
            return False, "Either path must be provided or commit_all must be True"

        # Determine working directory for git operations
        working_dir = None
        if path is not None:
            # First, check if this is a git repository
            if not await is_git_repository(path):
                return False, f"Path '{path}' is not in a Git repository"

            # Get absolute paths for consistency
            abs_path = os.path.abspath(path)

            # Get the directory - if path is a file, use its directory, otherwise use the path itself
            working_dir = (
                os.path.dirname(abs_path) if os.path.isfile(abs_path) else abs_path
            )

            # If it's a file, check if it exists (only if not commit_all mode)
            if (
                not commit_all
                and os.path.isfile(abs_path)
                and not os.path.exists(abs_path)
            ):
                return False, f"File does not exist: {abs_path}"
        else:
            # If no path is provided, use the current directory
            working_dir = os.getcwd()

        # Try to get the git repository root for more reliable operations
        try:
            repo_root = (
                await run_command(
                    ["git", "rev-parse", "--show-toplevel"],
                    cwd=working_dir,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            ).stdout.strip()

            # Use the repo root as the working directory for git commands
            git_cwd = repo_root
        except (subprocess.SubprocessError, OSError):
            # Fall back to the directory if we can't get the repo root
            git_cwd = working_dir

        # Handle commit_all mode
        if commit_all:
            # Check if working directory has uncommitted changes
            status_result = await run_command(
                ["git", "status", "--porcelain"],
                cwd=git_cwd,
                capture_output=True,
                check=True,
                text=True,
            )

            if status_result.stdout:
                # Add all changes to staging
                add_result = await run_command(
                    ["git", "add", "."],
                    cwd=git_cwd,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            else:
                # No changes to commit
                return True, "No changes to commit"
        else:
            # Standard path-specific mode
            # Add the path to git - could be a file or directory
            try:
                # If path is a directory, do git add .
                add_command = (
                    ["git", "add", "."]
                    if os.path.isdir(abs_path)
                    else ["git", "add", abs_path]
                )

                add_result = await run_command(
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
        rev_parse_result = await run_command(
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
            diff_result = await run_command(
                ["git", "diff-index", "--cached", "--quiet", "HEAD"],
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=False,
            )

            # If diff-index returns 0, there are no changes to commit
            if diff_result.returncode == 0 and not allow_empty:
                return (
                    True,
                    "No changes to commit (changes already committed or no changes detected)",
                )

        # Determine whether to amend or create a new commit
        head_chat_id = await get_head_commit_chat_id(git_cwd) if has_commits else None
        logging.debug(
            "commit_changes: has_commits = %r, head_chat_id = %s",
            has_commits,
            head_chat_id,
        )

        # If HEAD exists but doesn't have the right chat_id, check if we have a
        # commit reference for this chat_id that we need to cherry-pick first
        if has_commits and chat_id and head_chat_id != chat_id:
            ref_name = f"refs/codemcp/{chat_id}"
            ref_exists = False

            # Check if the reference exists
            ref_result = await run_command(
                ["git", "show-ref", "--verify", ref_name],
                cwd=git_cwd,
                check=False,
                capture_output=True,
                text=True,
            )
            ref_exists = ref_result.returncode == 0

            if ref_exists:
                # Using git plumbing commands instead of cherry-pick to avoid conflicts with local changes
                logging.info(f"Creating a new commit from reference {ref_name}")

                # Get the current HEAD commit hash
                head_hash = await get_head_commit_hash(git_cwd, short=False)

                # Get the tree from HEAD
                tree_result = await run_command(
                    ["git", "show", "-s", "--format=%T", "HEAD"],
                    cwd=git_cwd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                tree_hash = tree_result.stdout.strip()

                # Get the commit message from the reference
                ref_message_result = await run_command(
                    ["git", "log", "-1", "--pretty=%B", ref_name],
                    cwd=git_cwd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                ref_message = ref_message_result.stdout.strip()

                # Create a new commit with the same tree as HEAD but message from the reference
                # This effectively creates the commit without changing the working tree
                new_commit_result = await run_command(
                    [
                        "git",
                        "commit-tree",
                        tree_hash,
                        "-p",
                        head_hash,
                        "-m",
                        ref_message,
                    ],
                    cwd=git_cwd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                new_commit_hash = new_commit_result.stdout.strip()

                # Update HEAD to point to the new commit
                await run_command(
                    ["git", "update-ref", "HEAD", new_commit_hash],
                    cwd=git_cwd,
                    capture_output=True,
                    text=True,
                    check=True,
                )

                logging.info(
                    f"Successfully applied reference commit for chat ID {chat_id}"
                )
                # After applying, the HEAD commit should have the right chat_id
                head_chat_id = await get_head_commit_chat_id(git_cwd)

        should_amend = has_commits and head_chat_id == chat_id

        should_amend = has_commits and head_chat_id == chat_id

        # Prepare the commit message with metadata
        if custom_message:
            # Use the custom message and add chat_id if needed
            commit_message = custom_message

            # Make sure it has the chat_id metadata
            if chat_id:
                commit_message = append_metadata_to_message(
                    commit_message, {"codemcp-id": chat_id}
                )
        else:
            commit_message = f"wip: {description}"

        if should_amend:
            # Get the current commit hash before amending
            commit_hash = await get_head_commit_hash(git_cwd)

            # Get the current commit message
            current_commit_message = await get_head_commit_message(git_cwd)
            if not current_commit_message:
                current_commit_message = ""

            # Verify the commit has our codemcp-id
            if chat_id and "codemcp-id: " not in current_commit_message:
                logging.warning("Expected codemcp-id in current commit but not found")

            # Check if message already has base revision
            has_base_revision = "(Base revision)" in current_commit_message

            # Prepare the commit message for amending
            if not has_base_revision:
                # Add base revision marker for the first edit
                main_message = current_commit_message.replace(
                    "\ncodemcp-id: " + chat_id, ""
                )
                main_message += f"\n\n{commit_hash}  (Base revision)"
                commit_message = (
                    main_message + f"\nHEAD     {description}\n\ncodemcp-id: {chat_id}"
                )
            else:
                # Use the update function for subsequent edits
                commit_message = update_commit_message_with_description(
                    current_commit_message=current_commit_message,
                    description=description,
                    commit_hash=commit_hash,
                    chat_id=chat_id,
                )

            # Amend the previous commit
            commit_result = await run_command(
                ["git", "commit", "--amend", "-m", commit_message],
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=False,
            )
        else:
            # For new commits, ensure chat ID is added to the message
            if chat_id:
                # Add the codemcp-id to the message
                commit_message = append_metadata_to_message(
                    commit_message, {"codemcp-id": chat_id}
                )

            # Create a new commit
            commit_cmd = ["git", "commit", "-m", commit_message]
            if allow_empty:
                commit_cmd.append("--allow-empty")

            commit_result = await run_command(
                commit_cmd,
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=False,
            )

        if commit_result.returncode != 0:
            return False, f"Failed to commit changes: {commit_result.stderr}"

        # Get the new commit hash
        await get_head_commit_hash(git_cwd)

        verb = "amended" if should_amend else "committed"

        # If this was an amended commit, include the original hash in the message
        if should_amend and commit_hash:
            return (
                True,
                f"Changes {verb} successfully (previous commit was {commit_hash})",
            )
        else:
            return True, f"Changes {verb} successfully"
    except Exception as e:
        logging.warning(
            f"Exception suppressed when committing changes: {e!s}", exc_info=True
        )
        return False, f"Error committing changes: {e!s}"
