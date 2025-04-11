"""
Simplified test for the cache optimization system.
"""

import pytest
import json
import tempfile
from pathlib import Path
import shutil
import asyncio

from memory_bank.cache.llm.optimizer import LLMCacheOptimizer


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    shutil.rmtree(dir_path)


@pytest.fixture
def test_content():
    """Simple test content for cache optimization."""
    return {
        "file1.md": "# Test File 1\n\nThis is test content.",
        "file2.md": "# Test File 2\n\nMore test content."
    }


@pytest.mark.asyncio
async def test_simple_cache_with_no_api_key(temp_dir, test_content):
    """Test that simple cache is created when no API key is provided."""
    # Create optimizer with no API key
    optimizer = LLMCacheOptimizer(api_key=None)
    
    # Run optimization (force_full is ignored with no API key)
    result = await optimizer.optimize_cache(temp_dir, test_content, "test", True)
    
    # Check result
    assert result is True
    
    # Check cache file exists
    cache_path = temp_dir / "cache.json"
    assert cache_path.exists()
    
    # Check cache content
    with open(cache_path, "r") as f:
        cache_data = json.load(f)
    
    # Verify it's a simple optimization
    assert cache_data["optimization_type"] == "simple"
    assert "version" in cache_data
    assert "files" in cache_data
    assert set(cache_data["files"]) == set(test_content.keys())
    
    # Clean up
    await optimizer.close()
