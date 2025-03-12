#!/usr/bin/env python3

"""Tests for the WriteFile subtool."""

import os
import subprocess
import unittest

from codemcp.testing import MCPEndToEndTestCase


class WriteFileTest(MCPEndToEndTestCase):
    """Test the WriteFile subtool."""

    async def test_write_file(self):
        """Test the WriteFile subtool, which writes to a file and automatically commits the changes."""
        test_file_path = os.path.join(self.temp_dir.name, "new_file.txt")
        content = "New content\nLine 2"

        # First add the file to git to make it tracked
        with open(test_file_path, "w") as f:
            f.write("")

        # Add it to git
        subprocess.run(
            ["git", "add", test_file_path],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        # Commit it
        subprocess.run(
            ["git", "commit", "-m", "Add empty file for WriteFile test"],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        async with self.create_client_session() as session:
            # Call the WriteFile tool
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "WriteFile",
                    "path": test_file_path,
                    "content": content,
                    "description": "Create new file",
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Verify the success message
            self.assertIn("Successfully wrote to", result_text)

            # Verify the file was created with the correct content
            with open(test_file_path) as f:
                file_content = f.read()
            self.assertEqual(file_content, content)

            # Verify git state (working tree should be clean after automatic commit)
            status = subprocess.check_output(
                ["git", "status"],
                cwd=self.temp_dir.name,
                env=self.env,
            ).decode()

            # Use expect test to verify git status - should show clean working tree
            self.assertExpectedInline(
                status,
                """On branch main
nothing to commit, working tree clean
""",
            )

    async def test_create_new_file_with_write_file(self):
        """Test creating a new file that doesn't exist yet with WriteFile."""
        # Path to a new file that doesn't exist yet, within the git repository
        new_file_path = os.path.join(self.temp_dir.name, "completely_new_file.txt")

        self.assertFalse(
            os.path.exists(new_file_path),
            "Test file should not exist initially",
        )

        async with self.create_client_session() as session:
            # Create a new file
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "WriteFile",
                    "path": new_file_path,
                    "content": "This is a brand new file",
                    "description": "Create a new file with WriteFile",
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Check that the operation succeeded
            self.assertIn("Successfully wrote to", result_text)

            # Verify the file was created
            self.assertTrue(
                os.path.exists(new_file_path),
                "File was not created even though operation reported success",
            )

            # Check content
            with open(new_file_path) as f:
                content = f.read()
            self.assertEqual(content, "This is a brand new file")

            # Verify the file was added to git
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

            # The new file should be tracked in git
            self.assertTrue(
                ls_files_output,
                "New file was created but not added to git",
            )

    async def test_write_to_untracked_file(self):
        """Test that writes to untracked files are rejected."""
        # Create an untracked file (not added to git)
        untracked_file_path = os.path.join(
            self.temp_dir.name,
            "untracked_for_write.txt",
        )
        with open(untracked_file_path, "w") as f:
            f.write("Initial content in untracked file")

        # Verify the file exists but is not tracked by git
        file_exists = os.path.exists(untracked_file_path)
        self.assertTrue(file_exists, "Test file should exist on filesystem")

        # Check that the file is untracked
        ls_files_output = (
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

        self.assertEqual(ls_files_output, "", "File should not be tracked by git")

        # Save original content and modification time for comparison
        with open(untracked_file_path) as f:
            original_content = f.read()
        original_mtime = os.path.getmtime(untracked_file_path)

        async with self.create_client_session() as session:
            # Try to write to the untracked file
            new_content = "This content should not be written to untracked file"
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "WriteFile",
                    "path": untracked_file_path,
                    "content": new_content,
                    "description": "Attempt to write to untracked file",
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)

            # Extract the text content for assertions
            result_text = self.extract_text_from_result(normalized_result)

            # Verify that the operation was rejected
            self.assertIn(
                "Error",
                result_text,
                "Write to untracked file should be rejected with an error",
            )
            self.assertIn(
                "not tracked by git",
                result_text,
                "Error message should indicate the file is not tracked by git",
            )

            # Verify the file content was not changed
            with open(untracked_file_path) as f:
                current_content = f.read()
            self.assertEqual(
                current_content,
                original_content,
                "File content should not have been changed",
            )

            # Verify file modification time was not changed
            current_mtime = os.path.getmtime(untracked_file_path)
            self.assertEqual(
                current_mtime,
                original_mtime,
                "File modification time should not have changed",
            )

    async def test_write_file_outside_tracked_paths(self):
        """Test that codemcp properly handles writing to paths outside tracked paths."""
        # Create a subdirectory but don't add it to git
        subdir_path = os.path.join(self.temp_dir.name, "untrackeddir")
        os.makedirs(subdir_path, exist_ok=True)

        new_file_path = os.path.join(subdir_path, "newfile.txt")

        async with self.create_client_session() as session:
            # Try to write a new file in the untracked directory
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "WriteFile",
                    "path": new_file_path,
                    "content": "New file in untracked directory",
                    "description": "Attempt to create file in untracked directory",
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Check the actual behavior
            if "Successfully wrote to" in result_text:
                # The operation succeeded - check if the directory and file are now tracked in git
                subprocess.check_output(
                    ["git", "status"],
                    cwd=self.temp_dir.name,
                    env=self.env,
                ).decode()

                # The file should exist
                self.assertTrue(
                    os.path.exists(new_file_path),
                    "File was not created even though operation reported success",
                )

                # SECURITY CHECK: If writing to untracked directories succeeds,
                # both the directory and file should be tracked in git
                ls_files_output = (
                    subprocess.check_output(
                        ["git", "ls-files", new_file_path],
                        cwd=self.temp_dir.name,
                        env=self.env,
                    )
                    .decode()
                    .strip()
                )

                # Check that the file is tracked - if this fails, we have a security issue
                self.assertTrue(
                    ls_files_output,
                    "SECURITY VULNERABILITY: File was created in untracked directory but not added to git",
                )


if __name__ == "__main__":
    unittest.main()
