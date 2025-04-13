"""
Integration tests for complete workflows.
"""

import pytest
import asyncio
import json

from tests.conftest import parse_response


@pytest.mark.asyncio
async def test_simplified_workflow(server):
    """Test a full workflow of activating and updating memory banks with simplified interface."""
    # Step 1: Activate a global bank
    result1 = await server.call_tool_test(
        "activate",
        {
            "conversation_type": "global"
        }
    )
    response1 = parse_response(result1)
    assert response1["status"] == "success"
    assert response1["bank_info"]["type"] == "global"
    
    # Step 2: Update the global bank
    result2 = await server.call_tool_test(
        "update",
        {
            "content": "## Workflow Test\nThis is a workflow test update.",
            "conversation_id": "workflow_test",
            "update_count": 1
        }
    )
    response2 = parse_response(result2)
    assert response2["status"] == "success"
    
    # Step 3: Activate a project bank (new conversation)
    result3 = await server.call_tool_test(
        "activate",
        {
            "conversation_type": "project",
            "project_name": "Workflow Test Project",
            "project_description": "A project for testing the workflow."
        }
    )
    response3 = parse_response(result3)
    assert response3["status"] == "success"
    assert response3["bank_info"]["type"] == "project"
    
    # Step 4: Update the project bank
    result4 = await server.call_tool_test(
        "update",
        {
            "content": "## Test Architecture\nWe decided to use a microservice architecture for this project.",
            "conversation_id": "workflow_test_project",
            "update_count": 1
        }
    )
    response4 = parse_response(result4)
    assert response4["status"] == "success"
    
    # Step 5: List all banks
    result5 = await server.call_tool_test(
        "list",
        {}
    )
    response5 = parse_response(result5)
    
    # Check that both banks are in the list
    global_banks = response5["global"]
    project_banks = response5["projects"]
    
    # We should have at least one global bank
    assert len(global_banks) > 0
    
    # We should have our project bank
    project_found = False
    for bank in project_banks:
        if "id" in bank and bank["id"].startswith("workflow_test_project"):
            project_found = True
            break
    assert project_found, "Project bank not found in list"
