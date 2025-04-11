"""
Tests for no-api-key cache optimization.
"""

import pytest
import json
import tempfile
import shutil
import os
from pathlib import Path

from memory_bank.cache.llm.optimizer import LLMCacheOptimizer


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    shutil.rmtree(dir_path)


@pytest.fixture
def simple_content():
    """Simple test content."""
    return {
        "test.md": "# Test\n\nSimple test content."
    }


def test_simple_optimization_direct(temp_dir, simple_content):
    """Test simple optimization with no API key directly."""
    # Skip async stuff, we'll create the cache directly
    optimizer = LLMCacheOptimizer(api_key=None)
    
    # Call the simple optimization method directly
    cache_path = temp_dir / "cache.json"
    result = optimizer._optimize_simple(temp_dir, simple_content, cache_path)
    
    # Check result
    assert result is True
    
    # Check cache file exists
    assert cache_path.exists()
    
    # Check cache content
    with open(cache_path, "r") as f:
        cache_data = json.load(f)
    
    # Verify it's a simple optimization
    assert cache_data["optimization_type"] == "simple"
