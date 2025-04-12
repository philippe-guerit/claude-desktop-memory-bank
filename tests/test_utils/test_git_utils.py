"""
Tests for Git utility functions.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
import subprocess
from datetime import datetime
import logging

from memory_bank.utils.git import (
    detect_git_repo,
    get_branch_list,
    get_git_file_history
)

# Skip all tests if GitPython is not installed
pytestmark = pytest.mark.skipif(
    pytest.importorskip("git", reason="GitPython not installed") is None,
    reason="GitPython not installed"
)


@pytest.fixture
def git_repo():
    """Create a temporary Git repository for testing."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir)
    
    try:
        # Initialize Git repo
        subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True, capture_output=True)
        
        # Create and commit a test file
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content")
        
        subprocess.run(["git", "add", "test.txt"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, check=True, capture_output=True)
        
        # Create a branch
        subprocess.run(["git", "branch", "test-branch"], cwd=temp_dir, check=True, capture_output=True)
        
        # Create a nested directory with a file
        nested_dir = repo_path / "nested"
        nested_dir.mkdir()
        nested_file = nested_dir / "nested.txt"
        nested_file.write_text("Nested content")
        
        subprocess.run(["git", "add", "nested/nested.txt"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add nested file"], cwd=temp_dir, check=True, capture_output=True)
        
        # Update the test file to create history
        test_file.write_text("Updated content")
        subprocess.run(["git", "add", "test.txt"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Update test file"], cwd=temp_dir, check=True, capture_output=True)
        
        yield repo_path
    finally:
        shutil.rmtree(temp_dir)


def test_detect_git_repo(git_repo):
    """Test detecting a Git repository."""
    # Test with the repo root
    result = detect_git_repo(git_repo)
    
    assert result is not None
    assert result["is_git_repo"] is True
    assert result["repo_path"] == str(git_repo)
    assert result["repo_name"] == git_repo.name
    assert result["current_branch"] == "master"  # Default branch name
    assert "last_commit" in result
    assert result["last_commit"]["message"] == "Update test file"
    
    # Test with a subdirectory
    nested_dir = git_repo / "nested"
    result = detect_git_repo(nested_dir)
    
    assert result is not None
    assert result["is_git_repo"] is True
    assert result["repo_path"] == str(git_repo)
    
    # Test with a non-Git directory
    non_git_dir = tempfile.mkdtemp()
    try:
        result = detect_git_repo(Path(non_git_dir))
        assert result is None
    finally:
        shutil.rmtree(non_git_dir)


def test_get_branch_list(git_repo):
    """Test getting a list of branches in a Git repository."""
    # Get branch list
    result = get_branch_list(git_repo)
    
    assert result is not None
    assert result["current_branch"] == "master"  # Default branch name
    
    # Check local branches
    assert "local_branches" in result
    assert len(result["local_branches"]) >= 2  # master and test-branch
    
    # Find master branch
    master_branch = next((b for b in result["local_branches"] if b["name"] == "master"), None)
    assert master_branch is not None
    assert master_branch["is_active"] is True
    
    # Find test-branch
    test_branch = next((b for b in result["local_branches"] if b["name"] == "test-branch"), None)
    assert test_branch is not None
    assert test_branch["is_active"] is False


def test_get_git_file_history(git_repo):
    """Test getting the history of a file in a Git repository."""
    # Get history for test.txt
    result = get_git_file_history(git_repo, "test.txt")
    
    assert result is not None
    assert result["file_path"] == "test.txt"
    assert "history" in result
    assert len(result["history"]) >= 2  # Initial commit and update
    
    # Check the most recent commit first
    latest_commit = result["history"][0]
    assert latest_commit["message"] == "Update test file"
    
    # Second commit should be the initial one
    initial_commit = result["history"][1]
    assert initial_commit["message"] == "Initial commit"
    
    # Test with nested file
    result = get_git_file_history(git_repo, "nested/nested.txt")
    
    assert result is not None
    assert result["file_path"] == "nested/nested.txt"
    assert "history" in result
    assert len(result["history"]) >= 1
    assert result["history"][0]["message"] == "Add nested file"
    
    # Test with non-existent file
    result = get_git_file_history(git_repo, "nonexistent.txt")
    assert result is None


def test_git_integration(git_repo):
    """Test integration between Git utility functions."""
    # First, detect the repo
    repo_info = detect_git_repo(git_repo)
    assert repo_info is not None
    assert repo_info["is_git_repo"] is True
    
    # Get branch list using repo path from detection
    branches = get_branch_list(Path(repo_info["repo_path"]))
    assert branches is not None
    assert branches["current_branch"] == repo_info["current_branch"]
    
    # Get file history for a committed file
    history = get_git_file_history(Path(repo_info["repo_path"]), "test.txt")
    assert history is not None
    assert history["history"][0]["commit_id"] == repo_info["last_commit"]["id"]


def test_automatic_git_detection(git_repo):
    """Test that Git repositories are automatically detected."""
    from memory_bank.server import MemoryBankServer
    import tempfile
    
    # Create a temporary directory for the storage
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_dir = Path(temp_dir)
        
        # Create server with the storage directory
        server = MemoryBankServer(storage_root=storage_dir)
        
        try:
            # Start the server in test mode
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(server.start(test_mode=True))
            
            # Call activate with auto detection
            result = loop.run_until_complete(
                server.call_tool_test(
                    "activate",
                    {
                        "bank_type": "code",
                        "bank_id": "auto",
                        "current_path": str(git_repo)
                    }
                )
            )
            
            # Parse the response
            response = result
            
            # Verify the repository was detected
            assert response["status"] == "success"
            assert response["bank_info"]["type"] == "code"
            
            # Get the bank ID
            bank_id = response["bank_info"]["id"]
            
            # Get the bank and check Git info
            bank = server.storage.get_bank("code", bank_id)
            meta = bank.get_meta()
            
            # Verify Git info
            assert "git" in meta
            assert meta["git"]["is_git_repo"] is True
            assert "repo_path" in meta["git"]
            
            # Clean up
            loop.run_until_complete(server.stop())
            loop.close()
            
        except Exception as e:
            pytest.fail(f"Git detection test failed: {e}")
