"""
Tests for LLM-based cache optimization.
"""

import pytest
import json
import tempfile
from pathlib import Path
import shutil
import os
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

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
                        "We're using the MVC design pattern with a modular approach.\n\n"
                        "## Technology Stack\n\nThe project uses Python with FastAPI for the backend.",
        "tasks.md": "# Tasks\n\n- [x] Create project\n- [ ] Implement features\n- [ ] Write tests"
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return """
{
  "summaries": {
    "readme.md": "An introduction to the test project for LLM-based cache optimization.",
    "doc/design.md": "Architectural documentation describing the project's MVC design pattern and modular approach, with Python and FastAPI as the technology stack.",
    "tasks.md": "Current project tasks showing completed project creation and pending work on feature implementation and testing."
  },
  "concepts": {
    "architecture": ["MVC", "modular approach"],
    "technology": ["Python", "FastAPI"],
    "progress": ["project creation completed"],
    "tasks": ["implement features", "write tests"]
  },
  "relationships": {
    "MVC": ["modular approach"],
    "Python": ["FastAPI"]
  }
}
"""


class MockAsyncResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        
    async def json(self):
        return self.json_data
        
    async def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")


@pytest.mark.asyncio
async def test_llm_cache_optimizer_with_mock(temp_bank_dir, mock_content, mock_llm_response):
    """Test the LLM cache optimizer with mock responses."""
    # Create a mock for the HTTP client
    mock_post = AsyncMock()
    mock_post.return_value = MockAsyncResponse({
        "content": [{"text": mock_llm_response}]
    })
    
    # Create optimizer with mocked HTTP client
    optimizer = LLMCacheOptimizer(api_key="test_key")
    optimizer.http_client.post = mock_post
    
    # Run optimization
    result = await optimizer.optimize_cache(temp_bank_dir, mock_content, "project", True)
    
    # Check result
    assert result is True
    
    # Verify cache file was created
    cache_path = temp_bank_dir / "cache.json"
    assert cache_path.exists()
    
    # Verify cache content
    with open(cache_path, "r") as f:
        cache_data = json.load(f)
    
    # Check structure
    assert "version" in cache_data
    assert "timestamp" in cache_data
    assert "files" in cache_data
    assert "summaries" in cache_data
    assert "concepts" in cache_data
    assert "optimization_type" in cache_data
    
    # Check files list
    assert set(cache_data["files"]) == set(mock_content.keys())
    
    # Clean up
    await optimizer.close()


@pytest.mark.asyncio
@patch("memory_bank.cache.llm.summarizer.summarize_file")
@patch("memory_bank.cache.llm.concepts.extract_concepts_and_relationships")
@patch("memory_bank.cache.llm.views.generate_consolidated_view")
@patch("memory_bank.cache.llm.scoring.calculate_relevance_scores")
async def test_llm_components_integration(mock_scoring, mock_views, mock_concepts, 
                                         mock_summarize, temp_bank_dir, mock_content):
    """Test integration of LLM optimization components."""
    # Setup mocks
    mock_summarize.return_value = "Mocked summary"
    mock_concepts.return_value = ({"architecture": ["MVC"]}, {"MVC": ["design pattern"]})
    mock_views.return_value = {"architecture_decisions": "Uses MVC"}
    mock_scoring.return_value = {"readme.md": 0.8}
    
    # Create optimizer
    optimizer = LLMCacheOptimizer(api_key="test_key")
    
    # Run optimization
    result = await optimizer.optimize_cache(temp_bank_dir, mock_content, "project", True)
    
    # Check result
    assert result is True
    
    # Verify cache file was created
    cache_path = temp_bank_dir / "cache.json"
    assert cache_path.exists()
    
    # Check mocks were called properly
    mock_summarize.assert_called()
    mock_concepts.assert_called_once()
    mock_views.assert_called_once()
    mock_scoring.assert_called_once()
    
    # Clean up
    await optimizer.close()


@pytest.mark.asyncio
async def test_fallback_to_simple_optimization(temp_bank_dir, mock_content):
    """Test fallback to simple optimization when API key is missing."""
    # Create optimizer with no API key
    optimizer = LLMCacheOptimizer(api_key=None)
    
    # Run optimization
    result = await optimizer.optimize_cache(temp_bank_dir, mock_content, "project", True)
    
    # Check result
    assert result is True
    
    # Verify cache file was created
    cache_path = temp_bank_dir / "cache.json"
    assert cache_path.exists()
    
    # Verify cache type is simple
    with open(cache_path, "r") as f:
        cache_data = json.load(f)
    
    assert cache_data["optimization_type"] == "simple"
    
    # Clean up
    await optimizer.close()


def test_sync_optimize_function(temp_bank_dir, mock_content, monkeypatch):
    """Test the synchronous optimize_cache function."""
    # Mock the async optimize function
    async def mock_optimize(*args, **kwargs):
        cache_path = args[0] / "cache.json"
        cache_path.write_text('{"test": "data"}')
        return True
    
    # Apply the mock
    monkeypatch.setattr(
        "memory_bank.cache.llm.optimizer.LLMCacheOptimizer.optimize_cache", 
        mock_optimize
    )
    
    # Import the function to test
    from memory_bank.cache.optimizer import optimize_cache
    
    # Run the function
    result = optimize_cache(temp_bank_dir, mock_content)
    
    # Check result
    assert result is True
    
    # Verify cache file was created
    cache_path = temp_bank_dir / "cache.json"
    assert cache_path.exists()


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), 
                   reason="No API key available for integration test")
@pytest.mark.asyncio
async def test_integration_with_real_api(temp_bank_dir, mock_content):
    """Integration test with real API (requires API key)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("No API key available for integration test")
    
    # Create optimizer with real API key
    optimizer = LLMCacheOptimizer(api_key=api_key)
    
    # Run optimization
    result = await optimizer.optimize_cache(temp_bank_dir, mock_content, "project", True)
    
    # Check result
    assert result is True
    
    # Verify cache file was created
    cache_path = temp_bank_dir / "cache.json"
    assert cache_path.exists()
    
    # Verify cache structure
    with open(cache_path, "r") as f:
        cache_data = json.load(f)
    
    assert "version" in cache_data
    assert "files" in cache_data
    assert "summaries" in cache_data
    assert "concepts" in cache_data
    
    # Clean up
    await optimizer.close()
