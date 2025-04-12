"""
Tests for the activate tool.
"""

import pytest
import asyncio
import json

from tests.conftest import parse_response


@pytest.mark.asyncio
async def test_activate_tool(server):
    """Test the activate tool."""
    # Call the activate tool handler directly for testing
    result = await server.call_tool_test(
        "activate",
        {
            "bank_type": "global",
            "bank_id": "test_activate"
        }
    )
    response = parse_response(result)
    
    # Check response structure
    assert "status" in response
    assert response["status"] == "success"
    assert "bank_info" in response
    assert response["bank_info"]["type"] == "global"
    assert response["bank_info"]["id"] == "test_activate"
    assert "content" in response
    assert "custom_instructions" in response


@pytest.mark.asyncio
async def test_custom_instructions(server):
    """Test that custom instructions are returned from tools."""
    # Call the activate tool handler directly for testing
    result = await server.call_tool_test(
        "activate",
        {
            "bank_type": "code",
            "bank_id": "test_instructions"
        }
    )
    response = parse_response(result)
    
    # Check custom instructions structure
    assert "custom_instructions" in response
    instructions = response["custom_instructions"]
    
    assert "directives" in instructions
    assert len(instructions["directives"]) > 0
    
    assert "prompts" in instructions
    assert len(instructions["prompts"]) > 0
    
    # Check for code-specific directives
    found_code_directive = False
    for directive in instructions["directives"]:
        if "CODE_" in directive["name"]:
            found_code_directive = True
            break
    
    assert found_code_directive, "Code-specific directives not found"
