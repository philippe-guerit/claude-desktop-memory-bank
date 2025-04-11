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
from typing import Dict, Any, Optional

from .llm.optimizer import LLMCacheOptimizer

logger = logging.getLogger(__name__)

# Load .env file
from dotenv import load_dotenv
from pathlib import Path

# Try to load from memory_bank/.env
env_path = Path(__file__).parents[2] / '.env'
load_dotenv(dotenv_path=env_path)

# Environment variables for LLM configuration (must be explicitly set)
LLM_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
LLM_API_URL = os.environ.get("LLM_API_URL", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "")


def optimize_cache(bank_path: Path, content: Dict[str, str], 
                   bank_type: str = "project", force_llm: bool = False) -> bool:
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
        force_llm: Force using LLM even for small content
        
    Returns:
        True if optimization was successful, False otherwise
    """
    optimizer = LLMCacheOptimizer(api_key=LLM_API_KEY, api_url=LLM_API_URL, model=LLM_MODEL)
    
    # Run optimization in a new event loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(optimizer.optimize_cache(bank_path, content, bank_type, force_llm))
        loop.run_until_complete(optimizer.close())
        return result
    except Exception as e:
        logger.error(f"Error in optimizing cache: {e}")
        return False
    finally:
        loop.close()


async def optimize_cache_async(bank_path: Path, content: Dict[str, str], 
                         bank_type: str = "project", force_llm: bool = False,
                         api_key: Optional[str] = None) -> bool:
    """Asynchronous version of optimize_cache.
    
    This function is useful when calling from an async context.
    
    Args:
        bank_path: Path to the memory bank root
        content: Dict mapping file paths to their content
        bank_type: Type of memory bank (global, project, code)
        force_llm: Force using LLM even for small content
        api_key: Optional API key to override environment variable
        
    Returns:
        True if optimization was successful, False otherwise
    """
    optimizer = LLMCacheOptimizer(api_key=api_key or LLM_API_KEY, 
                                  api_url=LLM_API_URL, 
                                  model=LLM_MODEL)
    
    try:
        result = await optimizer.optimize_cache(bank_path, content, bank_type, force_llm)
        await optimizer.close()
        return result
    except Exception as e:
        logger.error(f"Error in async optimizing cache: {e}")
        return False
