#!/usr/bin/env python3

"""End-to-end tests for directory creation in WriteFile and EditFile."""

import os
import unittest

from codemcp.testing import MCPEndToEndTestCase


class DirectoryCreationTest(MCPEndToEndTestCase):
    """Test recursive directory creation in WriteFile and EditFile subtools."""

    async def test_write_file_nested_directories(self):
        """Test WriteFile can create nested directories."""
        # Create a path with multiple nested directories that don't exist
        nested_path = os.path.join(
            self.temp_dir.name, "test_nest", "level1", "level2", "level3"
        )
        test_file_path = os.path.join(nested_path, "test_file.txt")

        # Verify directory doesn't exist
        self.assertFalse(
            os.path.exists(nested_path), "Nested directory should not exist initially"
        )

        content = "Content in a deeply nested directory"

        async with self.create_client_session() as session:
            # Call the WriteFile tool
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "WriteFile",
                    "path": test_file_path,
                    "content": content,
                    "description": "Create file in nested directories",
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Check for success or permission error - base directories might not be in git
            if "Successfully wrote to" in result_text:
                # Test passed - the directories were created as expected
                self.assertTrue(
                    os.path.exists(nested_path), "Nested directories were not created"
                )

                # Verify the file was created with the correct content
                self.assertTrue(os.path.exists(test_file_path), "File was not created")
                with open(test_file_path) as f:
                    file_content = f.read()
                self.assertEqual(file_content, content)
            else:
                # Unexpected error
                self.fail(f"Unexpected error: {result_text}")

    async def test_edit_file_nested_directories(self):
        """Test EditFile can create nested directories when old_string is empty."""
        # Create a path with multiple nested directories that don't exist
        nested_path = os.path.join(self.temp_dir.name, "edit_nest", "level1", "level2")
        test_file_path = os.path.join(nested_path, "new_file.txt")

        # Verify directory doesn't exist
        self.assertFalse(
            os.path.exists(nested_path), "Nested directory should not exist initially"
        )

        content = "Content created in nested directories by EditFile"

        async with self.create_client_session() as session:
            # Call the EditFile tool with empty old_string
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "EditFile",
                    "path": test_file_path,
                    "old_string": "",
                    "new_string": content,
                    "description": "Create file in nested directories with EditFile",
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Check for success or permission error - base directories might not be in git
            if "Successfully created" in result_text:
                # Test passed - the directories were created as expected
                self.assertTrue(
                    os.path.exists(nested_path), "Nested directories were not created"
                )

                # Verify the file was created with the correct content
                self.assertTrue(os.path.exists(test_file_path), "File was not created")
                with open(test_file_path) as f:
                    file_content = f.read()
                self.assertEqual(file_content, content)
            else:
                # Unexpected error
                self.fail(f"Unexpected error: {result_text}")


if __name__ == "__main__":
    unittest.main()
