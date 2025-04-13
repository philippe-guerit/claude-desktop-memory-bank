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
    # Create a global bank first
    await server.call_tool_test(
        "activate",
        {
            "conversation_type": "global"
        }
    )
    
    # Create a project bank
    await server.call_tool_test(
        "activate",
        {
            "conversation_type": "project",
            "project_name": "Test Project"
        }
    )
    
    # Call the list tool handler directly for testing
    result = await server.call_tool_test(
        "list",
        {}
    )
    response = parse_response(result)
    
    # Check response structure
    assert "global" in response
    assert "projects" in response
    
    # Check that we have global banks
    global_banks = response["global"]
    assert isinstance(global_banks, list)
    assert len(global_banks) > 0, "No global banks found"
    
    # Check that we have the project bank
    project_banks = response["projects"]
    assert isinstance(project_banks, list)
    
    test_project_found = False
    for bank in project_banks:
        if "id" in bank and "test_project" in bank["id"].lower():
            test_project_found = True
            break
    
    assert test_project_found, "Test project not found in list response"
