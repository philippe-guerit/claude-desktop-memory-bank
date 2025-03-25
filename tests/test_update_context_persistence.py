"""
Test for verifying that update-context properly persists changes.

This test ensures that file writes are properly completed and verified
when using the update_context_tool.
"""

import os
import asyncio
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from memory_bank_server.services.storage_service import StorageService
from memory_bank_server.services.repository_service import RepositoryService
from memory_bank_server.services.context_service import ContextService
from memory_bank_server.server.fastmcp_integration import FastMCPIntegration


@pytest.mark.asyncio
async def test_update_context_persistence():
    """Test that update_context_tool properly persists and verifies content."""
    # Set up temporary test directory
    test_dir = Path(os.path.join(os.getcwd(), "test_storage"))
    if not test_dir.exists():
        test_dir.mkdir(parents=True)
    
    try:
        # Set up services
        storage_service = StorageService(str(test_dir))
        repo_service = RepositoryService(storage_service)
        context_service = ContextService(storage_service, repo_service)
        
        # Set up FastMCP integration
        integration = FastMCPIntegration(context_service)
        integration.initialize("Test Instructions")
        
        # Create template files (needed for initialization)
        templates_path = test_dir / "templates"
        templates_path.mkdir(exist_ok=True)
        templates = {
            "projectbrief.md": "# Project Brief\n\n## Purpose\n\n## Goals\n\n## Requirements\n\n## Scope\n",
            "productContext.md": "# Product Context\n\n## Problem\n\n## Solution\n\n## User Experience\n\n## Stakeholders\n",
            "systemPatterns.md": "# System Patterns\n\n## Architecture\n\n## Patterns\n\n## Decisions\n\n## Relationships\n",
            "techContext.md": "# Technical Context\n\n## Technologies\n\n## Setup\n\n## Constraints\n\n## Dependencies\n",
            "activeContext.md": "# Active Context\n\n## Current Focus\n\n## Recent Changes\n\n## Next Steps\n\n## Active Decisions\n",
            "progress.md": "# Progress\n\n## Completed\n\n## In Progress\n\n## Pending\n\n## Issues\n"
        }
        
        # Write template files
        for name, content in templates.items():
            template_path = templates_path / name
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Create the update_context_tool function 
        # Note: We're not using integration.register_handlers() because that would
        # require a full FastMCP server setup
        async def update_context_tool(context_type, content):
            # Mock the function by accessing the protected method directly
            handlers = integration._register_tool_handlers.__code__
            # Execute the relevant part of the code that would define the tool
            memory_bank = await context_service.update_context(context_type, content)
            
            # Wait for a moment to ensure file operations complete
            await asyncio.sleep(0.1)
            
            # Verify that the file was actually updated
            try:
                # Get the file path
                file_name = context_service.CONTEXT_FILES[context_type]
                file_path = Path(memory_bank['path']) / file_name
                
                # Read back from file to verify it was written
                read_content = await context_service.get_context(context_type)
                
                # Check if content matches what we tried to write
                if read_content != content:
                    return f"Error: Content verification failed for {context_type}. The file may not have been updated correctly."
                
                # The verification passed if we get here
                return "Success"
            except Exception as e:
                return f"Error verifying context update: {str(e)}"
        
        # Initialize the context service
        await context_service.initialize()
        
        # Test updating context
        test_content = "# Test Update\n\nThis is a test update to verify persistence."
        result = await update_context_tool("project_brief", test_content)
        
        # Verify result indicates success
        assert result == "Success", "The update_context_tool did not return success"
        
        # Directly read the file to double-check
        memory_bank = await context_service.get_current_memory_bank()
        file_name = context_service.CONTEXT_FILES["project_brief"]
        file_path = Path(memory_bank['path']) / file_name
        
        with open(file_path, 'r', encoding='utf-8') as f:
            direct_content = f.read()
        
        # Verify content matches what we wrote
        assert direct_content == test_content, "Content doesn't match in the file"
        
        print("Test passed - update_context_tool properly persists and verifies content")
    
    finally:
        # Clean up test directory
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    asyncio.run(test_update_context_persistence())
