#!/usr/bin/env python3

"""Tests for the RunCommand with test."""

import os
import subprocess
import sys
import unittest

from codemcp.testing import MCPEndToEndTestCase


class RunCommandTestTest(MCPEndToEndTestCase):
    """Test the RunCommand with test subtool."""

    async def test_run_tests_with_run_subtool(self):
        """Test the RunCommand with test command."""
        # Create a test directory for testing
        test_dir = os.path.join(self.temp_dir.name, "test_directory")
        os.makedirs(test_dir, exist_ok=True)

        # Create a test.py file with a simple test
        test_file_path = os.path.join(test_dir, "test_simple.py")
        with open(test_file_path, "w") as f:
            f.write("""
import unittest

class SimpleTestCase(unittest.TestCase):
    def test_success(self):
        self.assertEqual(1 + 1, 2)

    def test_another_success(self):
        self.assertTrue(True)
""")

        # Create a second test file with another test
        test_file_path2 = os.path.join(test_dir, "test_another.py")
        with open(test_file_path2, "w") as f:
            f.write("""
import unittest

class AnotherTestCase(unittest.TestCase):
    def test_success(self):
        self.assertEqual(2 + 2, 4)
""")

        # Create a run_test.sh script to mimic the real one
        # Get the current Python executable path
        current_python = os.path.abspath(sys.executable)

        # Create run_test.sh script using the current Python executable
        runner_script_path = os.path.join(self.temp_dir.name, "run_test.sh")
        with open(runner_script_path, "w") as f:
            f.write(f"""#!/bin/bash
set -e
cd "$(dirname "$0")"
{current_python} -m pytest $@
""")
        os.chmod(runner_script_path, 0o755)  # Make it executable

        # Update codemcp.toml to include the test subtool
        config_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(config_path, "w") as f:
            f.write("""
[project]
name = "test-project"

[commands]
test = ["./run_test.sh"]
""")

        # Add files to git
        subprocess.run(
            ["git", "add", "."],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        subprocess.run(
            ["git", "commit", "-m", "Add test files"],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        async with self.create_client_session() as session:
            # Call the RunCommand tool with test command
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "RunCommand",
                    "path": self.temp_dir.name,
                    "command": "test",
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Verify the success message
            self.assertIn("Code test successful", result_text)

            # Call the RunCommand tool with test command and arguments
            selector_result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "RunCommand",
                    "path": self.temp_dir.name,
                    "command": "test",
                    "arguments": ["test_directory/test_another.py"],
                },
            )

            # Normalize the result
            normalized_selector_result = self.normalize_path(selector_result)
            selector_result_text = self.extract_text_from_result(
                normalized_selector_result
            )

            # Verify the success message
            self.assertIn("Code test successful", selector_result_text)
            # Verify that the selector was used
            self.assertIn("test_another.py", selector_result_text)
            self.assertNotIn("test_simple.py", selector_result_text)


if __name__ == "__main__":
    unittest.main()
