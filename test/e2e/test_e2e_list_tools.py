#!/usr/bin/env python3

"""Test for listing available tools."""

import unittest

from codemcp.testing import MCPEndToEndTestCase


class ListToolsTest(MCPEndToEndTestCase):
    """Test listing available tools."""

    async def test_list_tools(self):
        """Test listing available tools."""
        async with self.create_client_session() as session:
            result = await session.list_tools()
            # Verify the codemcp tool is available
            tool_names = [tool.name for tool in result.tools]
            self.assertIn("codemcp", tool_names)


if __name__ == "__main__":
    unittest.main()
