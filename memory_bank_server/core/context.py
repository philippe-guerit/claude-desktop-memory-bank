"""
Core business logic for context management.

This module contains pure, framework-agnostic functions for
managing context data, independent of the FastMCP integration.
"""

import re
from typing import Dict, List, Optional, Any, Tuple, Union

async def update(
    context_service,
    updates: Dict[str, Union[str, Dict[str, str]]]
) -> Dict[str, Any]:
    """Core logic for updating multiple context files at once.
    
    Args:
        context_service: The context service instance
        updates: Dictionary mapping context types to either:
                - Complete new content (string)
                - Section updates (Dict[section_header, new_content])
        
    Returns:
        Dictionary with memory bank information
    """
    # Process updates, handling both full file and section-specific updates
    processed_updates = {}
    
    for context_type, update_content in updates.items():
        # If update is a string, it's a full file update
        if isinstance(update_content, str):
            processed_updates[context_type] = update_content
        # If update is a dict, it's a section update
        elif isinstance(update_content, dict):
            # Get current content
            try:
                current_content = await context_service.get_context(context_type)
                # Apply section updates to current content
                new_content = await _update_sections(current_content, update_content)
                processed_updates[context_type] = new_content
            except Exception as e:
                # If getting current content fails, raise error
                raise ValueError(f"Error processing section update for {context_type}: {str(e)}")
    
    # Apply all updates at once
    return await context_service.bulk_update_context(processed_updates)

async def _update_sections(content: str, section_updates: Dict[str, str]) -> str:
    """Update specific sections within content.
    
    Args:
        content: Current file content
        section_updates: Dictionary mapping section headers to new content
        
    Returns:
        Updated content with modified sections
    """
    for section_header, new_section_content in section_updates.items():
        # Find the section in the content
        section_pattern = re.compile(f"(#+\\s*{re.escape(section_header)}.*?)(?:^#+\\s*|$)", re.MULTILINE | re.DOTALL)
        
        match = section_pattern.search(content)
        if match:
            # Found the section, now get the next section (if any)
            start_pos = match.start()
            # Get the header part (e.g., "## Section Name")
            header_end = content.find('\n', start_pos)
            if header_end == -1:  # No newline found
                header_end = len(content)
            header_part = content[start_pos:header_end]
            
            # Replace section content while preserving the header
            content = (
                content[:start_pos] + 
                header_part + "\n\n" + 
                new_section_content + "\n\n" + 
                content[match.end():]
            )
        else:
            # Section not found, append it at the end
            # Determine heading level (default to ##)
            heading_level = "##"
            if section_header.strip() and section_header.strip()[0] == '#':
                # Section header already includes # symbols
                pass
            else:
                # Add the heading level
                section_header = f"{heading_level} {section_header}"
            
            # Append new section
            if not content.endswith('\n'):
                content += '\n'
            content += f"\n{section_header}\n\n{new_section_content}\n"
    
    return content

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


