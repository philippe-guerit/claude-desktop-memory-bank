"""
Tests for optimizer integration with service_config.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import asyncio

from memory_bank.cache.optimizer import optimize_cache
from memory_bank.utils.service_config import ApiStatus, LLMConfig

# Helper for async tests
def run_async(coro):
    """Run an async function within a test."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


class TestOptimizerConfig:
    """Test the integration of optimizer with service_config."""
    
    def test_optimizer_uses_service_config(self, tmp_path):
        """Test that optimizer uses the service config for LLM settings."""
        # Create test content
        content = {
            "file1.md": "Test content for file 1",
            "file2.md": "Test content for file 2"
        }
        
        # Mock service config to be unconfigured
        with patch('memory_bank.utils.service_config.llm_config') as mock_config:
            mock_config.is_configured.return_value = False
            mock_config.get_status.return_value = ApiStatus.UNCONFIGURED
            mock_config.get_api_key.return_value = ""
            mock_config.get_api_url.return_value = ""
            mock_config.get_model.return_value = ""
            
            # Run optimization
            result, messages = optimize_cache(tmp_path, content)
            
            # Verify result
            assert result is True
            
            # Check the created cache file
            cache_path = tmp_path / "cache.json"
            assert cache_path.exists()
            
            # Load and verify cache content
            with open(cache_path, "r") as f:
                cache_data = json.load(f)
            
            # Verify it used simple optimization due to unconfigured LLM
            assert cache_data["optimization_type"] == "simple"
            
            # Verify API methods were called
            mock_config.is_configured.assert_called()
            mock_config.get_api_key.assert_called()
    
    def test_optimizer_force_llm_respects_config(self, tmp_path):
        """Test that force_llm is ignored when LLM is not configured."""
        # Create test content
        content = {
            "file1.md": "Test content for file 1",
            "file2.md": "Test content for file 2"
        }
        
        # Mock service config to be unconfigured
        with patch('memory_bank.utils.service_config.llm_config') as mock_config:
            mock_config.is_configured.return_value = False
            mock_config.get_status.return_value = ApiStatus.UNCONFIGURED
            mock_config.get_api_key.return_value = ""
            mock_config.get_api_url.return_value = ""
            mock_config.get_model.return_value = ""
            
            # Run optimization with force_llm=True
            result, messages = optimize_cache(tmp_path, content, force_llm=True)
            
            # Verify result
            assert result is True
            
            # Check the created cache file
            cache_path = tmp_path / "cache.json"
            assert cache_path.exists()
            
            # Load and verify cache content
            with open(cache_path, "r") as f:
                cache_data = json.load(f)
            
            # Verify it still used simple optimization due to unconfigured LLM
            assert cache_data["optimization_type"] == "simple"
    
    def test_optimizer_with_configured_llm(self, tmp_path):
        """Test optimizer behavior with a configured LLM."""
        # Create test content - small enough to use simple optimization by default
        content = {
            "file1.md": "Test content for file 1",
            "file2.md": "Test content for file 2"
        }
        
        # Mock service config to be configured
        with patch('memory_bank.utils.service_config.llm_config') as mock_config:
            mock_config.is_configured.return_value = True
            mock_config.get_status.return_value = ApiStatus.CONFIGURED
            mock_config.get_api_key.return_value = "test-api-key"
            mock_config.get_api_url.return_value = "https://api.test.com"
            mock_config.get_model.return_value = "test-model"
            
            # Mock the LLMCacheOptimizer
            with patch('memory_bank.cache.optimizer.LLMCacheOptimizer') as mock_optimizer_class:
                # Create a mock instance
                mock_optimizer = MagicMock()
                mock_optimizer_class.return_value = mock_optimizer
                
                # Setup the simple optimization path
                mock_optimizer._optimize_simple.return_value = True
                
                # Run optimization
                result, messages = optimize_cache(tmp_path, content)
                
                # Verify result
                assert result is True
                
                # Verify the optimizer was initialized with config values
                mock_optimizer_class.assert_called_once_with(
                    api_key="test-api-key",
                    api_url="https://api.test.com",
                    model="test-model"
                )
