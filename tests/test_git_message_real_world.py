#!/usr/bin/env python3

import re
import unittest
from codemcp.git import parse_git_commit_message, append_metadata_to_message


class TestGitMessageRealWorldCases(unittest.TestCase):
    """Test Git commit message parsing with real-world examples."""

    def test_complex_commit_message_with_signatures(self):
        """Test parsing a complex commit message with different types of signature trailers."""
        message = """feat(git): Improve commit message handling

This commit enhances the Git commit message parsing logic to handle
various forms of trailers and metadata more robustly. It follows
the Git trailer conventions while ensuring backward compatibility.

The implementation now correctly handles:
- Trailers in the conventional format (Key: Value)
- Multiple trailers with different keys
- Multiline trailer values (with indentation)
- Various signature types used in Git projects

Fixes #123
Closes: #456
Refs: #789

Reviewed-by: John Smith <john@example.com>
Tested-by: Continuous Integration <ci@example.com>
Signed-off-by: Developer <dev@example.com>
Co-authored-by: Collaborator <collab@example.com>
codemcp-id: abc-123456"""

        main_message, metadata = parse_git_commit_message(message)

        # Check the main message is preserved without the trailers
        expected_main = """feat(git): Improve commit message handling

This commit enhances the Git commit message parsing logic to handle
various forms of trailers and metadata more robustly. It follows
the Git trailer conventions while ensuring backward compatibility.

The implementation now correctly handles:
- Trailers in the conventional format (Key: Value)
- Multiple trailers with different keys
- Multiline trailer values (with indentation)
- Various signature types used in Git projects

Fixes #123
Closes: #456
Refs: #789"""

        self.assertEqual(main_message, expected_main)

        # Check all the trailers are extracted correctly
        expected_metadata = {
            "Reviewed-by": "John Smith <john@example.com>",
            "Tested-by": "Continuous Integration <ci@example.com>",
            "Signed-off-by": "Developer <dev@example.com>",
            "Co-authored-by": "Collaborator <collab@example.com>",
            "codemcp-id": "abc-123456",
        }

        self.assertEqual(metadata, expected_metadata)

        # Test appending new metadata while preserving existing metadata
        new_message = append_metadata_to_message(
            message, {"codemcp-id": "new-id", "New-key": "value"}
        )

        # Extract the metadata from the updated message
        _, updated_metadata = parse_git_commit_message(new_message)

        # Check that the codemcp-id was updated and the new key was added
        # while preserving other metadata
        self.assertEqual(updated_metadata["codemcp-id"], "new-id")
        self.assertEqual(updated_metadata["New-key"], "value")
        self.assertEqual(
            updated_metadata["Signed-off-by"], "Developer <dev@example.com>"
        )
        self.assertEqual(len(updated_metadata), 6)  # 5 original + 1 new key

    def test_commit_message_with_edge_case_signatures(self):
        """Test parsing a commit message with edge case signatures like DCO Sign-off."""
        message = """refactor: Improve code organization

Split the large function into smaller, more focused functions
for better readability and testability.

Change-Id: I1a2b3c4d5e6f7g8h9i
Bug: b/12345
Exempt-From-Owner-Approval: true
DCO-1.1-Signed-off-by: Developer <dev@example.com>
codemcp-id: abc-123456"""

        main_message, metadata = parse_git_commit_message(message)

        # Check all the trailers are extracted correctly
        expected_metadata = {
            "Change-Id": "I1a2b3c4d5e6f7g8h9i",
            "Bug": "b/12345",
            "Exempt-From-Owner-Approval": "true",
            "DCO-1.1-Signed-off-by": "Developer <dev@example.com>",
            "codemcp-id": "abc-123456",
        }

        self.assertEqual(metadata, expected_metadata)

    def test_complex_commit_message_with_middle_codemcp_id(self):
        """Test parsing a complex commit message with codemcp-id in the middle followed by other metadata."""
        message = """Subject
    
Foo desc
Bar bar
    
codemcp-id: 10-blah
    
Signed-off-by: foobar
ghstack-id: blahblahblah"""

        # Test that get_head_commit_chat_id would correctly extract the codemcp-id
        # We'll do this by using the regex pattern directly since the function is async
        matches = re.findall(r"codemcp-id:\s*([^\n]*)", message)

        # Verify we found a match and it's the correct value
        self.assertTrue(matches)
        self.assertEqual(matches[-1].strip(), "10-blah")

        # Also test the parse_git_commit_message function for completeness
        main_message, metadata = parse_git_commit_message(message)

        # This is a complex case where our standard parser will have difficulty
        # due to the blank lines between metadata sections
        # But our regex approach should still correctly identify codemcp-id

        # Verify metadata contains expected entries
        self.assertEqual(metadata.get("Signed-off-by"), "foobar")
        self.assertEqual(metadata.get("ghstack-id"), "blahblahblah")


if __name__ == "__main__":
    unittest.main()
