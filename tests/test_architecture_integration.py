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
        
        # Update the context in global memory bank
        project_brief_content = "# Test Project Brief\n\nThis is a test project."
        result = await server.direct.update_context(
            context_type="project_brief",
            content=project_brief_content
        )
        
        # Verify the memory bank is global
        assert result["type"] == "global"
        
        # Get the context back
        retrieved_content = await server.direct.get_project_brief()
        
        # Verify the content is correct
        assert retrieved_content == project_brief_content
        
        # Search the context
        search_result = await server.direct.search_context(query="test project")
        
        # Verify the search result contains the brief
        assert "project_brief" in search_result
        assert len(search_result["project_brief"]) > 0
        
        # Get all available memory banks
        memory_banks = await server.direct.list_memory_banks()
        
        # Verify the current memory bank is global
        assert memory_banks["current"]["type"] == "global"
    
    @pytest.mark.asyncio
    async def test_end_to_end_project_flow(self, server):
        """Test end-to-end flow with project memory bank."""
        # Initialize the server
        await server.initialize()
        
        # Create a new project
        project_result = await server.direct.create_project(
            name="test-project",
            description="A test project"
        )
        
        # Verify the project was created
        assert project_result["name"] == "test-project"
        
        # Update the context in the project memory bank
        project_brief_content = "# Test Project Brief\n\nThis is a test project."
        result = await server.direct.update_context(
            context_type="project_brief",
            content=project_brief_content
        )
        
        # Verify the memory bank is for the project
        assert result["type"] == "project"
        assert result["project"] == "test-project"
        
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
        
        # Detect the repository
        repo_info = await server.direct.detect_repository(path=temp_git_repo)
        
        # Verify the repository was detected
        assert repo_info["name"] == os.path.basename(temp_git_repo)
        assert repo_info["path"] == temp_git_repo
        
        # Initialize the repository memory bank
        repo_mb = await server.direct.initialize_repository_memory_bank(
            repository_path=temp_git_repo
        )
        
        # Verify the memory bank was initialized
        assert repo_mb["type"] == "repository"
        assert repo_mb["repo_info"]["name"] == os.path.basename(temp_git_repo)
        
        # Update the context in the repository memory bank
        project_brief_content = "# Test Repository Brief\n\nThis is a test repository."
        result = await server.direct.update_context(
            context_type="project_brief",
            content=project_brief_content
        )
        
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
        
        # Test auto-summarize
        conversation_text = """
        This project is a memory bank system.
        It maintains context across conversations.
        Current progress: finished refactoring the architecture.
        """
        
        auto_result = await server.direct.auto_summarize_context(
            conversation_text=conversation_text
        )
        
        # Verify that summarization extracted content
        assert "project_brief" in auto_result
        assert "memory bank" in auto_result["project_brief"].lower()
    
    @pytest.mark.asyncio
    async def test_cross_memory_bank_context_isolation(self, server):
        """Test that context is properly isolated between memory banks."""
        # Initialize the server
        await server.initialize()
        
        # Update the global context
        global_brief = "# Global Brief\n\nThis is the global brief."
        await server.direct.update_context(
            context_type="project_brief",
            content=global_brief
        )
        
        # Create a project
        await server.direct.create_project(
            name="isolation-test",
            description="Testing context isolation"
        )
        
        # Update the project context
        project_brief = "# Project Brief\n\nThis is the project brief."
        await server.direct.update_context(
            context_type="project_brief",
            content=project_brief
        )
        
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
