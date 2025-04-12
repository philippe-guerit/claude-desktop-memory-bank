"""
Tests for the update tool.
"""

import pytest
import asyncio
import json

from tests.conftest import parse_response


@pytest.mark.asyncio
async def test_update_tool(server):
    """Test the update tool."""
    # Create a bank first
    await server.call_tool_test(
        "activate",
        {
            "bank_type": "global",
            "bank_id": "test_update"
        }
    )
    
    # Call the update tool handler directly for testing
    test_content = "# Test Update\n\nThis is a test update to the memory bank."
    result = await server.call_tool_test(
        "update",
        {
            "bank_type": "global",
            "bank_id": "test_update",
            "target_file": "test.md",
            "operation": "replace",
            "content": test_content,
            "trigger_type": "user_request",
            "conversation_id": "test_conversation",
            "update_count": 1
        }
    )
    response = parse_response(result)
    
    # Check response structure
    assert "status" in response
    assert response["status"] == "success"
    assert "updated_file" in response
    assert response["updated_file"] == "test.md"
    assert "verification" in response
    
    # Verify that the file was updated correctly
    bank = server.storage.get_bank("global", "test_update")
    assert bank is not None
    
    loaded_content = bank.load_file("test.md")
    assert test_content in loaded_content
