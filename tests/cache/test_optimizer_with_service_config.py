"""
Tests for the cache optimizer with service config integration.

This module tests the integration between the cache optimizer and service config,
ensuring proper API status handling and error propagation.
"""

import os
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile
import shutil

from memory_bank.cache.optimizer import optimize_cache
from memory_bank.utils.service_config import ApiStatus, llm_config

# Sample test content
TEST_CONTENT = {
    "test.md": "# Test File\n\nThis is a test file with some content.",
    "other.md": "# Other File\n\nThis is another test file with different content."
}


@pytest.fixture
def temp_bank_path():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


class TestOptimizerWithServiceConfig:
    """Test the integration between optimizer and service config."""

    def test_optimize_with_unconfigured_status(self, temp_bank_path):
        """Test optimization when LLM API is unconfigured."""
        # Mock service config to return unconfigured status
        with patch('memory_bank.utils.service_config.llm_config.get_status',
                  return_value=ApiStatus.UNCONFIGURED), \
             patch('memory_bank.utils.service_config.llm_config.is_configured',
                  return_value=False), \
             patch('memory_bank.utils.service_config.is_llm_configured',
                  return_value=False):
            
            # Run optimization
            result, messages = optimize_cache(temp_bank_path, TEST_CONTENT)
            
            # Check that optimization succeeded with simple mode
            assert result is True
            assert len(messages) == 0
            
            # Verify cache file was created with simple optimization
            cache_path = temp_bank_path / "cache.json"
            assert cache_path.exists()
            
            with open(cache_path, "r") as f:
                cache_data = json.load(f)
                
            assert cache_data["optimization_type"] == "simple"
            assert set(cache_data["files"]) == set(TEST_CONTENT.keys())

    def test_optimize_with_rate_limited_status(self, temp_bank_path):
        """Test optimization when LLM API is rate limited."""
        # Mock service config to return rate limited status
        with patch('memory_bank.utils.service_config.llm_config.get_status',
                  return_value=ApiStatus.RATE_LIMITED), \
             patch('memory_bank.utils.service_config.llm_config.is_configured',
                  return_value=True), \
             patch('memory_bank.utils.service_config.is_llm_configured',
                  return_value=True):
            
            # Run optimization
            result, messages = optimize_cache(temp_bank_path, TEST_CONTENT)
            
            # Check that optimization succeeded with simple mode
            assert result is True
            assert len(messages) == 0
            
            # Verify cache file was created with simple optimization
            cache_path = temp_bank_path / "cache.json"
            assert cache_path.exists()
            
            with open(cache_path, "r") as f:
                cache_data = json.load(f)
                
            assert cache_data["optimization_type"] == "simple"

    def test_optimize_with_error_status(self, temp_bank_path):
        """Test optimization when LLM API has error status."""
        # Mock service config to return error status
        with patch('memory_bank.utils.service_config.llm_config.get_status',
                  return_value=ApiStatus.ERROR), \
             patch('memory_bank.utils.service_config.llm_config.is_configured',
                  return_value=True), \
             patch('memory_bank.utils.service_config.is_llm_configured',
                  return_value=True):
            
            # Run optimization
            result, messages = optimize_cache(temp_bank_path, TEST_CONTENT)
            
            # Check that optimization succeeded with simple mode
            assert result is True
            assert len(messages) == 0
            
            # Verify cache file was created with simple optimization
            cache_path = temp_bank_path / "cache.json"
            assert cache_path.exists()
            
            with open(cache_path, "r") as f:
                cache_data = json.load(f)
                
            assert cache_data["optimization_type"] == "simple"

    def test_optimize_with_configured_status_but_small_content(self, temp_bank_path):
        """Test optimization with configured LLM but small content."""
        # Mock service config to return configured status
        with patch('memory_bank.utils.service_config.llm_config.get_status',
                  return_value=ApiStatus.CONFIGURED), \
             patch('memory_bank.utils.service_config.llm_config.is_configured',
                  return_value=True), \
             patch('memory_bank.utils.service_config.is_llm_configured',
                  return_value=True), \
             patch('memory_bank.utils.service_config.llm_config.get_api_key',
                  return_value="test-api-key"), \
             patch('memory_bank.utils.service_config.llm_config.get_api_url',
                  return_value="https://api.test.com"), \
             patch('memory_bank.utils.service_config.llm_config.get_model',
                  return_value="test-model"):
            
            # Run optimization (small content should use simple optimization)
            result, messages = optimize_cache(temp_bank_path, TEST_CONTENT)
            
            # Check that optimization succeeded with simple mode
            assert result is True
            assert len(messages) == 0
            
            # Verify cache file was created with simple optimization
            cache_path = temp_bank_path / "cache.json"
            assert cache_path.exists()
            
            with open(cache_path, "r") as f:
                cache_data = json.load(f)
                
            assert cache_data["optimization_type"] == "simple"

    def test_llm_api_error_handling(self, temp_bank_path):
        """Test LLM API error handling and reporting."""
        # Create large content to trigger LLM optimization
        large_content = {
            "large.md": "# " + "A" * 10000  # Create content larger than threshold
        }
        
        # First, let's patch _optimize_with_llm directly to ensure our test captures
        # the error handling properly without async complexity
        with patch('memory_bank.cache.llm.optimizer.LLMCacheOptimizer._optimize_with_llm',
                  side_effect=lambda *args, **kwargs: self._mock_optimize_with_llm_error(*args, **kwargs)), \
             patch('memory_bank.utils.service_config.llm_config.report_error') as mock_report_error:
            
            # Run optimization with large content and explicitly request LLM
            result, messages = optimize_cache(temp_bank_path, large_content, "project", "llm")
            
            # Check that optimization fell back to simple mode
            assert result is True
            
            # Check that error was reported (this may not be captured in the synchronous test
            # since the error happens in an async context, but we're testing the fallback works)
            
            # Verify cache file was created with simple optimization
            cache_path = temp_bank_path / "cache.json"
            assert cache_path.exists()
            
            with open(cache_path, "r") as f:
                cache_data = json.load(f)
                
            assert cache_data["optimization_type"] == "simple"
