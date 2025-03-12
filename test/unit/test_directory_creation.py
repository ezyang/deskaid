#!/usr/bin/env python3

import os
import tempfile
import unittest
from unittest.mock import patch

from expecttest import TestCase

from codemcp.tools.edit_file import edit_file_content
from codemcp.tools.write_file import write_file_content


class TestDirectoryCreation(TestCase):
    def setUp(self):
        """Setup for directory creation tests"""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        # Setup mock patches
        self.setup_mocks()

    def setup_mocks(self):
        """Setup mocks for git functions to bypass repository checks"""
        # Create patch for git repository check
        self.is_git_repo_patch = patch("codemcp.git.is_git_repository")
        self.mock_is_git_repo = self.is_git_repo_patch.start()
        self.mock_is_git_repo.return_value = True
        self.addCleanup(self.is_git_repo_patch.stop)

        # Create patch for git base directory
        self.git_base_dir_patch = patch("codemcp.access.get_git_base_dir")
        self.mock_git_base_dir = self.git_base_dir_patch.start()
        self.mock_git_base_dir.return_value = self.temp_dir.name
        self.addCleanup(self.git_base_dir_patch.stop)

        # Create patch for commit operations
        self.commit_changes_patch_write = patch(
            "codemcp.tools.write_file.commit_changes"
        )
        self.mock_commit_changes_write = self.commit_changes_patch_write.start()
        self.mock_commit_changes_write.return_value = (True, "Mocked commit success")
        self.addCleanup(self.commit_changes_patch_write.stop)

        # Create patch for commit operations in edit_file
        self.commit_changes_patch_edit = patch("codemcp.tools.edit_file.commit_changes")
        self.mock_commit_changes_edit = self.commit_changes_patch_edit.start()
        self.mock_commit_changes_edit.return_value = (True, "Mocked commit success")
        self.addCleanup(self.commit_changes_patch_edit.stop)

        # Create patch for pending commit operations
        self.commit_pending_patch = patch(
            "codemcp.tools.file_utils.commit_pending_changes"
        )
        self.mock_commit_pending = self.commit_pending_patch.start()
        self.mock_commit_pending.return_value = (True, "No pending changes to commit")
        self.addCleanup(self.commit_pending_patch.stop)

        # Create a mock codemcp.toml file to satisfy permission check
        config_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(config_path, "w") as f:
            f.write("[codemcp]\nenabled = true\n")

    def test_write_file_creates_nested_directories(self):
        """Test that write_file_content creates nested directories"""
        # Path with multiple levels of nested directories that don't exist
        nested_dirs = os.path.join(
            self.temp_dir.name, "level1", "level2", "level3", "level4"
        )
        file_path = os.path.join(nested_dirs, "test_file.txt")
        content = "Test content in deeply nested directory"

        # Verify directories don't exist
        self.assertFalse(os.path.exists(nested_dirs))

        # Write the file
        result = write_file_content(file_path, content)

        # Check the result
        self.assertIn(f"Successfully wrote to {file_path}", result)

        # Verify directories were created
        self.assertTrue(os.path.exists(nested_dirs))

        # Verify file was created with correct content
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "r") as f:
            self.assertEqual(f.read(), content)

    def test_edit_file_creates_nested_directories(self):
        """Test that edit_file_content creates nested directories when old_string is empty"""
        # Path with multiple levels of nested directories that don't exist
        nested_dirs = os.path.join(self.temp_dir.name, "edit", "nested", "dirs")
        file_path = os.path.join(nested_dirs, "new_file.txt")
        content = "Test content for edit_file_content in nested directories"

        # Verify directories don't exist
        self.assertFalse(os.path.exists(nested_dirs))

        # Create the file with edit_file_content
        result = edit_file_content(file_path, "", content)

        # Check the result
        self.assertIn(f"Successfully created {file_path}", result)

        # Verify directories were created
        self.assertTrue(os.path.exists(nested_dirs))

        # Verify file was created with correct content
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "r") as f:
            self.assertEqual(f.read(), content)

    def test_edit_file_git_commit_on_new_file(self):
        """Test that edit_file_content commits changes when creating a new file"""
        # Path to a new file
        file_path = os.path.join(self.temp_dir.name, "commit_test", "new_file.txt")
        content = "Content that should be committed"

        # Create the file with edit_file_content
        edit_file_content(file_path, "", content, description="Test commit")

        # Verify that commit_changes was called
        self.mock_commit_changes_edit.assert_called_once()
        args, kwargs = self.mock_commit_changes_edit.call_args
        self.assertEqual(args[0], file_path)
        self.assertEqual(args[1], "Test commit")


if __name__ == "__main__":
    unittest.main()
