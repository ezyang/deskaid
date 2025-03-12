#!/usr/bin/env python3

"""Tests for the RunCommand with format."""

import os
import subprocess
import unittest

from codemcp.testing import MCPEndToEndTestCase


class RunCommandFormatTest(MCPEndToEndTestCase):
    """Test the RunCommand with format subtool."""

    async def test_format_with_run_subtool(self):
        """Test that RunCommand with format commits changes made by formatting."""
        # Create a file that is not properly formatted (needs formatting)
        # We'll use Python's ruff formatter conventions
        unformatted_file_path = os.path.join(self.temp_dir.name, "unformatted.py")
        unformatted_content = """def   badly_formatted_function ( arg1,arg2 ):
    x=1+2
    y= [1,2,
3, 4]
    return   x+y
"""

        with open(unformatted_file_path, "w") as f:
            f.write(unformatted_content)

        # Add it to git
        subprocess.run(
            ["git", "add", unformatted_file_path],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        # Commit it
        subprocess.run(
            ["git", "commit", "-m", "Add unformatted file"],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        # Create a simple format script that simulates ruff formatting
        format_script_path = os.path.join(self.temp_dir.name, "run_format.sh")
        with open(format_script_path, "w") as f:
            f.write("""#!/bin/bash
# Simple mock formatter that just fixes the format of the unformatted.py file
if [ -f unformatted.py ]; then
    # Replace with properly formatted version
    cat > unformatted.py << 'EOF'
def badly_formatted_function(arg1, arg2):
    x = 1 + 2
    y = [1, 2, 3, 4]
    return x + y
EOF
    echo "Formatted unformatted.py"
fi
""")

        # Make it executable
        os.chmod(format_script_path, 0o755)

        # Create a codemcp.toml file with format subtool
        codemcp_toml_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(codemcp_toml_path, "w") as f:
            f.write("""[project]
name = "test-project"

[commands]
format = ["./run_format.sh"]
""")

        # Record the current commit hash before formatting
        commit_before = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=self.temp_dir.name,
                env=self.env,
            )
            .decode()
            .strip()
        )

        async with self.create_client_session() as session:
            # Call the RunCommand tool with format command
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "RunCommand",
                    "path": self.temp_dir.name,
                    "command": "format",
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Verify the success message
            self.assertIn("Code format successful", result_text)

            # Verify the file was formatted correctly
            with open(unformatted_file_path) as f:
                file_content = f.read()

            expected_content = """def badly_formatted_function(arg1, arg2):
    x = 1 + 2
    y = [1, 2, 3, 4]
    return x + y
"""
            self.assertEqual(file_content, expected_content)

            # Verify git state shows clean working tree after commit
            status = subprocess.check_output(
                ["git", "status"],
                cwd=self.temp_dir.name,
                env=self.env,
            ).decode()

            # Verify that the working tree is clean (changes were committed)
            self.assertExpectedInline(
                status,
                """On branch main
nothing to commit, working tree clean
""",
            )

            # Verify that a new commit was created
            commit_after = (
                subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.temp_dir.name,
                    env=self.env,
                )
                .decode()
                .strip()
            )

            # The commit hash should be different
            self.assertNotEqual(commit_before, commit_after)

            # Verify the commit message indicates it was a formatting change
            commit_msg = (
                subprocess.check_output(
                    ["git", "log", "-1", "--pretty=%B"],
                    cwd=self.temp_dir.name,
                    env=self.env,
                )
                .decode()
                .strip()
            )

            self.assertEqual(commit_msg, "Auto-commit format changes")


if __name__ == "__main__":
    unittest.main()
