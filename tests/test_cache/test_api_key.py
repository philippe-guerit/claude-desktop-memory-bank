"""
Test for API key handling in the cache optimization system.

This module tests specifically how the optimizer behaves with and without an API key.
"""

import pytest
import json
import tempfile
from pathlib import Path
import shutil
import os
from unittest.mock import AsyncMock, patch, MagicMock

from memory_bank.cache.optimizer import optimize_cache
from memory_bank.cache.llm.optimizer import LLMCacheOptimizer


@pytest.fixture
def temp_bank_dir():
    """Create a temporary directory for a memory bank."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_content():
    """Sample content for testing."""
    return {
        "readme.md": "# Test Project\n\nThis is a test project for cache optimization.",
        "doc/design.md": "# Design\n\nThis document describes the design of the test project.",
        "tasks.md": "# Tasks\n\n- [x] Create project\n- [ ] Implement features\n- [ ] Write tests"
    }


def test_api_key_handling(temp_bank_dir, mock_content, monkeypatch):
    """
    Test that the API key is properly checked and that we fall back to simple
    optimization when no API key is available.
    """
    # Save original environment values
    original_api_key = os.environ.get("OPENROUTER_API_KEY", "")
    original_api_url = os.environ.get("LLM_API_URL", "")
    original_model = os.environ.get("LLM_MODEL", "")
    
    try:
        # Set environment variables to empty to ensure no API key is available
        monkeypatch.setenv("OPENROUTER_API_KEY", "")
        monkeypatch.setenv("LLM_API_URL", "")
        monkeypatch.setenv("LLM_MODEL", "")
        
        # Run optimization with force_llm=True
        success, messages = optimize_cache(temp_bank_dir, mock_content, "project", True)
        
        # Verify optimization was successful
        assert success is True
        
        # Verify the cache file was created
        cache_path = temp_bank_dir / "cache.json"
        assert cache_path.exists()
        
        # Verify the cache has the simple optimization type
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
        
        # The key check is that even with force_llm=True, we got a simple optimization
        # due to the missing API key
        assert cache_data["optimization_type"] == "simple", \
            "Should use simple optimization when no API key is available"
    
    finally:
        # Restore original environment values
        if original_api_key:
            monkeypatch.setenv("OPENROUTER_API_KEY", original_api_key)
        if original_api_url:
            monkeypatch.setenv("LLM_API_URL", original_api_url)
        if original_model:
            monkeypatch.setenv("LLM_MODEL", original_model)


def test_optimizer_contains_security_check(monkeypatch):
    """
    Test that the LLM optimizer contains the critical security check to validate
    the API key before attempting to use LLM optimization.
    """
    # Create an optimizer with no API key
    optimizer = LLMCacheOptimizer(api_key=None)
    
    # Set up a function to track if _optimize_with_llm is called
    llm_called = False
    async def mock_optimize_with_llm(*args, **kwargs):
        nonlocal llm_called
        llm_called = True
        return True
    
    # Set up a function to track if _optimize_simple is called
    simple_called = False
    def mock_optimize_simple(*args, **kwargs):
        nonlocal simple_called
        simple_called = True
        return True
    
    # Mock the optimizer methods
    optimizer._optimize_with_llm = mock_optimize_with_llm
    optimizer._optimize_simple = mock_optimize_simple
    
    # Create a test directory
    test_dir = Path(tempfile.mkdtemp())
    try:
        # Create test content
        content = {"test.md": "Test content"}
        
        # Run the optimization with force_full=True which would use LLM if API key was present
        import asyncio
        result = asyncio.run(optimizer.optimize_cache(test_dir, content, "project", True))
        
        # Validate the result
        assert result is True, "Optimization should succeed even without API key"
        assert simple_called, "Simple optimization should be used when no API key is present"
        assert not llm_called, "LLM optimization should not be used when no API key is present"
    finally:
        shutil.rmtree(test_dir)
