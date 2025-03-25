"""
Core business logic for context management.

This module contains pure, framework-agnostic functions for
managing context data, independent of the FastMCP integration.
"""

from typing import Dict, List, Optional, Any

async def get_context(context_service, context_type: str) -> str:
    """Core logic for getting a specific context file.
    
    Args:
        context_service: The context service instance
        context_type: The type of context to get
        
    Returns:
        Content of the context file
    """
    return await context_service.get_context(context_type)

async def update_context(
    context_service,
    context_type: str,
    content: str
) -> Dict[str, Any]:
    """Core logic for updating a context file in the current memory bank.
    
    Args:
        context_service: The context service instance
        context_type: The type of context to update
        content: The new content for the context file
        
    Returns:
        Dictionary with memory bank information
    """
    return await context_service.update_context(context_type, content)


async def bulk_update_context(
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

async def auto_summarize_context(
    context_service,
    conversation_text: str
) -> Dict[str, str]:
    """Core logic for automatically extracting and updating context.
    
    Args:
        context_service: The context service instance
        conversation_text: Text of the conversation to summarize
        
    Returns:
        Dictionary of suggested context updates by context type
    """
    return await context_service.auto_summarize_context(conversation_text)

async def prune_context(
    context_service,
    max_age_days: int = 90
) -> Dict[str, Any]:
    """Core logic for removing outdated information from context files.
    
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
