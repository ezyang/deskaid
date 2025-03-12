#!/usr/bin/env python3

"""Tests for the RunCommand with lint."""

import os
import subprocess
import unittest

from codemcp.testing import MCPEndToEndTestCase


class RunCommandLintTest(MCPEndToEndTestCase):
    """Test the RunCommand with lint subtool."""

    async def test_lint_with_run_subtool(self):
        """Test that RunCommand with lint commits changes made by linting."""
        # Create a file that needs linting
        unlinted_file_path = os.path.join(self.temp_dir.name, "unlinted.py")
        unlinted_content = """import math
import os
import sys
from typing import List, Dict, Any

def unused_param(x, y):
    # Unused parameter 'y' that linter would remove
    return x * 2

def main():
    # Unused import
    # Variables defined but not used
    unused_var = 42
    return True
"""

        with open(unlinted_file_path, "w") as f:
            f.write(unlinted_content)

        # Add it to git
        subprocess.run(
            ["git", "add", unlinted_file_path],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        # Commit it
        subprocess.run(
            ["git", "commit", "-m", "Add unlinted file"],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        # Create a simple lint script that simulates ruff linting
        lint_script_path = os.path.join(self.temp_dir.name, "run_lint.sh")
        with open(lint_script_path, "w") as f:
            f.write("""#!/bin/bash
# Simple mock linter that fixes linting issues in the unlinted.py file
if [ -f unlinted.py ]; then
    # Replace with properly linted version (removed unused imports and variables)
    cat > unlinted.py << 'EOF'
import math
from typing import List, Dict, Any

def unused_param(x):
    # Linter removed unused parameter 'y'
    return x * 2

def main():
    return True
EOF
    echo "Linted unlinted.py"
fi
""")

        # Make it executable
        os.chmod(lint_script_path, 0o755)

        # Create a codemcp.toml file with lint subtool
        codemcp_toml_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(codemcp_toml_path, "w") as f:
            f.write("""[project]
name = "test-project"

[commands]
lint = ["./run_lint.sh"]
""")

        # Record the current commit hash before linting
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
            # Call the RunCommand tool with lint command
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "RunCommand",
                    "path": self.temp_dir.name,
                    "command": "lint",
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Verify the success message
            self.assertIn("Code lint successful", result_text)

            # Verify the file was linted correctly
            with open(unlinted_file_path) as f:
                file_content = f.read()

            expected_content = """import math
from typing import List, Dict, Any

def unused_param(x):
    # Linter removed unused parameter 'y'
    return x * 2

def main():
    return True
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

            # Verify the commit message indicates it was a linting change
            commit_msg = (
                subprocess.check_output(
                    ["git", "log", "-1", "--pretty=%B"],
                    cwd=self.temp_dir.name,
                    env=self.env,
                )
                .decode()
                .strip()
            )

            self.assertEqual(commit_msg, "Auto-commit lint changes")


if __name__ == "__main__":
    unittest.main()
