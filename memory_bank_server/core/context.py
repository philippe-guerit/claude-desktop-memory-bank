"""
Core business logic for context management.

This module contains pure, framework-agnostic functions for
managing context data, independent of the FastMCP integration.
"""

from typing import Dict, List, Optional, Any

async def update(
    context_service,
    updates: Dict[str, str]
) -> Dict[str, Any]:
    """Core logic for updating multiple context files at once.
    
    Args:
        context_service: The context service instance
        updates: Dictionary mapping context types to content
        
    Returns:
        Dictionary with memory bank information
    """
    return await context_service.bulk_update_context(updates)

async def get_context(context_service, context_type: str) -> str:
    """Core logic for getting a specific context file.
    
    Args:
        context_service: The context service instance
        context_type: The type of context to get
        
    Returns:
        Content of the context file
    """
    return await context_service.get_context(context_type)




# Internal helper function for pruning - used by memory-bank-start internally
async def _prune_context_internal(
    context_service,
    max_age_days: int = 90
) -> Dict[str, Any]:
    """Internal helper for pruning context.
    Not exposed as a tool - used by memory-bank-start.
    
    Args:
        context_service: The context service instance
        max_age_days: Maximum age of content to retain (in days)
        
    Returns:
        Dictionary with pruning results
    """
    return await context_service.prune_context(max_age_days)

async def get_all_context(context_service) -> Dict[str, str]:
    """Core logic for getting all context files.
    
    Args:
        context_service: The context service instance
        
    Returns:
        Dictionary mapping context types to content
    """
    return await context_service.get_all_context()

async def get_memory_bank_info(context_service) -> Dict[str, Any]:
    """Core logic for getting information about the current memory bank.
    
    Args:
        context_service: The context service instance
        
    Returns:
        Dictionary with memory bank information
    """
    current_memory_bank = await context_service.get_current_memory_bank()
    all_memory_banks = await context_service.get_memory_banks()
    
    return {
        "current": current_memory_bank,
        "all": all_memory_banks
    }


