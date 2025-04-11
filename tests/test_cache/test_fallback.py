"""
Test the fallback behavior of the LLM cache optimizer.
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil

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
        "readme.md": "# Test Project\n\nThis is a test project for LLM-based cache optimization.",
        "doc/design.md": "# Design\n\nThis document describes the architecture of the test project.\n\n"
                        "We're using the MVC design pattern with a modular approach.",
        "tasks.md": "# Tasks\n\n- [x] Create project\n- [ ] Implement features\n- [ ] Write tests"
    }


@pytest.mark.asyncio
async def test_simple_optimization_with_no_api_key(temp_bank_dir, mock_content):
    """Test that with no API key, we get a cache file with optimization_type=simple."""
    # Create a special test optimizer that will fail the test if LLM optimization is used
    class TestOptimizer(LLMCacheOptimizer):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.simple_called = False
            
        def _optimize_simple(self, bank_path, content, cache_path):
            """Override to track calls and ensure we get a simple optimization."""
            self.simple_called = True
            
            # Create a simple cache file
            cache_data = {
                "version": "2.0.0",
                "timestamp": "2025-04-10T00:00:00Z",
                "optimization_type": "simple",
                "files": list(content.keys()),
                "summaries": {k: "Mock summary" for k in content.keys()},
                "concepts": {"architecture": ["test"]},
                "consolidated": {"test": "data"},
                "relevance_scores": {k: 0.5 for k in content.keys()}
            }
            cache_path.write_text(json.dumps(cache_data))
            return True
            
        async def _optimize_with_llm(self, *args, **kwargs):
            """This should never be called when api_key is None."""
            assert False, "LLM optimization method should not be called with no API key"
            return False
    
    # Create optimizer with no API key
    optimizer = TestOptimizer(api_key=None)
    
    # Run optimization (with force_full=True to ensure it would use LLM if possible)
    result = await optimizer.optimize_cache(temp_bank_dir, mock_content, "project", True)
    
    # Check result
    assert result is True
    assert optimizer.simple_called, "Simple optimization method was not called"
    
    # Verify cache file exists with the right type
    cache_path = temp_bank_dir / "cache.json"
    assert cache_path.exists(), "Cache file was not created"
    
    with open(cache_path, "r") as f:
        cache_data = json.load(f)
    
    assert cache_data["optimization_type"] == "simple", "Cache should have simple optimization type"
    
    # Clean up
    await optimizer.close()
