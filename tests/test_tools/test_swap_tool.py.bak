"""
Tests for the swap tool.
"""

import pytest
import asyncio
import json

from tests.conftest import parse_response


@pytest.mark.asyncio
async def test_swap_tool(server):
    """Test the swap tool."""
    # Create two banks first
    await server.call_tool_test(
        "activate",
        {
            "bank_type": "global",
            "bank_id": "test_swap_1"
        }
    )
    
    await server.call_tool_test(
        "activate",
        {
            "bank_type": "project",
            "bank_id": "test_swap_2"
        }
    )
    
    # Call the swap tool handler directly for testing
    result = await server.call_tool_test(
        "swap",
        {
            "bank_type": "project",
            "bank_id": "test_swap_2",
            "temporary": True
        }
    )
    response = parse_response(result)
    
    # Check response structure
    assert "status" in response
    assert response["status"] == "success"
    assert "bank_info" in response
    assert response["bank_info"]["type"] == "project"
    assert response["bank_info"]["id"] == "test_swap_2"
    assert "content" in response
    assert "custom_instructions" in response
    
    # Check that the temporary flag is set
    assert "bank_info" in response
    assert "temporary" in response["bank_info"]
    assert response["bank_info"]["temporary"] is True
