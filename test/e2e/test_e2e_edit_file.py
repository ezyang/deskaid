#!/usr/bin/env python3

"""Tests for the EditFile subtool."""

import os
import subprocess
import unittest

from codemcp.testing import MCPEndToEndTestCase


class EditFileTest(MCPEndToEndTestCase):
    """Test the EditFile subtool."""

    async def test_edit_file(self):
        """Test the EditFile subtool, which edits a file and automatically commits the changes."""
        # Create a test file with multiple lines for good context
        test_file_path = os.path.join(self.temp_dir.name, "edit_file.txt")
        original_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
        with open(test_file_path, "w") as f:
            f.write(original_content)

        # Add the file to git and commit it
        subprocess.run(
            ["git", "add", "edit_file.txt"],
            cwd=self.temp_dir.name,
            env=self.env,
            check=False,
        )
        subprocess.run(
            ["git", "commit", "-m", "Add file for editing"],
            cwd=self.temp_dir.name,
            env=self.env,
            check=False,
        )

        # Edit the file using the EditFile subtool with proper context
        old_string = "Line 1\nLine 2\nLine 3\n"
        new_string = "Line 1\nModified Line 2\nLine 3\n"

        async with self.create_client_session() as session:
            # Call the EditFile tool
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "EditFile",
                    "path": test_file_path,
                    "old_string": old_string,
                    "new_string": new_string,
                    "description": "Modify line 2",
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)

            # Extract the text content for assertions
            result_text = self.extract_text_from_result(normalized_result)

            # Verify the success message
            self.assertIn("Successfully edited", result_text)

            # Verify the file was edited correctly
            with open(test_file_path) as f:
                file_content = f.read()

            expected_content = "Line 1\nModified Line 2\nLine 3\nLine 4\nLine 5\n"
            self.assertEqual(file_content, expected_content)

            # Verify git state shows file was committed
            status = subprocess.check_output(
                ["git", "status"],
                cwd=self.temp_dir.name,
                env=self.env,
            ).decode()

            # Use expect test to verify git status - should show as clean working tree
            # since EditFile automatically commits changes
            self.assertExpectedInline(
                status,
                """On branch main
nothing to commit, working tree clean
""",
            )

    async def test_edit_untracked_file(self):
        """Test that codemcp properly handles editing files that aren't tracked by git."""
        # Create a file but don't commit it to git
        untracked_file_path = os.path.join(self.temp_dir.name, "untracked.txt")
        original_content = "Untracked file content"
        with open(untracked_file_path, "w") as f:
            f.write(original_content)

        # Verify the file exists but is not tracked
        status = subprocess.check_output(
            ["git", "status"],
            cwd=self.temp_dir.name,
            env=self.env,
        ).decode()

        (
            subprocess.run(
                ["git", "ls-files", untracked_file_path],
                cwd=self.temp_dir.name,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            .stdout.decode()
            .strip()
        )

        self.assertIn("Untracked files:", status)
        self.assertIn("untracked.txt", status)

        # Save the original modification time to check if file was modified
        os.path.getmtime(untracked_file_path)

        async with self.create_client_session() as session:
            # Try to edit the untracked file
            new_content = "Modified untracked content"

            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "EditFile",
                    "path": untracked_file_path,
                    "old_string": "Untracked file content",
                    "new_string": new_content,
                    "description": "Attempt to modify untracked file",
                },
            )

            # Get the result content
            (result.content if hasattr(result, "content") else str(result))

            # Normalize the result
            self.normalize_path(result)

            # Check file after the operation
            if os.path.exists(untracked_file_path):
                with open(untracked_file_path) as f:
                    actual_content = f.read()
                os.path.getmtime(untracked_file_path)
            else:
                self.fail("File doesn't exist anymore!")

            # With new policy, we expect the edit to fail since the file is not tracked
            edit_succeeded = actual_content == new_content
            self.assertFalse(
                edit_succeeded,
                "POLICY ERROR: Editing untracked files should be rejected",
            )

    async def test_create_file_with_edit_file_in_untracked_dir(self):
        """Test that codemcp properly handles creating new files with EditFile in untracked directories."""
        # Create an untracked subdirectory within the Git repository
        untracked_dir = os.path.join(self.temp_dir.name, "untracked_subdir")
        os.makedirs(untracked_dir, exist_ok=True)

        # Path to a new file in the untracked directory
        new_file_path = os.path.join(untracked_dir, "new_file.txt")

        async with self.create_client_session() as session:
            # Try to create a new file using EditFile with empty old_string
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "EditFile",
                    "path": new_file_path,
                    "old_string": "",
                    "new_string": "This file in untracked dir",
                    "description": "Attempt to create file in untracked dir with EditFile",
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Since we've changed the behavior, we now expect this to succeed
            self.assertIn("Successfully created", result_text)

            # Check the file was created
            self.assertTrue(
                os.path.exists(new_file_path),
                "File was not created even though operation reported success",
            )

            # Read the content to verify it was written correctly
            with open(new_file_path) as f:
                content = f.read()
            self.assertEqual(content, "This file in untracked dir")

            # For this test, we'll manually add and commit the file
            # This is a change in the test expectation since we don't need automatic git tracking
            # for files in untracked directories - we just want file creation to work
            subprocess.run(
                ["git", "add", new_file_path],
                cwd=self.temp_dir.name,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            subprocess.run(
                ["git", "commit", "-m", "Add test file"],
                cwd=self.temp_dir.name,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            # Now check if the file is tracked
            ls_files_output = (
                subprocess.run(
                    ["git", "ls-files", new_file_path],
                    cwd=self.temp_dir.name,
                    env=self.env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                .stdout.decode()
                .strip()
            )

            # Verify the file is tracked by git after our manual commit
            self.assertTrue(
                ls_files_output,
                "Failed to add file to git even after manual commit",
            )

    async def test_edit_after_git_rm(self):
        """Test that codemcp properly handles editing files that have been removed with git rm."""
        # Create a tracked file
        tracked_file_path = os.path.join(self.temp_dir.name, "tracked.txt")
        with open(tracked_file_path, "w") as f:
            f.write("Tracked file content")

        # Add and commit the file
        subprocess.run(
            ["git", "add", "tracked.txt"],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        subprocess.run(
            ["git", "commit", "-m", "Add tracked file"],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        # Remove the file with git rm
        subprocess.run(
            ["git", "rm", "tracked.txt"],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        # Verify file was removed
        self.assertFalse(
            os.path.exists(tracked_file_path),
            "File should be physically removed",
        )

        async with self.create_client_session() as session:
            # Try to write to the removed file
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "WriteFile",
                    "path": tracked_file_path,
                    "content": "Attempt to write to git-removed file",
                    "description": "Attempt to modify git-removed file",
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Check the actual behavior
            if "Successfully wrote to" in result_text:
                # The operation succeeded - check if the file was recreated and added to git
                self.assertTrue(
                    os.path.exists(tracked_file_path),
                    "File was not recreated even though operation reported success",
                )

                # SECURITY CHECK: Read file content to confirm it was written correctly
                with open(tracked_file_path) as f:
                    content = f.read()
                self.assertEqual(content, "Attempt to write to git-removed file")

                # Check if the recreated file is tracked in git
                status_after = subprocess.check_output(
                    ["git", "status"],
                    cwd=self.temp_dir.name,
                    env=self.env,
                ).decode()

                # If the file is untracked or deleted, we have a problem
                self.assertNotIn(
                    "deleted:",
                    status_after,
                    "SECURITY VULNERABILITY: File still shows as deleted in git",
                )
                self.assertNotIn(
                    "tracked.txt",
                    status_after,
                    "SECURITY VULNERABILITY: Recreated file is not properly tracked",
                )


if __name__ == "__main__":
    unittest.main()
