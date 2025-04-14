"""
Update tool implementation.

This module provides the update tool for updating memory banks with automatic content analysis
and in-memory cache integration.
"""

from typing import Dict, Any, Optional
import logging

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData

from memory_bank.content import ContentAnalyzer
from memory_bank.cache_manager.cache_manager import CacheManager

logger = logging.getLogger(__name__)

# Schema for update tool
update_schema = {
    "type": "object",
    "properties": {
        "content": {
            "type": "string",
            "description": "The conversation content to store"
        },
        "conversation_id": {
            "type": "string",
            "description": "Identifier for the current conversation"
        },
        "update_count": {
            "type": "integer",
            "description": "Counter for updates in this conversation"
        }
    },
    "required": ["content"]
}


def register_update_tool(server: FastMCP, storage):
    """Register the update tool with the MCP server.
    
    Args:
        server: MCP server instance
        storage: Storage manager instance
    """
    
    # Get the cache manager singleton instance
    cache_manager = CacheManager.get_instance()
    
    @server.tool(
        name="update",
        description="Updates memory with conversation content"
    )
    async def update(content: str, 
                     conversation_id: Optional[str] = None, 
                     update_count: Optional[int] = None) -> Dict[str, Any]:
        """Update memory with conversation content.
        
        Args:
            content: The conversation content to store
            conversation_id: Identifier for the current conversation
            update_count: Counter for updates in this conversation
            
        Returns:
            Dict containing update status and information
        """
        logger.info(f"Updating memory with conversation content")
        
        try:
            # Get the currently active memory bank information from storage
            bank_type, bank_id = _get_active_bank_info(storage)
            logger.info(f"Using {bank_type} memory bank: {bank_id}")
            
            # Analyze content to determine target file and operation using ContentAnalyzer
            # This maintains compatibility with existing content processing
            analysis = ContentAnalyzer.determine_target_file(bank_type, content)
            target_file = analysis["target_file"]
            operation = analysis["operation"]
            position = analysis["position"]
            category = analysis["category"]
            
            # Create a trigger type based on the content category
            trigger_type = category if category != "default" else "watchdog"
            
            # Add context to content if extra metadata is provided
            # This maintains compatibility with existing content processing
            if trigger_type or conversation_id or update_count:
                # Add a footer with metadata
                footer = "\n\n"
                if trigger_type:
                    footer += f"Trigger: {trigger_type}\n"
                if conversation_id:
                    footer += f"Conversation: {conversation_id}\n"
                if update_count:
                    footer += f"Update: {update_count}\n"
                
                # Add verification line for custom instructions
                footer += f"\n// Update #{update_count or 'N/A'} for conversation {conversation_id or 'unknown'}"
                
                # Append footer to content
                content += footer
            
            # Process with content analyzer to get structured format
            processed_content = {target_file: content}
            
            # Determine if this is a high-priority update that requires immediate sync
            immediate_sync = category in ["architecture", "technology", "progress"]
            
            # Update the in-memory cache using the cache manager
            # This is the central change from Phase 3 implementation
            result = cache_manager.update_bank(
                bank_type, 
                bank_id, 
                content,
                immediate_sync=immediate_sync
            )
            
            # If update failed, raise an error
            if result["status"] == "error":
                raise Exception(result.get("error", "Unknown error updating memory bank"))
            
            # Generate verification string
            verification = f"// Update #{update_count or 'N/A'} for conversation {conversation_id or 'unknown'}"
            
            # Determine if we should perform LLM optimization on this update
            cache_optimized = False
            optimize_with_llm = False
            
            # Optimization triggers
            if category in ["architecture", "technology", "progress"]:
                # Important updates should trigger LLM optimization
                optimize_with_llm = True
                logger.info(f"Triggering LLM optimization due to {category} update")
            elif update_count and update_count % 5 == 0:
                # Periodic optimization every 5 updates
                optimize_with_llm = True
                logger.info("Triggering periodic LLM optimization")
                
            # Perform optimization if needed
            # Note: In a future phase, this can be moved into the CacheManager
            if optimize_with_llm:
                # Import here to avoid circular imports
                from memory_bank.cache.optimizer import optimize_cache_async
                
                # Get bank to get root path and content
                bank = storage.get_bank(bank_type, bank_id)
                if bank:
                    all_content = bank.load_all_content()
                    optimization_result, messages = await optimize_cache_async(
                        bank.root_path, all_content, bank_type, optimization_preference="llm"
                    )
                    
                    if optimization_result:
                        logger.info(f"Successfully optimized cache for {bank_type}/{bank_id}")
                        cache_optimized = True
                    else:
                        logger.warning(f"Failed to optimize cache for {bank_type}/{bank_id}")
            
            # Include any previous errors in the response
            previous_errors = cache_manager.get_error_history()
            
            # Return results with backward-compatible structure
            return {
                "status": "success",
                "bank_info": {
                    "type": bank_type,
                    "id": bank_id
                },
                "updated_file": target_file,
                "operation": operation,
                "category": category,
                "confidence": analysis["confidence"],
                "cache_updated": True,
                "cache_optimized": cache_optimized,
                "verification": verification,
                "previous_errors": previous_errors
            }
            
        except Exception as e:
            logger.error(f"Error updating memory bank: {e}")
            raise McpError(
                ErrorData(
                    code=500,  # Internal Server Error
                    message=f"Failed to update memory: {str(e)}"
                )
            )

def _get_active_bank_info(storage) -> tuple:
    """Helper function to get active bank type and ID.
    
    Args:
        storage: Storage manager instance
        
    Returns:
        Tuple of (bank_type, bank_id)
    """
    # Look for the first memory bank that was activated
    active_banks = []
    for bank_type in ["global", "project", "code"]:
        active_banks.extend(storage.active_banks.get(bank_type, {}).values())
    
    if not active_banks:
        # Default to global memory bank
        logger.warning("No active memory bank found, using global default")
        bank = storage.get_bank("global", "default")
        if not bank:
            bank = storage.create_bank("global", "default")
    else:
        # Use the first active bank
        bank = active_banks[0]
    
    # Get bank type and ID
    bank_type = bank.__class__.__name__.replace("MemoryBank", "").lower()
    bank_id = bank.bank_id
    
    return bank_type, bank_id
