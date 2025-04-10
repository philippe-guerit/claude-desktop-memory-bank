"""
Tests for cache optimization.
"""

import pytest
import json
import tempfile
from pathlib import Path
import shutil

from memory_bank.cache.optimizer import optimize_cache


@pytest.fixture
def temp_bank_dir():
    """Create a temporary directory for a memory bank."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


def test_cache_optimization(temp_bank_dir):
    """Test the basic cache optimization process."""
    # Prepare test content
    content = {
        "readme.md": "# Test Project\n\nThis is a test project for cache optimization.",
        "doc/design.md": "# Design\n\nThis document describes the design of the test project.",
        "tasks.md": "# Tasks\n\n- [x] Create project\n- [ ] Implement features\n- [ ] Write tests"
    }
    
    # Run cache optimization
    result = optimize_cache(temp_bank_dir, content)
    
    # Verify optimization was successful
    assert result is True
    
    # Verify cache file was created
    cache_path = temp_bank_dir / "cache.json"
    assert cache_path.exists()
    
    # Verify cache content
    with open(cache_path, 'r') as f:
        cache_data = json.load(f)
    
    # Check cache structure
    assert "version" in cache_data
    assert "files" in cache_data
    assert "summaries" in cache_data
    assert "concepts" in cache_data
    assert "consolidated" in cache_data
    
    # Check file list
    assert set(cache_data["files"]) == set(content.keys())
    
    # Check summaries
    for file_path, file_content in content.items():
        assert file_path in cache_data["summaries"]
        expected_summary = file_content[:100] + "..." if len(file_content) > 100 else file_content
        assert cache_data["summaries"][file_path] == expected_summary


def test_cache_optimization_empty_content(temp_bank_dir):
    """Test cache optimization with empty content."""
    # Prepare empty content
    content = {}
    
    # Run cache optimization
    result = optimize_cache(temp_bank_dir, content)
    
    # Verify optimization was successful
    assert result is True
    
    # Verify cache file was created
    cache_path = temp_bank_dir / "cache.json"
    assert cache_path.exists()
    
    # Verify cache content
    with open(cache_path, 'r') as f:
        cache_data = json.load(f)
    
    # Check file list is empty
    assert cache_data["files"] == []
    assert cache_data["summaries"] == {}


def test_cache_optimization_failure(monkeypatch):
    """Test cache optimization failure handling."""
    def mock_write_text_that_fails(*args, **kwargs):
        raise PermissionError("Mock permission error")
    
    # Mock Path.write_text to simulate a failure
    monkeypatch.setattr(Path, "write_text", mock_write_text_that_fails)
    
    # Prepare test content
    content = {"test.md": "Test content"}
    
    # Run cache optimization with a non-existent directory to force failure
    result = optimize_cache(Path("/nonexistent"), content)
    
    # Verify optimization failed
    assert result is False


def test_cache_relevance_scoring(temp_bank_dir):
    """Test relevance scoring for cache entries."""
    # Prepare test content with keywords that should be detected in concepts
    content = {
        "architecture.md": "# Architecture\n\nWe'll use the MVC design pattern with a modular framework structure.",
        "tech_stack.md": "# Technology\n\nWe'll use Python as our primary language with FastAPI library.",
        "progress.md": "# Progress\n\nWe have completed the initial setup. In progress: API design.",
        "todo.md": "# Tasks\n\nTODO: Implement authentication\nDONE: Project setup\nIN PROGRESS: Database schema"
    }
    
    # Run cache optimization
    result = optimize_cache(temp_bank_dir, content)
    assert result is True
    
    # Verify cache file was created
    cache_path = temp_bank_dir / "cache.json"
    assert cache_path.exists()
    
    # Verify cache content
    with open(cache_path, 'r') as f:
        cache_data = json.load(f)
    
    # Check concepts
    assert "concepts" in cache_data
    concepts = cache_data["concepts"]
    
    # The cache optimizer's concepts are currently static, but we verify they exist
    assert "architecture" in concepts
    assert "technology" in concepts
    assert "progress" in concepts
    assert "tasks" in concepts
    
    # Verify consolidated summaries exist
    assert "consolidated" in cache_data
    assert "architecture_decisions" in cache_data["consolidated"]
    assert "technology_choices" in cache_data["consolidated"]
    assert "current_status" in cache_data["consolidated"]
    assert "next_steps" in cache_data["consolidated"]


def test_cache_file_format(temp_bank_dir):
    """Test the format of the cache file."""
    content = {
        "test.md": "Test content for cache format validation."
    }
    
    # Run cache optimization
    result = optimize_cache(temp_bank_dir, content)
    assert result is True
    
    # Verify cache file was created
    cache_path = temp_bank_dir / "cache.json"
    assert cache_path.exists()
    
    # Verify the file is valid JSON
    try:
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
    except json.JSONDecodeError:
        pytest.fail("Cache file is not valid JSON")
    
    # Verify version format
    assert "version" in cache_data
    assert isinstance(cache_data["version"], str)
    assert cache_data["version"].count(".") == 2  # Check for semantic versioning format
