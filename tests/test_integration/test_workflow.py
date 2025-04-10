"""
Integration tests for complete workflows.
"""

import pytest
import asyncio
import json

from tests.conftest import parse_response


@pytest.mark.asyncio
async def test_full_workflow(server):
    """Test a full workflow of activating, updating, and swapping banks."""
    # Step 1: Activate a global bank
    result1 = await asyncio.gather(
        server.server.call_tool(
            "activate",
            {
                "bank_type": "global",
                "bank_id": "workflow_test"
            }
        )
    )
    response1 = parse_response(result1[0])
    assert response1["status"] == "success"
    
    # Step 2: Update the global bank
    result2 = await asyncio.gather(
        server.server.call_tool(
            "update",
            {
                "bank_type": "global",
                "bank_id": "workflow_test",
                "target_file": "preferences.md",
                "operation": "append",
                "content": "## Workflow Test\nThis is a workflow test update.",
                "trigger_type": "user_request",
                "conversation_id": "workflow_test",
                "update_count": 1
            }
        )
    )
    response2 = parse_response(result2[0])
    assert response2["status"] == "success"
    
    # Step 3: Activate a project bank
    result3 = await asyncio.gather(
        server.server.call_tool(
            "activate",
            {
                "bank_type": "project",
                "bank_id": "workflow_project",
                "project_name": "Workflow Test Project",
                "project_description": "A project for testing the workflow."
            }
        )
    )
    response3 = parse_response(result3[0])
    assert response3["status"] == "success"
    
    # Step 4: Update the project bank
    result4 = await asyncio.gather(
        server.server.call_tool(
            "update",
            {
                "bank_type": "project",
                "bank_id": "workflow_project",
                "target_file": "doc/architecture.md",
                "operation": "append",
                "content": "## Test Architecture\nThis is a test architecture update.",
                "trigger_type": "architecture",
                "conversation_id": "workflow_test",
                "update_count": 2
            }
        )
    )
    response4 = parse_response(result4[0])
    assert response4["status"] == "success"
    
    # Step 5: Swap back to the global bank
    result5 = await asyncio.gather(
        server.server.call_tool(
            "swap",
            {
                "bank_type": "global",
                "bank_id": "workflow_test"
            }
        )
    )
    response5 = parse_response(result5[0])
    assert response5["status"] == "success"
    
    # Check that content from step 2 is in the swapped bank
    assert "preferences.md" in response5["content"]
    assert "Workflow Test" in response5["content"]["preferences.md"]
    
    # Step 6: List all banks
    result6 = await asyncio.gather(
        server.server.call_tool(
            "list",
            {}
        )
    )
    response6 = parse_response(result6[0])
    
    # Check that both banks are in the list
    global_banks = response6["global"]
    project_banks = response6["projects"]
    
    global_found = False
    for bank in global_banks:
        if bank["id"] == "workflow_test":
            global_found = True
            break
    assert global_found, "Global bank not found in list"
    
    project_found = False
    for bank in project_banks:
        if bank["id"] == "workflow_project":
            project_found = True
            break
    assert project_found, "Project bank not found in list"
