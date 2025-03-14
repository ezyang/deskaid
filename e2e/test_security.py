#!/usr/bin/env python3

"""Tests for security aspects of codemcp."""

import os
import subprocess
import unittest

from codemcp.testing import MCPEndToEndTestCase


class SecurityTest(MCPEndToEndTestCase):
    """Test security aspects of codemcp."""

    async def test_path_traversal_attacks(self):
        """Test that codemcp properly prevents path traversal attacks."""
        # Create a file in the git repo that we'll try to access from outside
        test_file_path = os.path.join(self.temp_dir.name, "target.txt")
        with open(test_file_path, "w") as f:
            f.write("Target file content")

        # Add and commit the file
        subprocess.run(
            ["git", "add", "target.txt"],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        subprocess.run(
            ["git", "commit", "-m", "Add target file"],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        # Create a directory outside of the repo
        parent_dir = os.path.dirname(self.temp_dir.name)
        outside_file_path = os.path.join(parent_dir, "outside.txt")

        if os.path.exists(outside_file_path):
            os.unlink(outside_file_path)  # Clean up any existing file

        # Try various path traversal techniques
        traversal_paths = [
            outside_file_path,  # Direct absolute path outside the repo
            os.path.join(self.temp_dir.name, "..", "outside.txt"),  # Using .. to escape
            os.path.join(
                self.temp_dir.name,
                "subdir",
                "..",
                "..",
                "outside.txt",
            ),  # Multiple ..
        ]

        async with self.create_client_session() as session:
            # First initialize project to get chat_id
            init_result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                    "user_prompt": "Test initialization for path traversal test",
                    "subject_line": "test: initialize for path traversal test",
                    "reuse_head_chat_id": False,
                },
            )

            # Extract chat_id from the init result
            chat_id = self.extract_chat_id_from_text(init_result_text)

            for path in traversal_paths:
                path_desc = path.replace(
                    parent_dir,
                    "/parent_dir",
                )  # For better error messages

                # Try to write to a file outside the repository
                # This should result in an error
                result_text = await self.call_tool_assert_error(
                    session,
                    "codemcp",
                    {
                        "subtool": "WriteFile",
                        "path": path,
                        "content": "This should not be allowed to write outside the repo",
                        "description": f"Attempt path traversal attack ({path_desc})",
                        "chat_id": chat_id,
                    },
                )

                # Since we used call_tool_assert_error, we don't need to check if rejected
                rejected = True

                # Verify the file wasn't created outside the repo boundary
                file_created = os.path.exists(outside_file_path)

                # Either the operation should be rejected, or the file should not exist outside the repo
                if not rejected:
                    self.assertFalse(
                        file_created,
                        f"SECURITY VULNERABILITY: Path traversal attack succeeded with {path_desc}",
                    )

                # Clean up if the file was created
                if file_created:
                    os.unlink(outside_file_path)

    async def test_write_to_gitignored_file(self):
        """Test that codemcp properly handles writing to files that are in .gitignore."""
        # Create a .gitignore file
        gitignore_path = os.path.join(self.temp_dir.name, ".gitignore")
        with open(gitignore_path, "w") as f:
            f.write("ignored.txt\n")

        # Add and commit the .gitignore file
        subprocess.run(
            ["git", "add", ".gitignore"],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        subprocess.run(
            ["git", "commit", "-m", "Add .gitignore"],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        # Create the ignored file
        ignored_file_path = os.path.join(self.temp_dir.name, "ignored.txt")
        original_content = "This file is ignored by git"
        with open(ignored_file_path, "w") as f:
            f.write(original_content)

        # Verify the file is ignored
        status = subprocess.check_output(
            ["git", "status"],
            cwd=self.temp_dir.name,
            env=self.env,
        ).decode()
        self.assertNotIn("ignored.txt", status, "File should be ignored by git")

        async with self.create_client_session() as session:
            # First initialize project to get chat_id
            init_result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                    "user_prompt": "Test initialization for gitignored file test",
                    "subject_line": "test: initialize for gitignored file test",
                    "reuse_head_chat_id": False,
                },
            )

            # Extract chat_id from the init result
            chat_id = self.extract_chat_id_from_text(init_result_text)

            # Try to edit the ignored file
            # Using call_tool_assert_success because we expect success here
            result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "EditFile",
                    "path": ignored_file_path,
                    "old_string": "This file is ignored by git",
                    "new_string": "Modified ignored content",
                    "description": "Attempt to modify gitignored file",
                    "chat_id": chat_id,
                },
            )

            # Check if the operation was permitted and what happened
            if "Successfully edited" in result_text:
                # The file was modified, check if it was added to git despite being ignored
                with open(ignored_file_path) as f:
                    new_content = f.read()
                self.assertEqual(new_content, "Modified ignored content")

                # Check if git add succeeded (it should for explicitly named files even if ignored)
                ls_files_output = (
                    subprocess.check_output(
                        ["git", "ls-files", ignored_file_path],
                        cwd=self.temp_dir.name,
                        env=self.env,
                    )
                    .decode()
                    .strip()
                )

                # SECURITY CHECK: If editing ignored files succeeds, they should be explicitly added
                # to git to maintain the invariant that we can revert any change
                self.assertTrue(
                    ls_files_output,
                    "SECURITY VULNERABILITY: Ignored file was edited but not added to git",
                )


if __name__ == "__main__":
    unittest.main()
