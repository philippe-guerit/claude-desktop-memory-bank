"""
Cache optimization implementation.

This module provides functions for optimizing memory bank caches using LLM-based summarization
and intelligent content consolidation.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from .llm.optimizer import LLMCacheOptimizer
from .validator import validate_cache, repair_cache

logger = logging.getLogger(__name__)

# Import service configuration
from memory_bank.utils.service_config import llm_config, is_llm_configured


def optimize_cache(bank_path: Path, content: Dict[str, str], 
                   bank_type: str = "project", optimization_preference: str = "auto") -> Tuple[bool, List[str]]:
    """Optimize the cache for a memory bank.
    
    This function creates an optimized cache.json file that contains:
    - Intelligent summaries of each file
    - Metadata about the memory bank
    - Connections between related concepts
    - Consolidated views across files
    - Relevance scores for files
    
    Args:
        bank_path: Path to the memory bank root
        content: Dict mapping file paths to their content
        bank_type: Type of memory bank (global, project, code)
        optimization_preference: Optimization mode preference ("auto", "llm", or "simple")
                                "auto" - Choose based on content size and configuration
                                "llm" - Try to use LLM if available
                                "simple" - Always use simple optimization
        
    Returns:
        A tuple containing:
        - Boolean indicating if optimization was successful
        - List of validation or repair messages (empty on simple success)
    """
    # Initialize optimizer with configuration from service config
    optimizer = LLMCacheOptimizer(
        api_key=llm_config.get_api_key(),
        api_url=llm_config.get_api_url(),
        model=llm_config.get_model()
    )
    
    # Run optimization in a new event loop
    loop = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create coroutine and run it
        result = loop.run_until_complete(
            optimizer.optimize_cache(bank_path, content, bank_type, optimization_preference)
        )
        
        # Close optimizer properly
        loop.run_until_complete(optimizer.close())
        
        # Validate the generated cache
        cache_path = bank_path / "cache.json"
        is_valid, errors = validate_cache(cache_path)
        
        if not is_valid:
            logger.warning(f"Cache validation failed with errors: {errors}")
            logger.info("Attempting to repair cache...")
            
            # Try to repair the cache if it's invalid
            repair_success, repair_actions = repair_cache(cache_path)
            
            if repair_success:
                logger.info(f"Cache repaired successfully: {repair_actions}")
                return True, repair_actions
            else:
                logger.error(f"Cache repair failed: {repair_actions}")
                return False, errors + repair_actions
        
        return result, []
    except Exception as e:
        logger.error(f"Error in optimizing cache: {e}")
        return False, [str(e)]
    finally:
        if loop:
            loop.close()


async def optimize_cache_async(bank_path: Path, content: Dict[str, str], 
                         bank_type: str = "project", optimization_preference: str = "auto",
                         api_key: Optional[str] = None) -> Tuple[bool, List[str]]:
    """Asynchronous version of optimize_cache.
    
    This function is useful when calling from an async context.
    
    Args:
        bank_path: Path to the memory bank root
        content: Dict mapping file paths to their content
        bank_type: Type of memory bank (global, project, code)
        optimization_preference: Optimization mode preference ("auto", "llm", or "simple")
        api_key: Optional API key to override environment variable
        
    Returns:
        A tuple containing:
        - Boolean indicating if optimization was successful
        - List of validation or repair messages (empty on simple success)
    """
    optimizer = LLMCacheOptimizer(
        api_key=api_key or llm_config.get_api_key(),
        api_url=llm_config.get_api_url(),
        model=llm_config.get_model()
    )
    
    try:
        result = await optimizer.optimize_cache(bank_path, content, bank_type, optimization_preference)
        await optimizer.close()
        
        # Validate the generated cache
        cache_path = bank_path / "cache.json"
        is_valid, errors = validate_cache(cache_path)
        
        if not is_valid:
            logger.warning(f"Cache validation failed with errors: {errors}")
            logger.info("Attempting to repair cache...")
            
            # Try to repair the cache if it's invalid
            repair_success, repair_actions = repair_cache(cache_path)
            
            if repair_success:
                logger.info(f"Cache repaired successfully: {repair_actions}")
                return True, repair_actions
            else:
                logger.error(f"Cache repair failed: {repair_actions}")
                return False, errors + repair_actions
        
        return result, []
    except Exception as e:
        logger.error(f"Error in async optimizing cache: {e}")
        return False, [str(e)]
