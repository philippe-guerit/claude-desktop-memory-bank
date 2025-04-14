"""
Content processor factory for memory bank.

Provides a factory function to get the appropriate content processor based on
configuration and availability.
"""

import logging
from typing import Optional, Union, Dict, Any

from .base_processor import ContentProcessor
from .rule_processor import RuleBasedProcessor
from .llm import LLMProcessor
from memory_bank.utils.service_config import llm_config, is_llm_configured, ApiStatus

logger = logging.getLogger(__name__)


def get_content_processor(processor_preference: str = "auto",
                       api_key: Optional[str] = None,
                       api_url: Optional[str] = None,
                       model: Optional[str] = None) -> ContentProcessor:
    """Get the appropriate content processor based on preference and availability.
    
    Args:
        processor_preference: Processor preference: "auto", "llm", or "rule"
        api_key: API key for LLM service (default: from service_config)
        api_url: URL for LLM API (default: from service_config)
        model: LLM model to use (default: from service_config)
        
    Returns:
        ContentProcessor implementation (LLMProcessor or RuleBasedProcessor)
    """
    # Create a rule-based processor - we'll use this either directly or as a fallback
    rule_processor = RuleBasedProcessor()
    
    # Check if LLM is explicitly requested
    if processor_preference == "rule":
        logger.info("Using rule-based processor (explicitly requested)")
        return rule_processor
        
    # Check if LLM is available
    llm_status = llm_config.get_status()
    if not is_llm_configured() or (hasattr(llm_status, 'value') and llm_status.value != 'CONFIGURED') and llm_status != 'CONFIGURED' and llm_status != ApiStatus.CONFIGURED:
        # If LLM was explicitly requested but is not available, log a warning
        if processor_preference == "llm":
            logger.warning("LLM processor was requested but LLM is not properly configured or unavailable")
            status_value = llm_status.value if hasattr(llm_status, 'value') else str(llm_status)
            logger.warning(f"Current LLM status: {status_value}")
        
        logger.info("Using rule-based processor (LLM not available)")
        return rule_processor
        
    # If we get here, LLM is available
    if processor_preference in ["auto", "llm"]:
        logger.info("Using LLM processor")
        return LLMProcessor(api_key, api_url, model)
    
    # Fallback to rule-based processor for any other preference
    logger.info(f"Using rule-based processor (unrecognized preference: {processor_preference})")
    return rule_processor
