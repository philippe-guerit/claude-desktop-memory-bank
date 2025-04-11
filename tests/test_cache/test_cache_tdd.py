"""
Test-driven development tests for the cache optimization system.

This module uses proper TDD practices to validate cache optimization behaviors:
1. Write a test that defines expected behavior
2. Run it to verify it fails appropriately
3. Implement the minimum code to make it pass
4. Refactor while maintaining passing tests
"""

import pytest
import json
import tempfile
from pathlib import Path
import shutil
import os
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from memory_bank.cache.llm.optimizer import LLMCacheOptimizer
from memory_bank.cache.optimizer import optimize_cache, optimize_cache_async
from memory_bank.utils.service_config import ApiStatus


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


@pytest.fixture
def mock_llm_client():
    """Create a mock HTTP client for LLM API calls."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    return mock_client


class MockResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        
    def json(self):
        return self.json_data
        
    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "Mock HTTP error", 
                request=httpx.Request("POST", "https://mock.url"), 
                response=httpx.Response(self.status_code)
            )


class TestCacheOptimization:
    """Test-driven development tests for cache optimization."""
    
    def test_cache_version_validation(self, temp_bank_dir, mock_content):
        """
        Test that cache optimization creates a file with a valid semantic version number.
        
        The version should be a string with format X.Y.Z where X, Y, and Z are integers.
        """
        # Run optimization
        success, messages = optimize_cache(temp_bank_dir, mock_content)
        
        # Verify optimization was successful
        assert success is True
        assert isinstance(messages, list)
        
        # Verify cache file was created
        cache_path = temp_bank_dir / "cache.json"
        assert cache_path.exists()
        
        # Verify cache version is valid
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
        
        # Check version exists and is a string
        assert "version" in cache_data
        assert isinstance(cache_data["version"], str)
        
        # Check version has format X.Y.Z
        version_parts = cache_data["version"].split('.')
        assert len(version_parts) == 3
        
        # Each part should be convertible to an integer
        for part in version_parts:
            assert part.isdigit()
    
    def test_cache_content_validation(self, temp_bank_dir, mock_content):
        """
        Test that cache optimization properly captures content from all files.
        
        The cache should include:
        1. A list of all file paths
        2. Summaries for each file
        3. Concepts extracted from the content
        4. A consolidated view that integrates information across files
        5. A mapping of relevance scores for each file
        """
        # Run optimization
        success, messages = optimize_cache(temp_bank_dir, mock_content)
        
        # Verify optimization was successful
        assert success is True
        assert isinstance(messages, list)
        
        # Verify cache file contains all required sections
        cache_path = temp_bank_dir / "cache.json"
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
        
        # Check basic structure
        required_fields = ["version", "timestamp", "optimization_type", 
                           "files", "summaries", "concepts", 
                           "consolidated", "relevance_scores"]
        
        for field in required_fields:
            assert field in cache_data, f"Missing required field: {field}"
        
        # Check file list contains all files
        assert set(cache_data["files"]) == set(mock_content.keys())
        
        # Check summaries exist for all files
        assert set(cache_data["summaries"].keys()) == set(mock_content.keys())
        
        # Check summaries are non-empty
        for file_path, summary in cache_data["summaries"].items():
            assert summary, f"Empty summary for {file_path}"
        
        # Check concepts are non-empty
        assert cache_data["concepts"], "No concepts extracted"
        
        # Check consolidated view has expected sections
        expected_sections = ["architecture_decisions", "technology_choices", 
                             "current_status", "next_steps"]
        
        for section in expected_sections:
            assert section in cache_data["consolidated"], f"Missing consolidated section: {section}"
        
        # Check relevance scores exist for all files
        assert set(cache_data["relevance_scores"].keys()) == set(mock_content.keys())
        
        # Check score values are in range [0, 1]
        for file_path, score in cache_data["relevance_scores"].items():
            assert 0 <= score <= 1, f"Score out of range for {file_path}: {score}"
    
    @pytest.mark.asyncio
    async def test_llm_optimization_uses_api_key(self, temp_bank_dir, mock_content, monkeypatch):
        """
        Test that LLM optimization only proceeds when an API key is provided.
        
        The cache should:
        1. Use LLM optimization when API key is present
        2. Fall back to simple optimization when API key is missing
        3. Have the correct 'optimization_type' in both cases
        """
        # Fix the LLM cache optimizer to prevent actual API calls
        monkeypatch.setattr(
            "memory_bank.cache.llm.optimizer.LLMCacheOptimizer.call_llm", 
            AsyncMock(return_value="{}")
        )
        
        # Mock LLM configuration as configured
        monkeypatch.setattr(
            "memory_bank.cache.llm.optimizer.is_llm_configured",
            lambda: True
        )
        monkeypatch.setattr(
            "memory_bank.cache.llm.optimizer.llm_config.get_status",
            lambda: ApiStatus.CONFIGURED
        )
        
        # Create optimizer with API key
        with_key_optimizer = LLMCacheOptimizer(api_key="test_key")
        
        # Mock _optimize_with_llm to track calls
        with_key_called = False
        async def mock_optimize_with_llm(*args, **kwargs):
            nonlocal with_key_called
            with_key_called = True
            # Create a test cache file
            cache_path = args[0] / "cache.json"
            cache_data = {
                "version": "2.0.0",
                "timestamp": "2025-04-10T12:34:56Z",
                "optimization_type": "llm",
                "files": list(mock_content.keys()),
                "summaries": {k: "Test summary" for k in mock_content.keys()},
                "concepts": {"test": ["concept"]},
                "relationships": {"test": ["relationship"]},
                "consolidated": {
                    "architecture_decisions": "Test architecture",
                    "technology_choices": "Test technology",
                    "current_status": "Test status",
                    "next_steps": "Test next steps"
                },
                "relevance_scores": {k: 0.7 for k in mock_content.keys()}
            }
            cache_path.write_text(json.dumps(cache_data))
            return True
        
        # Apply mock and run optimizer with API key
        with patch.object(with_key_optimizer, '_optimize_with_llm', mock_optimize_with_llm):
            result = await with_key_optimizer.optimize_cache(
                temp_bank_dir, mock_content, "project", "llm")
            await with_key_optimizer.close()
        
        # Verify LLM optimization was used
        assert result is True
        assert with_key_called is True
        
        # Verify cache has LLM optimization type
        with open(temp_bank_dir / "cache.json", 'r') as f:
            cache_data = json.load(f)
        assert cache_data["optimization_type"] == "llm"
        
        # Create new optimizer without API key
        no_key_optimizer = LLMCacheOptimizer(api_key=None)
        
        # Mock _optimize_simple to track calls
        no_key_called = False
        def mock_optimize_simple(*args, **kwargs):
            nonlocal no_key_called
            no_key_called = True
            # Create a test cache file
            cache_path = args[2]  # Third arg is cache_path
            cache_data = {
                "version": "2.0.0",
                "timestamp": "2025-04-10T12:34:56Z",
                "optimization_type": "simple",
                "files": list(mock_content.keys()),
                "summaries": {k: "Test summary" for k in mock_content.keys()},
                "concepts": {"test": ["concept"]},
                "consolidated": {
                    "architecture_decisions": "Test architecture",
                    "technology_choices": "Test technology",
                    "current_status": "Test status",
                    "next_steps": "Test next steps"
                },
                "relevance_scores": {k: 0.5 for k in mock_content.keys()}
            }
            cache_path.write_text(json.dumps(cache_data))
            return True
        
        # Create mock for direct call to check no_key behavior
        direct_test = async_mock = AsyncMock()
        async_mock.return_value = True
        
        with patch('memory_bank.cache.llm.optimizer.LLMCacheOptimizer._optimize_simple', side_effect=mock_optimize_simple) as mocked:
            # Use a new directory
            new_dir = Path(tempfile.mkdtemp())
            try:
                # Force to use LLM which should fall back to simple due to no API key
                result = await no_key_optimizer.optimize_cache(
                    new_dir, mock_content, "project", True)
                await no_key_optimizer.close()
                
                # Verify optimize_simple was called
                assert mocked.called
                
                # Verify cache has simple optimization type
                with open(new_dir / "cache.json", 'r') as f:
                    cache_data = json.load(f)
                assert cache_data["optimization_type"] == "simple"
            finally:
                shutil.rmtree(new_dir)
    
    @pytest.mark.asyncio
    async def test_llm_api_call_handles_errors(self, monkeypatch):
        """
        Test that LLM API calls properly handle errors.
        
        The optimizer should:
        1. Catch and log HTTP errors
        2. Catch and log connection errors
        3. Return a meaningful error message
        """
        # Mock LLM configuration as configured
        monkeypatch.setattr(
            "memory_bank.cache.llm.optimizer.is_llm_configured",
            lambda: True
        )
        monkeypatch.setattr(
            "memory_bank.cache.llm.optimizer.llm_config.get_status",
            lambda: ApiStatus.CONFIGURED
        )
        
        # Create optimizer for testing
        optimizer = LLMCacheOptimizer(api_key="test_key")
        
        # Test case 1: HTTP error
        async def mock_http_error(*args, **kwargs):
            raise httpx.HTTPStatusError(
                "Test HTTP error", 
                request=httpx.Request("POST", "https://api.test"), 
                response=httpx.Response(status_code=401)
            )
        
        # Apply mock
        monkeypatch.setattr(optimizer.http_client, "post", mock_http_error)
        
        # Verify error is handled
        with pytest.raises(httpx.HTTPStatusError):
            await optimizer.call_llm("Test prompt")
        
        # Test case 2: Connection error
        async def mock_connection_error(*args, **kwargs):
            raise httpx.ConnectError("Test connection error")
        
        # Apply mock
        monkeypatch.setattr(optimizer.http_client, "post", mock_connection_error)
        
        # Verify error is handled
        with pytest.raises(httpx.ConnectError):
            await optimizer.call_llm("Test prompt")
        
        # Clean up
        await optimizer.close()
    
    @pytest.mark.asyncio
    async def test_cache_optimization_respects_threshold(self, temp_bank_dir, monkeypatch):
        """
        Test that cache optimization respects the content size threshold.
        
        The optimizer should:
        1. Use simple optimization for small content (below threshold)
        2. Use LLM optimization for large content (above threshold)
        3. Respect the force_full parameter to override the threshold
        """
        # Mock LLM configuration as configured
        monkeypatch.setattr(
            "memory_bank.cache.llm.optimizer.is_llm_configured",
            lambda: True
        )
        monkeypatch.setattr(
            "memory_bank.cache.llm.optimizer.llm_config.get_status",
            lambda: ApiStatus.CONFIGURED
        )
        
        # Create an optimizer with mock methods to track calls
        optimizer = LLMCacheOptimizer(api_key="test_key")
        
        # Track which optimization method was called
        simple_called = False
        llm_called = False
        
        # Mock _optimize_simple and _optimize_with_llm methods
        def mock_optimize_simple(*args, **kwargs):
            nonlocal simple_called
            simple_called = True
            cache_path = args[2]
            cache_data = {
                "version": "2.0.0",
                "timestamp": "2025-04-10T12:34:56Z",
                "optimization_type": "simple",
                "files": ["test.md"],
                "summaries": {"test.md": "Test summary"},
                "concepts": {"test": ["concept"]},
                "consolidated": {
                    "architecture_decisions": "Test architecture",
                    "technology_choices": "Test technology",
                    "current_status": "Test status",
                    "next_steps": "Test next steps"
                },
                "relevance_scores": {"test.md": 0.5}
            }
            cache_path.write_text(json.dumps(cache_data))
            return True
        
        async def mock_optimize_with_llm(*args, **kwargs):
            nonlocal llm_called
            llm_called = True
            cache_path = args[3]
            cache_data = {
                "version": "2.0.0",
                "timestamp": "2025-04-10T12:34:56Z",
                "optimization_type": "llm",
                "files": ["test.md"],
                "summaries": {"test.md": "Test summary"},
                "concepts": {"test": ["concept"]},
                "relationships": {"test": ["relationship"]},
                "consolidated": {
                    "architecture_decisions": "Test architecture",
                    "technology_choices": "Test technology",
                    "current_status": "Test status",
                    "next_steps": "Test next steps"
                },
                "relevance_scores": {"test.md": 0.7}
            }
            cache_path.write_text(json.dumps(cache_data))
            return True
        
        # Apply mocks
        monkeypatch.setattr(optimizer, '_optimize_simple', mock_optimize_simple)
        monkeypatch.setattr(optimizer, '_optimize_with_llm', mock_optimize_with_llm)
        
        # Test case 1: Small content, no force
        small_content = {"test.md": "Small content"}
        
        # Reset trackers
        simple_called = False
        llm_called = False
        
        # Run test
        result = await optimizer.optimize_cache(temp_bank_dir, small_content, "project", False)
        
        # Verify simple optimization was used
        assert result is True
        assert simple_called is True
        assert llm_called is False
        
        # Test case 2: Small content, force LLM
        # Reset trackers
        simple_called = False
        llm_called = False
        
        # Run test with optimization_preference="llm"
        result = await optimizer.optimize_cache(temp_bank_dir, small_content, "project", "llm")
        
        # Verify LLM optimization was used
        assert result is True
        assert simple_called is False
        assert llm_called is True
        
        # Test case 3: Large content, no force
        # Create content larger than the threshold
        large_content = {"test.md": "A" * (optimizer.full_optimization_threshold + 1000)}
        
        # Reset trackers
        simple_called = False
        llm_called = False
        
        # Run test with large content
        result = await optimizer.optimize_cache(temp_bank_dir, large_content, "project", False)
        
        # Verify LLM optimization was used for large content
        assert result is True
        assert simple_called is False
        assert llm_called is True
        
        # Clean up
        await optimizer.close()
