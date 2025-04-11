"""
Service Configuration Manager.

This module provides central configuration management for various services
used by the memory bank system, including LLM API integration.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Load .env file once at module import
from dotenv import load_dotenv
env_path = Path(__file__).parents[2] / '.env'
load_dotenv(dotenv_path=env_path)


class ApiStatus(Enum):
    """Possible states for an API service."""
    CONFIGURED = "configured"  # API is properly configured
    UNCONFIGURED = "unconfigured"  # API lacks necessary configuration
    RATE_LIMITED = "rate_limited"  # API is temporarily unavailable due to rate limiting
    ERROR = "error"  # API is experiencing errors


class LLMConfig:
    """Configuration manager for LLM API access.
    
    This class centralizes all LLM configuration validation, status tracking,
    and access control to ensure consistent handling of API credentials and state.
    """
    
    def __init__(self):
        """Initialize the LLM configuration manager."""
        # Core configuration fields
        self._api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self._api_url = os.environ.get("LLM_API_URL", "")
        self._model = os.environ.get("LLM_MODEL", "")
        
        # Status tracking
        self._status = self._determine_initial_status()
        self._last_error: Optional[str] = None
        self._error_time: Optional[datetime] = None
        self._error_count = 0
        self._max_retry_errors = 3
        self._retry_reset_time = timedelta(minutes=10)
        
    def _determine_initial_status(self) -> ApiStatus:
        """Determine the initial status based on configuration."""
        if not self._api_key or not self._api_url or not self._model:
            logger.warning("LLM API not fully configured")
            return ApiStatus.UNCONFIGURED
        return ApiStatus.CONFIGURED

    def is_configured(self) -> bool:
        """Check if the LLM API is properly configured.
        
        Returns:
            True if all required LLM configuration is available, False otherwise
        """
        return self._status == ApiStatus.CONFIGURED
    
    def get_api_key(self) -> str:
        """Get the API key if the service is properly configured.
        
        Returns:
            API key string if configured, empty string otherwise
        """
        if self.is_configured():
            return self._api_key
        return ""
    
    def get_api_url(self) -> str:
        """Get the API URL if the service is properly configured.
        
        Returns:
            API URL string if configured, empty string otherwise
        """
        if self.is_configured():
            return self._api_url
        return ""
    
    def get_model(self) -> str:
        """Get the model name if the service is properly configured.
        
        Returns:
            Model name string if configured, empty string otherwise
        """
        if self.is_configured():
            return self._model
        return ""
    
    def get_status(self) -> ApiStatus:
        """Get the current status of the LLM API service.
        
        Returns:
            Current API status enum value
        """
        # Check for automatic retry reset
        if (self._status == ApiStatus.ERROR or self._status == ApiStatus.RATE_LIMITED) and \
           self._error_time is not None:
            # If enough time has passed since the last error, reset to configured
            if datetime.now() - self._error_time > self._retry_reset_time:
                logger.info("Resetting LLM API status after retry timeout")
                self._status = ApiStatus.CONFIGURED
                self._error_count = 0
                self._last_error = None
                self._error_time = None
                
        return self._status
    
    def report_error(self, error: str, is_permanent: bool = False) -> None:
        """Report an error with the LLM API.
        
        This updates the status based on the error type and tracks error frequency.
        
        Args:
            error: Error message or description
            is_permanent: If True, marks this as a permanent configuration error
        """
        self._last_error = error
        self._error_time = datetime.now()
        
        if is_permanent or "authentication" in error.lower() or "authorization" in error.lower():
            # Authentication errors indicate a permanent configuration issue
            logger.error(f"Permanent LLM API configuration error: {error}")
            self._status = ApiStatus.UNCONFIGURED
        elif "rate limit" in error.lower() or "429" in error:
            # Rate limit errors are temporary but require backing off
            logger.warning(f"LLM API rate limited: {error}")
            self._status = ApiStatus.RATE_LIMITED
            self._error_count += 1
        else:
            # Other errors might be temporary
            self._error_count += 1
            logger.error(f"LLM API error ({self._error_count}/{self._max_retry_errors}): {error}")
            
            # If we've had too many errors in a row, consider the service unavailable
            if self._error_count >= self._max_retry_errors:
                logger.error("Too many LLM API errors, marking as error state")
                self._status = ApiStatus.ERROR
    
    def reset(self) -> None:
        """Reset error state and retry counters.
        
        This can be called when conditions have changed (e.g., network connectivity restored).
        """
        if self._status != ApiStatus.UNCONFIGURED:
            self._status = ApiStatus.CONFIGURED
            self._error_count = 0
            self._last_error = None
            self._error_time = None
            logger.info("LLM API status manually reset")
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration state.
        
        Returns:
            Dictionary with configuration summary
        """
        return {
            "status": self._status.value,
            "is_configured": self.is_configured(),
            "has_api_key": bool(self._api_key),
            "has_api_url": bool(self._api_url),
            "has_model": bool(self._model),
            "error_count": self._error_count,
            "last_error": self._last_error,
            "last_error_time": self._error_time.isoformat() if self._error_time else None
        }
    
    def __str__(self) -> str:
        """String representation of the configuration.
        
        Returns:
            String summary of configuration state
        """
        masked_key = f"{self._api_key[:4]}...{self._api_key[-4:]}" if self._api_key and len(self._api_key) > 8 else None
        return (f"LLMConfig(status={self._status.value}, "
                f"api_key={'Present' if self._api_key else 'Missing'}, "
                f"api_url={self._api_url or 'Missing'}, "
                f"model={self._model or 'Missing'})")


# Create a singleton instance for use throughout the application
llm_config = LLMConfig()


# Convenience function for checking if LLM is available
def is_llm_configured() -> bool:
    """Check if the LLM API is properly configured.
    
    Returns:
        True if LLM API is properly configured, False otherwise
    """
    return llm_config.is_configured()
