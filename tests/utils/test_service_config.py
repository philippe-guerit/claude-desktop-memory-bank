"""
Tests for the service_config module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from memory_bank.utils.service_config import LLMConfig, ApiStatus, is_llm_configured


class TestLLMConfig:
    """Test the LLMConfig class."""

    def test_unconfigured_state(self):
        """Test an unconfigured state with empty environment variables."""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "",
            "LLM_API_URL": "",
            "LLM_MODEL": ""
        }, clear=True):
            config = LLMConfig()
            
            assert config.get_status() == ApiStatus.UNCONFIGURED
            assert not config.is_configured()
            assert config.get_api_key() == ""
            assert config.get_api_url() == ""
            assert config.get_model() == ""
    
    def test_configured_state(self):
        """Test a properly configured state with all environment variables set."""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "test-api-key",
            "LLM_API_URL": "https://api.test.com",
            "LLM_MODEL": "test-model"
        }, clear=True):
            config = LLMConfig()
            
            assert config.get_status() == ApiStatus.CONFIGURED
            assert config.is_configured()
            assert config.get_api_key() == "test-api-key"
            assert config.get_api_url() == "https://api.test.com"
            assert config.get_model() == "test-model"
    
    def test_partially_configured_state(self):
        """Test a partially configured state (missing some variables)."""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "test-api-key",
            "LLM_API_URL": "",  # Missing URL
            "LLM_MODEL": "test-model"
        }, clear=True):
            config = LLMConfig()
            
            assert config.get_status() == ApiStatus.UNCONFIGURED
            assert not config.is_configured()
            # Even with partial configuration, getters return empty strings when unconfigured
            assert config.get_api_key() == ""
            assert config.get_api_url() == ""
            assert config.get_model() == ""
    
    def test_error_reporting_transient(self):
        """Test reporting a transient error."""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "test-api-key",
            "LLM_API_URL": "https://api.test.com",
            "LLM_MODEL": "test-model"
        }, clear=True):
            config = LLMConfig()
            
            # Initially configured
            assert config.get_status() == ApiStatus.CONFIGURED
            
            # Report a non-critical error
            config.report_error("Connection timeout")
            
            # Should still be configured after one error
            assert config.get_status() == ApiStatus.CONFIGURED
            
            # Report multiple errors
            for i in range(3):  # Report 3 errors (matching _max_retry_errors)
                config.report_error(f"Error {i}")
            
            # Should now be in error state
            assert config.get_status() == ApiStatus.ERROR
            
            # Reset should clear the error state
            config.reset()
            assert config.get_status() == ApiStatus.CONFIGURED
    
    def test_error_reporting_permanent(self):
        """Test reporting a permanent error."""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "test-api-key",
            "LLM_API_URL": "https://api.test.com",
            "LLM_MODEL": "test-model"
        }, clear=True):
            config = LLMConfig()
            
            # Initially configured
            assert config.get_status() == ApiStatus.CONFIGURED
            
            # Report a critical authentication error
            config.report_error("Authentication failed: Invalid API key", is_permanent=True)
            
            # Should now be unconfigured
            assert config.get_status() == ApiStatus.UNCONFIGURED
            
            # Reset should not fix permanent errors
            config.reset()
            assert config.get_status() == ApiStatus.UNCONFIGURED
    
    def test_error_reporting_rate_limit(self):
        """Test reporting a rate limit error."""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "test-api-key",
            "LLM_API_URL": "https://api.test.com",
            "LLM_MODEL": "test-model"
        }, clear=True):
            config = LLMConfig()
            
            # Initially configured
            assert config.get_status() == ApiStatus.CONFIGURED
            
            # Report a rate limit error
            config.report_error("Rate limit exceeded, try again in 60 seconds")
            
            # Should be in rate limited state
            assert config.get_status() == ApiStatus.RATE_LIMITED
    
    def test_error_auto_recovery(self):
        """Test automatic recovery from error state after timeout."""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "test-api-key",
            "LLM_API_URL": "https://api.test.com",
            "LLM_MODEL": "test-model"
        }, clear=True):
            config = LLMConfig()
            
            # Set a short retry reset time for testing
            config._retry_reset_time = timedelta(seconds=0.1)
            
            # Report an error to enter error state
            for i in range(3):  # Report 3 errors (matching _max_retry_errors)
                config.report_error(f"Error {i}")
            
            # Should be in error state
            assert config.get_status() == ApiStatus.ERROR
            
            # Wait for retry timeout
            import time
            time.sleep(0.2)  # Wait longer than the reset time
            
            # Should auto-recover after timeout
            assert config.get_status() == ApiStatus.CONFIGURED
    
    def test_configuration_summary(self):
        """Test getting a configuration summary."""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "test-api-key",
            "LLM_API_URL": "https://api.test.com",
            "LLM_MODEL": "test-model"
        }, clear=True):
            config = LLMConfig()
            
            summary = config.get_configuration_summary()
            
            assert summary["status"] == "configured"
            assert summary["is_configured"] is True
            assert summary["has_api_key"] is True
            assert summary["has_api_url"] is True
            assert summary["has_model"] is True
            assert summary["error_count"] == 0
            assert summary["last_error"] is None
    
    def test_string_representation(self):
        """Test the string representation."""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "test-api-key",
            "LLM_API_URL": "https://api.test.com",
            "LLM_MODEL": "test-model"
        }, clear=True):
            config = LLMConfig()
            
            string_rep = str(config)
            
            # Should include status but not expose full API key
            assert "status=configured" in string_rep
            assert "api_key=Present" in string_rep
            assert "test-api-key" not in string_rep


def test_is_llm_configured_function():
    """Test the is_llm_configured convenience function."""
    # Test when configured
    with patch('memory_bank.utils.service_config.llm_config.is_configured', return_value=True):
        assert is_llm_configured() is True
    
    # Test when not configured
    with patch('memory_bank.utils.service_config.llm_config.is_configured', return_value=False):
        assert is_llm_configured() is False
