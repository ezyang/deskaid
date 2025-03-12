#!/usr/bin/env python3

import os
import subprocess
import sys
import unittest
from unittest import mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from codemcp.tools.grep import git_grep, grep_files


class TestGrepTool(unittest.TestCase):
    def setUp(self):
        # Set testing environment variable
        self.env_patcher = mock.patch.dict(os.environ, {"DESKAID_TESTING": "1"})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @mock.patch("codemcp.tools.grep.normalize_file_path", return_value="/test/path")
    @mock.patch("codemcp.tools.grep.is_git_repository", return_value=True)
    @mock.patch("codemcp.tools.grep.run_command")
    def test_git_grep_basic(self, mock_run, mock_is_git_repo, mock_normalize):
        # Setup mock
        mock_result = mock.MagicMock()
        mock_result.stdout = "file1.py\nfile2.py\nfile3.py"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Call the function
        result = git_grep("pattern", "/test/path")

        # Assert subprocess.run was called correctly
        mock_run.assert_called_once_with(
            cmd=["git", "grep", "-li", "pattern"],
            cwd="/test/path",
            capture_output=True,
            text=True,
            check=False,
        )

        # Assert correct files were returned
        expected = [
            "/test/path/file1.py",
            "/test/path/file2.py",
            "/test/path/file3.py",
        ]
        self.assertEqual(result, expected)

    @mock.patch("codemcp.tools.grep.normalize_file_path", return_value="/test/path")
    @mock.patch("codemcp.tools.grep.is_git_repository", return_value=True)
    @mock.patch("codemcp.tools.grep.run_command")
    def test_git_grep_with_include(self, mock_run, mock_is_git_repo, mock_normalize):
        # Setup mock
        mock_result = mock.MagicMock()
        mock_result.stdout = "file1.js\nfile2.js"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Call the function
        result = git_grep("pattern", "/test/path", "*.js")

        # Assert subprocess.run was called correctly
        mock_run.assert_called_once_with(
            cmd=["git", "grep", "-li", "pattern", "--", "*.js"],
            cwd="/test/path",
            capture_output=True,
            text=True,
            check=False,
        )

        # Assert correct files were returned
        expected = [
            "/test/path/file1.js",
            "/test/path/file2.js",
        ]
        self.assertEqual(result, expected)

    @mock.patch(
        "codemcp.tools.grep.normalize_file_path",
        return_value="/not/a/git/repo",
    )
    @mock.patch("codemcp.tools.grep.is_git_repository", return_value=False)
    @mock.patch("os.environ.get", return_value="1")  # Simulate test environment
    def test_git_grep_not_a_git_repo(
        self,
        mock_env_get,
        mock_is_git_repo,
        mock_normalize,
    ):
        # Should raise a ValueError if the path is not a git repository
        with self.assertRaises(ValueError) as context:
            git_grep("pattern", "/not/a/git/repo")

        # Verify the correct error message
        self.assertIn("not in a git repository", str(context.exception))

    @mock.patch("codemcp.tools.grep.normalize_file_path", return_value="/test/path")
    @mock.patch("codemcp.tools.grep.is_git_repository", return_value=True)
    @mock.patch("codemcp.tools.grep.run_command")
    def test_git_grep_no_matches(self, mock_run, mock_is_git_repo, mock_normalize):
        # Setup mock for no matches found
        mock_result = mock.MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 1  # git grep returns 1 when no matches are found
        mock_run.return_value = mock_result

        # Call the function
        result = git_grep("pattern", "/test/path")

        # Assert correct empty result
        self.assertEqual(result, [])

    @mock.patch("codemcp.tools.grep.normalize_file_path", return_value="/test/path")
    @mock.patch("codemcp.tools.grep.is_git_repository", return_value=True)
    @mock.patch("codemcp.tools.grep.run_command")
    def test_git_grep_error(self, mock_run, mock_is_git_repo, mock_normalize):
        # Setup mock for error
        mock_result = mock.MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "git grep error"
        mock_result.returncode = 2  # Some error code other than 0 or 1
        mock_run.return_value = mock_result

        # Should raise a subprocess.SubprocessError
        with self.assertRaises(subprocess.SubprocessError):
            git_grep("pattern", "/test/path")

    @mock.patch("codemcp.tools.grep.git_grep")
    @mock.patch("os.stat")
    @mock.patch("os.environ.get", return_value="1")  # Simulate test environment
    def test_grep_files_success(self, mock_env_get, mock_stat, mock_git_grep):
        # Setup mocks
        mock_git_grep.return_value = [
            "/test/path/file1.py",
            "/test/path/file2.py",
            "/test/path/file3.py",
        ]

        # Mock stat objects
        mock_stat1 = mock.MagicMock()
        mock_stat1.st_mtime = 1000
        mock_stat2 = mock.MagicMock()
        mock_stat2.st_mtime = 2000
        mock_stat3 = mock.MagicMock()
        mock_stat3.st_mtime = 3000

        mock_stat.side_effect = [mock_stat3, mock_stat2, mock_stat1]

        # Set test environment variables
        with mock.patch.dict(os.environ, {"NODE_ENV": "test", "DESKAID_TESTING": "1"}):
            result = grep_files("pattern", "/test/path")

        # Assertions
        self.assertEqual(result["numFiles"], 3)
        self.assertEqual(len(result["filenames"]), 3)
        self.assertIn("resultForAssistant", result)
        self.assertIn("Found 3 files", result["resultForAssistant"])

    @mock.patch("codemcp.tools.grep.git_grep")
    @mock.patch("os.environ.get", return_value="1")  # Simulate test environment
    def test_grep_files_empty_result(self, mock_env_get, mock_git_grep):
        # Setup mock for no matches
        mock_git_grep.return_value = []

        # Call the function
        result = grep_files("pattern", "/test/path")

        # Assertions
        self.assertEqual(result["numFiles"], 0)
        self.assertEqual(result["filenames"], [])
        self.assertIn("resultForAssistant", result)
        self.assertEqual(result["resultForAssistant"], "No files found")

    @mock.patch("codemcp.tools.grep.git_grep")
    @mock.patch("os.environ.get", return_value="1")  # Simulate test environment
    def test_grep_files_error(self, mock_env_get, mock_git_grep):
        # Setup mock to raise an exception
        mock_git_grep.side_effect = ValueError("Test error")

        # Call the function
        result = grep_files("pattern", "/test/path")

        # Assertions
        self.assertEqual(result["numFiles"], 0)
        self.assertEqual(result["filenames"], [])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Test error")
        self.assertIn("resultForAssistant", result)
        self.assertEqual(result["resultForAssistant"], "Error: Test error")


if __name__ == "__main__":
    unittest.main()
