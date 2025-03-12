#!/usr/bin/env python3

import os
import tempfile
import unittest
from unittest.mock import patch

from expecttest import TestCase

from codemcp.tools.file_utils import write_text_content
from codemcp.tools.write_file import (
    detect_file_encoding,
    detect_line_endings,
    detect_repo_line_endings,
    write_file_content,
)


class TestWriteFile(TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        # Create a test file with known content
        self.test_file_path = os.path.join(self.temp_dir.name, "test_file.txt")
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write("This is a test file\nWith multiple lines\n")

        # Create a test file with CRLF line endings
        self.crlf_file_path = os.path.join(self.temp_dir.name, "crlf_file.txt")
        with open(self.crlf_file_path, "wb") as f:
            f.write(b"This is a file\r\nWith CRLF line endings\r\n")

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
        self.commit_changes_patch = patch("codemcp.tools.write_file.commit_changes")
        self.mock_commit_changes = self.commit_changes_patch.start()
        self.mock_commit_changes.return_value = (True, "Mocked commit success")
        self.addCleanup(self.commit_changes_patch.stop)

        # Create patch for pending commit operations - patch in file_utils now
        self.commit_pending_patch = patch(
            "codemcp.tools.file_utils.commit_pending_changes",
        )
        self.mock_commit_pending = self.commit_pending_patch.start()
        self.mock_commit_pending.return_value = (True, "No pending changes to commit")
        self.addCleanup(self.commit_pending_patch.stop)

        # Create a mock codemcp.toml file to satisfy permission check
        config_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(config_path, "w") as f:
            f.write("[codemcp]\nenabled = true\n")

    def test_detect_file_encoding_utf8(self):
        """Test detecting UTF-8 encoding"""
        encoding = detect_file_encoding(self.test_file_path)
        self.assertEqual(encoding, "utf-8")

    def test_detect_file_encoding_fallback(self):
        """Test fallback encoding detection"""
        # Create a file with non-UTF-8 content
        non_utf8_path = os.path.join(self.temp_dir.name, "non_utf8.txt")
        with open(non_utf8_path, "wb") as f:
            f.write(b"\x80\x81\x82")  # Invalid UTF-8 bytes

        encoding = detect_file_encoding(non_utf8_path)
        self.assertEqual(encoding, "latin-1")

    def test_detect_line_endings_lf(self):
        """Test detecting LF line endings"""
        line_endings = detect_line_endings(self.test_file_path)
        self.assertEqual(line_endings, "\n")

    def test_detect_line_endings_crlf(self):
        """Test detecting CRLF line endings"""
        line_endings = detect_line_endings(self.crlf_file_path)
        self.assertEqual(line_endings, "\r\n")

    def test_detect_repo_line_endings(self):
        """Test detecting repository line endings"""
        line_endings = detect_repo_line_endings(self.temp_dir.name)
        self.assertEqual(line_endings, os.linesep)

    def test_write_text_content_basic(self):
        """Test basic text writing functionality"""
        test_path = os.path.join(self.temp_dir.name, "write_test.txt")
        content = "Test content\nMultiple lines"

        write_text_content(test_path, content)

        with open(test_path, encoding="utf-8") as f:
            written_content = f.read()

        self.assertEqual(written_content, content)

    def test_write_text_content_with_line_endings(self):
        """Test writing with specific line endings"""
        test_path = os.path.join(self.temp_dir.name, "line_endings_test.txt")
        content = "Line 1\nLine 2\nLine 3"

        write_text_content(test_path, content, line_endings="\r\n")

        # Read in binary mode to check the actual line endings
        with open(test_path, "rb") as f:
            written_content = f.read()

        # Should contain CRLF (b'\r\n') and not lone LF (b'\n\n')
        self.assertIn(b"\r\n", written_content)
        self.assertNotIn(b"\n\n", written_content)

        # Confirm the content has the correct number of newlines
        text_lines = written_content.count(b"\r\n")
        self.assertEqual(text_lines, 2, "Should have 2 CRLF line breaks")

    def test_write_file_content_success(self):
        """Test successful file writing"""
        abs_path = os.path.abspath(os.path.join(self.temp_dir.name, "success_test.txt"))
        content = "Test content for successful write"

        result = write_file_content(abs_path, content)

        self.assertIn(f"Successfully wrote to {abs_path}", result)
        self.assertTrue(os.path.exists(abs_path))

        with open(abs_path) as f:
            written_content = f.read()

        self.assertEqual(written_content, content)

    def test_write_file_content_relative_path(self):
        """Test error when using relative path"""
        rel_path = "relative/path/file.txt"
        content = "This should fail"

        result = write_file_content(rel_path, content)

        self.assertIn("Error: File path must be absolute", result)
        self.assertIn(rel_path, result)

    def test_write_file_content_creates_directory(self):
        """Test that directories are created if they don't exist"""
        new_dir_path = os.path.join(self.temp_dir.name, "new", "nested", "dir")
        abs_path = os.path.abspath(os.path.join(new_dir_path, "new_file.txt"))
        content = "Content in a new directory"

        self.assertFalse(os.path.exists(new_dir_path))

        result = write_file_content(abs_path, content)

        self.assertIn(f"Successfully wrote to {abs_path}", result)
        self.assertTrue(os.path.exists(new_dir_path))
        self.assertTrue(os.path.exists(abs_path))

    def test_write_file_content_existing_file(self):
        """Test writing to an existing file"""
        # First write
        abs_path = os.path.abspath(os.path.join(self.temp_dir.name, "existing.txt"))
        initial_content = "Initial content"
        write_file_content(abs_path, initial_content)

        # Second write
        new_content = "Updated content"
        result = write_file_content(abs_path, new_content)

        self.assertIn(f"Successfully wrote to {abs_path}", result)

        with open(abs_path) as f:
            written_content = f.read()

        self.assertEqual(written_content, new_content)

    @patch("codemcp.tools.write_file.write_text_content")
    def test_write_file_content_exception(self, mock_write):
        """Test handling of exceptions during writing"""
        mock_write.side_effect = Exception("Test exception")

        abs_path = os.path.abspath(
            os.path.join(self.temp_dir.name, "exception_test.txt"),
        )
        content = "This should raise an exception"

        result = write_file_content(abs_path, content)

        self.assertIn("Error writing file", result)
        self.assertIn("Test exception", result)

    def test_write_file_content_untracked_file(self):
        """Test that writing to an untracked file is rejected"""
        # Override the commit_pending_changes mock to simulate an untracked file
        with patch("codemcp.tools.file_utils.commit_pending_changes") as mock_pending:
            # Simulate the subprocess.run result for an untracked file with the updated error message
            mock_pending.return_value = (
                False,
                "File is not tracked by git. Please add the file to git tracking first using 'git add <file>'",
            )

            # Create the file first so it exists but is untracked
            abs_path = os.path.abspath(
                os.path.join(self.temp_dir.name, "untracked_file.txt"),
            )
            with open(abs_path, "w") as f:
                f.write("Initial content")

            content = "Content that should not be written"
            result = write_file_content(abs_path, content)

            # Verify that the write was rejected
            self.assertIn("Error: File is not tracked by git", result)
            self.assertIn("Please add the file to git tracking", result)

            # Verify that the file content was not changed
            with open(abs_path) as f:
                written_content = f.read()
            self.assertEqual(written_content, "Initial content")

    def test_write_file_content_new_file(self):
        """Test creating a new file that doesn't exist yet"""
        abs_path = os.path.abspath(os.path.join(self.temp_dir.name, "new_file.txt"))
        content = "Content for a new file"

        # Make sure the file doesn't exist first
        if os.path.exists(abs_path):
            os.remove(abs_path)

        result = write_file_content(abs_path, content)

        # Verify that the write was successful
        self.assertIn(f"Successfully wrote to {abs_path}", result)

        # Verify that the file was created with correct content
        self.assertTrue(os.path.exists(abs_path))
        with open(abs_path) as f:
            written_content = f.read()
        self.assertEqual(written_content, content)


if __name__ == "__main__":
    unittest.main()
