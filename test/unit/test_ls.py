#!/usr/bin/env python3

import os
import re
import tempfile
import unittest
from unittest.mock import patch

from expecttest import TestCase

from codemcp.tools.ls import (
    MAX_FILES,
    TreeNode,
    create_file_tree,
    list_directory,
    ls_directory,
    print_tree,
    skip,
)


class TestLS(TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        # Create a test directory structure
        self.test_dir = os.path.join(self.temp_dir.name, "test_dir")
        os.makedirs(self.test_dir, exist_ok=True)

        # Create some files in the test directory
        self.file1_path = os.path.join(self.test_dir, "file1.txt")
        with open(self.file1_path, "w") as f:
            f.write("This is file 1\n")

        self.file2_path = os.path.join(self.test_dir, "file2.txt")
        with open(self.file2_path, "w") as f:
            f.write("This is file 2\n")

        # Create a subdirectory
        self.subdir_path = os.path.join(self.test_dir, "subdir")
        os.makedirs(self.subdir_path, exist_ok=True)

        # Create a file in the subdirectory
        self.subdir_file_path = os.path.join(self.subdir_path, "subdir_file.txt")
        with open(self.subdir_file_path, "w") as f:
            f.write("This is a file in the subdirectory\n")

        # Create a hidden file
        self.hidden_file_path = os.path.join(self.test_dir, ".hidden_file")
        with open(self.hidden_file_path, "w") as f:
            f.write("This is a hidden file\n")

        # Create a __pycache__ directory
        self.pycache_dir = os.path.join(self.test_dir, "__pycache__")
        os.makedirs(self.pycache_dir, exist_ok=True)
        self.pycache_file_path = os.path.join(self.pycache_dir, "cache_file.pyc")
        with open(self.pycache_file_path, "w") as f:
            f.write("This is a cache file\n")

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

        # Create patch for check_edit_permission
        self.check_edit_permission_patch = patch("codemcp.access.check_edit_permission")
        self.mock_check_edit_permission = self.check_edit_permission_patch.start()
        self.mock_check_edit_permission.return_value = (True, "Permission granted.")
        self.addCleanup(self.check_edit_permission_patch.stop)

        # Create a mock codemcp.toml file to satisfy permission check
        config_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(config_path, "w") as f:
            f.write("[codemcp]\nenabled = true\n")

    def normalize_result(self, result):
        """Normalize temporary directory paths in the result.

        This replaces the actual temporary directory path with a fixed placeholder
        to make tests more stable across different runs.
        """
        if self.temp_dir and self.temp_dir.name:
            # Replace the actual temp dir path with a fixed placeholder
            return re.sub(re.escape(self.temp_dir.name), "/tmp", result)
        return result

    def test_ls_directory_basic(self):
        """Test basic directory listing functionality"""
        # Mock the is_git_repository and check_edit_permission functions directly in the ls module
        with (
            patch("codemcp.tools.ls.is_git_repository", return_value=True),
            patch(
                "codemcp.tools.ls.check_edit_permission",
                return_value=(True, "Permission granted."),
            ),
        ):
            result = ls_directory(self.test_dir)
            normalized_result = self.normalize_result(result)

            # Check that the output contains the expected files and directories
            self.assertIn("file1.txt", normalized_result)
            self.assertIn("file2.txt", normalized_result)
            self.assertIn("subdir", normalized_result)

            # Check that hidden files and __pycache__ are excluded
            self.assertNotIn(".hidden_file", normalized_result)
            self.assertNotIn("__pycache__", normalized_result)

    def test_ls_directory_nonexistent(self):
        """Test listing a nonexistent directory"""
        with (
            patch("codemcp.tools.ls.is_git_repository", return_value=True),
            patch(
                "codemcp.tools.ls.check_edit_permission",
                return_value=(True, "Permission granted."),
            ),
        ):
            nonexistent_dir = os.path.join(self.temp_dir.name, "nonexistent")
            result = ls_directory(nonexistent_dir)
            self.assertIn("Error: Directory does not exist", result)

    def test_ls_directory_file(self):
        """Test listing a file instead of a directory"""
        with (
            patch("codemcp.tools.ls.is_git_repository", return_value=True),
            patch(
                "codemcp.tools.ls.check_edit_permission",
                return_value=(True, "Permission granted."),
            ),
        ):
            result = ls_directory(self.file1_path)
            self.assertIn("Error: Path is not a directory", result)

    def test_list_directory(self):
        """Test the list_directory function"""
        results = list_directory(self.test_dir)

        # Convert to set for easier comparison
        result_set = set(results)

        # Check that the expected files and directories are included
        self.assertIn("file1.txt", result_set)
        self.assertIn("file2.txt", result_set)
        # Check for "subdir/" with trailing slash as directories have it appended
        self.assertIn(f"subdir{os.sep}", result_set)
        # The subdir file is now included in the results from list_directory
        self.assertIn(os.path.join("subdir", "subdir_file.txt"), result_set)

        # Check that hidden files and __pycache__ are excluded
        self.assertNotIn(".hidden_file", result_set)
        self.assertNotIn("__pycache__", result_set)

    def test_skip_function(self):
        """Test the skip function for filtering paths"""
        # Test skipping hidden files
        self.assertTrue(skip(".hidden_file"))

        # Test skipping __pycache__
        self.assertTrue(skip("__pycache__"))
        self.assertTrue(skip("__pycache__/file.pyc"))

    def test_list_directory_max_files(self):
        """Test the max_files parameter"""
        # Create a directory with many files
        many_files_dir = os.path.join(self.temp_dir.name, "many_files")
        os.makedirs(many_files_dir, exist_ok=True)

        # Create MAX_FILES + 10 files
        for i in range(MAX_FILES + 10):
            file_path = os.path.join(many_files_dir, f"file{i}.txt")
            with open(file_path, "w") as f:
                f.write(f"This is file {i}\n")

        # List the directory with default MAX_FILES
        results = list_directory(many_files_dir)

        # Check that the number of files is limited to MAX_FILES+1
        # (since it will include one more than MAX_FILES due to the check in the loop)
        self.assertLessEqual(len(results), MAX_FILES + 1)

    def test_create_file_tree(self):
        """Test creating a file tree"""
        # Get the list of paths first
        paths = list_directory(self.test_dir)
        # Create the tree
        tree_nodes = create_file_tree(paths)

        # Check that we have the expected number of nodes at the root level
        # We expect to have at least file1.txt, file2.txt, and subdir
        self.assertGreaterEqual(len(tree_nodes), 3)

        # Find the subdir node
        subdir_node = None
        for node in tree_nodes:
            if node.name == "subdir":
                subdir_node = node
                break

        # If subdir node wasn't found in the root level, it might be because
        # we're checking the wrong node name - print all node names to debug
        if subdir_node is None:
            node_names = [node.name for node in tree_nodes]
            print(f"DEBUG: Available node names at root level: {node_names}")

        # Check that the subdir node exists and has the correct type
        self.assertIsNotNone(subdir_node)
        self.assertEqual(subdir_node.type, "directory")

        # Check that the subdir has a child (subdir_file.txt)
        has_subfile = False
        for child in subdir_node.children:
            if child.name == "subdir_file.txt":
                has_subfile = True
                self.assertEqual(child.type, "file")
                break

        self.assertTrue(has_subfile)

    def test_print_tree(self):
        """Test printing a file tree"""
        # Create a simple tree structure
        root_node = TreeNode("root", "root", "directory")
        file1 = TreeNode("file1.txt", "root/file1.txt", "file")
        file2 = TreeNode("file2.txt", "root/file2.txt", "file")
        subdir = TreeNode("subdir", "root/subdir", "directory")
        subfile = TreeNode("subfile.txt", "root/subdir/subfile.txt", "file")

        root_node.children = [file1, file2, subdir]
        subdir.children = [subfile]

        # Create a list of nodes for the root level
        root_list = [root_node]

        # Print the tree with a cwd parameter
        result = print_tree(root_list, cwd="/tmp/test")

        # Check that the output has the expected content
        self.assertIn("root", result)
        self.assertIn("file1.txt", result)
        self.assertIn("file2.txt", result)
        self.assertIn("subdir", result)
        self.assertIn("subfile.txt", result)
        # Also check that cwd was included
        self.assertIn("/tmp/test", result)


if __name__ == "__main__":
    unittest.main()
