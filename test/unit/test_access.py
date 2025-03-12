#!/usr/bin/env python3

import os
import shutil
import subprocess
import tempfile
import unittest

from codemcp.access import check_edit_permission, get_git_base_dir


class TestAccess(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for our tests
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Initialize a git repository in the test directory
        subprocess.run(
            ["git", "init", "."],
            cwd=self.test_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        # Configure git user for commits
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.test_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.test_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        # Create a test file
        self.test_file_path = os.path.join(self.test_dir, "test_file.txt")
        with open(self.test_file_path, "w") as f:
            f.write("Test content")

        # Add the file to git
        subprocess.run(
            ["git", "add", self.test_file_path],
            cwd=self.test_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        # Commit the file
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.test_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

    def tearDown(self):
        # Restore the original working directory and clean up the test directory
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def test_get_git_base_dir(self):
        """Test that get_git_base_dir correctly identifies the git repository root."""
        # Create a subdirectory
        sub_dir = os.path.join(self.test_dir, "subdir")
        os.makedirs(sub_dir, exist_ok=True)

        # Create a file in the subdirectory
        sub_file_path = os.path.join(sub_dir, "sub_file.txt")
        with open(sub_file_path, "w") as f:
            f.write("Subdirectory file content")

        # Test getting the git base directory from both files
        base_dir_from_root_file = get_git_base_dir(self.test_file_path)
        base_dir_from_sub_file = get_git_base_dir(sub_file_path)

        # Use os.path.realpath to resolve symlinks (needed on macOS where /var is a symlink to /private/var)
        # Both should return the test directory (git root)
        self.assertEqual(
            os.path.realpath(base_dir_from_root_file),
            os.path.realpath(self.test_dir),
        )
        self.assertEqual(
            os.path.realpath(base_dir_from_sub_file),
            os.path.realpath(self.test_dir),
        )

    def test_permission_check_without_config(self):
        """Test that permission is denied when no codemcp.toml exists."""
        is_permitted, _ = check_edit_permission(self.test_file_path)
        self.assertFalse(is_permitted)

    def test_permission_check_with_config(self):
        """Test that permission is granted when codemcp.toml exists."""
        # Create a codemcp.toml file in the git root
        config_path = os.path.join(self.test_dir, "codemcp.toml")
        with open(config_path, "w") as f:
            f.write("[project]\nname = 'test-project'\n")

        # Test permission check
        is_permitted, message = check_edit_permission(self.test_file_path)
        self.assertTrue(is_permitted)
        self.assertEqual(message, "Permission granted.")


if __name__ == "__main__":
    unittest.main()
