"""
Integration tests for the Memory Bank architecture.

This module tests the end-to-end flow through all layers of the architecture.
"""

import os
import pytest
import tempfile
import asyncio
from pathlib import Path
import subprocess
from unittest.mock import patch

from memory_bank_server.server.memory_bank_server import MemoryBankServer


class TestArchitectureIntegration:
    """Integration test for the Memory Bank architecture."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield tmpdirname
    
    @pytest.fixture
    def temp_git_repo(self, temp_dir):
        """Create a temporary Git repository for testing."""
        repo_path = os.path.join(temp_dir, "test-repo")
        os.makedirs(repo_path)
        
        # Initialize Git repository
        try:
            subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
            # Create a test file and commit it
            with open(os.path.join(repo_path, "test.txt"), "w") as f:
                f.write("Test content")
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)
            return repo_path
        except (subprocess.SubprocessError, OSError):
            # Skip Git tests if Git is not available
            pytest.skip("Git not available")
    
    @pytest.fixture
    def server(self, temp_dir):
        """Create a server instance for testing."""
        server = MemoryBankServer(temp_dir)
        return server
    
    @pytest.mark.asyncio
    async def test_end_to_end_global_flow(self, server):
        """Test end-to-end flow with global memory bank."""
        # Initialize the server
        await server.initialize()
        
        # Start memory bank with global type
        result = await server.direct.start_memory_bank(
            force_type="global"
        )
        
        # Verify the memory bank is global
        assert result["selected_memory_bank"]["type"] == "global"
        
        # Update the context in global memory bank
        project_brief_content = "# Test Project Brief\n\nThis is a test project."
        updates = {"project_brief": project_brief_content}
        update_result = await server.direct.bulk_update_context(updates=updates)
        
        # Verify the update was successful
        assert update_result["type"] == "global"
        
        # Get the context back
        retrieved_content = await server.direct.get_project_brief()
        
        # Verify the content is correct
        assert retrieved_content == project_brief_content
        
        # Get all available memory banks
        memory_banks = await server.direct.list_memory_banks()
        
        # Verify the current memory bank is global
        assert memory_banks["current"]["type"] == "global"
    
    @pytest.mark.asyncio
    async def test_end_to_end_project_flow(self, server):
        """Test end-to-end flow with project memory bank."""
        # Initialize the server
        await server.initialize()
        
        # Start memory bank with project creation
        project_result = await server.direct.start_memory_bank(
            project_name="test-project",
            project_description="A test project"
        )
        
        # Verify the project was created
        assert project_result["selected_memory_bank"]["type"] == "project"
        assert "Created project" in " ".join(project_result["actions_taken"])
        
        # Update the context in the project memory bank
        project_brief_content = "# Test Project Brief\n\nThis is a test project."
        updates = {"project_brief": project_brief_content}
        result = await server.direct.bulk_update_context(updates=updates)
        
        # Verify the memory bank is for the project
        assert result["type"] == "project"
        
        # Get the context back
        retrieved_content = await server.direct.get_project_brief()
        
        # Verify the content is correct
        assert retrieved_content == project_brief_content
        
        # Switch back to global memory bank
        await server.direct.select_memory_bank(type="global")
        
        # Get memory banks
        memory_banks = await server.direct.list_memory_banks()
        
        # Verify the current memory bank is global
        assert memory_banks["current"]["type"] == "global"
        
        # Verify the project is in the available memory banks
        assert len(memory_banks["available"]["projects"]) > 0
        project_names = [p["name"] for p in memory_banks["available"]["projects"]]
        assert "test-project" in project_names
    
    @pytest.mark.asyncio
    async def test_end_to_end_repository_flow(self, server, temp_git_repo):
        """Test end-to-end flow with repository memory bank."""
        # Skip if Git is not available
        if temp_git_repo is None:
            pytest.skip("Git not available")
        
        # Initialize the server
        await server.initialize()
        
        # Start memory bank with repository path
        repo_result = await server.direct.start_memory_bank(
            current_path=temp_git_repo
        )
        
        # Verify the memory bank was initialized
        assert repo_result["selected_memory_bank"]["type"] == "repository"
        assert "Detected repository" in " ".join(repo_result["actions_taken"])
        
        # Update the context in the repository memory bank
        project_brief_content = "# Test Repository Brief\n\nThis is a test repository."
        updates = {"project_brief": project_brief_content}
        result = await server.direct.bulk_update_context(updates=updates)
        
        # Verify the memory bank is for the repository
        assert result["type"] == "repository"
        
        # Get the context back
        retrieved_content = await server.direct.get_project_brief()
        
        # Verify the content is correct
        assert retrieved_content == project_brief_content
        
        # Get memory banks
        memory_banks = await server.direct.list_memory_banks()
        
        # Verify the current memory bank is for the repository
        assert memory_banks["current"]["type"] == "repository"
        
        # Verify the repository is in the available memory banks
        assert len(memory_banks["available"]["repositories"]) > 0
        repo_paths = [r["repo_path"] for r in memory_banks["available"]["repositories"]]
        assert temp_git_repo in repo_paths
    
    @pytest.mark.asyncio
    async def test_bulk_context_operations(self, server):
        """Test bulk context operations."""
        # Initialize the server
        await server.initialize()
        
        # Create update data
        updates = {
            "project_brief": "# Project Brief\n\nThis is the project brief.",
            "active_context": "# Active Context\n\nThis is the active context.",
            "progress": "# Progress\n\nThis is the progress."
        }
        
        # Perform bulk update
        result = await server.direct.bulk_update_context(updates=updates)
        
        # Verify the result
        assert result["type"] == "global"
        
        # Get all context
        all_context = await server.direct.get_all_context()
        
        # Verify all context was updated
        assert all_context["project_brief"] == updates["project_brief"]
        assert all_context["active_context"] == updates["active_context"]
        assert all_context["progress"] == updates["progress"]
    
    @pytest.mark.asyncio
    async def test_cross_memory_bank_context_isolation(self, server):
        """Test that context is properly isolated between memory banks."""
        # Initialize the server
        await server.initialize()
        
        # Start with global memory bank
        await server.direct.start_memory_bank(force_type="global")
        
        # Update the global context
        global_brief = "# Global Brief\n\nThis is the global brief."
        await server.direct.bulk_update_context(updates={"project_brief": global_brief})
        
        # Create a project
        await server.direct.start_memory_bank(
            project_name="isolation-test",
            project_description="Testing context isolation"
        )
        
        # Update the project context
        project_brief = "# Project Brief\n\nThis is the project brief."
        await server.direct.bulk_update_context(updates={"project_brief": project_brief})
        
        # Get the project context
        retrieved_project_brief = await server.direct.get_project_brief()
        assert retrieved_project_brief == project_brief
        
        # Switch back to global
        await server.direct.select_memory_bank(type="global")
        
        # Get the global context
        retrieved_global_brief = await server.direct.get_project_brief()
        assert retrieved_global_brief == global_brief
        
        # Verify they are different
        assert retrieved_global_brief != retrieved_project_brief
