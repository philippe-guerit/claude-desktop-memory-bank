"""
Tests for the activate tool.
"""

import pytest
import asyncio
import json

from tests.conftest import parse_response


@pytest.mark.asyncio
async def test_activate_global(server):
    """Test activating a global conversation."""
    # Call the activate tool handler directly for testing
    result = await server.call_tool_test(
        "activate",
        {
            "conversation_type": "global"
        }
    )
    response = parse_response(result)
    
    # Check response structure
    assert "status" in response
    assert response["status"] == "success"
    assert "bank_info" in response
    assert response["bank_info"]["type"] == "global"
    assert response["bank_info"]["id"] == "default"  # Global conversations use "default"
    assert "content" in response
    assert "custom_instructions" in response


@pytest.mark.asyncio
async def test_activate_project(server):
    """Test activating a project conversation."""
    # Call the activate tool handler directly for testing
    result = await server.call_tool_test(
        "activate",
        {
            "conversation_type": "project",
            "project_name": "Test Project",
            "project_description": "A test project for unit tests"
        }
    )
    response = parse_response(result)
    
    # Check response structure
    assert "status" in response
    assert response["status"] == "success"
    assert "bank_info" in response
    assert response["bank_info"]["type"] == "project"
    assert response["bank_info"]["id"] == "test_project"  # Normalized from "Test Project"
    assert "content" in response
    assert "custom_instructions" in response


@pytest.mark.asyncio
async def test_activate_code_project(server, tmp_path):
    """Test activating a code project with repository detection."""
    # This test would ideally create a temporary Git repository
    # Since that's complex for this test, we'll mock the behavior
    
    # Call the activate tool handler directly for testing
    # In a real test, current_path would point to a Git repository
    result = await server.call_tool_test(
        "activate",
        {
            "conversation_type": "project",
            "project_name": "Code Test",
            "current_path": "/tmp/fake_git_repo"  # This won't be a real repo
        }
    )
    response = parse_response(result)
    
    # Since this isn't a real Git repo, it should fall back to a standard project
    assert "bank_info" in response
    assert response["bank_info"]["type"] == "project"  # Falls back to project
    assert response["bank_info"]["id"] == "code_test"


@pytest.mark.asyncio
async def test_custom_instructions(server):
    """Test that custom instructions are returned from tools."""
    # Call the activate tool handler directly for testing
    result = await server.call_tool_test(
        "activate",
        {
            "conversation_type": "project",
            "project_name": "Instruction Test"
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
