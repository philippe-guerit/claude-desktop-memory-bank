"""
Tests for the list tool.
"""

import pytest
import asyncio
import json

from tests.conftest import parse_response


@pytest.mark.asyncio
async def test_list_tool(server):
    """Test the list tool."""
    # Create a bank first
    await asyncio.gather(
        server.server.call_tool(
            "activate",
            {
                "bank_type": "global",
                "bank_id": "test_list"
            }
        )
    )
    
    # Call the list tool handler directly for testing
    result = await asyncio.gather(
        server.server.call_tool(
            "list",
            {}
        )
    )
    response = parse_response(result[0])
    
    # Check response structure
    assert "global" in response
    
    # Find our test bank
    found = False
    for bank in response["global"]:
        if bank["id"] == "test_list":
            found = True
            break
    
    assert found, "Created bank not found in list response"
