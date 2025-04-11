"""
Update tool implementation.

This module provides the update tool for updating memory banks.
"""

from typing import Dict, Any, Optional
import logging

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData

logger = logging.getLogger(__name__)

# Schema for update tool
update_schema = {
    "type": "object",
    "properties": {
        "bank_type": {
            "type": "string",
            "enum": ["global", "project", "code"],
            "description": "Type of memory bank to update"
        },
        "bank_id": {
            "type": "string",
            "description": "Identifier for the specific memory bank to update"
        },
        "target_file": {
            "type": "string",
            "description": "Specific file to update (e.g., 'doc/design.md')"
        },
        "operation": {
            "type": "string",
            "enum": ["append", "replace", "insert"],
            "description": "How to apply the update"
        },
        "content": {
            "type": "string",
            "description": "Content to add to the memory bank"
        },
        "position": {
            "type": "string",
            "description": "Position identifier for insert operations (e.g., section name)"
        },
        "trigger_type": {
            "type": "string",
            "enum": ["watchdog", "architecture", "technology", "progress", "commit", "user_request"],
            "description": "What triggered this update"
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
    "required": ["bank_type", "bank_id", "target_file", "operation", "content"]
}


def register_update_tool(server: FastMCP, storage):
    """Register the update tool with the MCP server.
    
    Args:
        server: MCP server instance
        storage: Storage manager instance
    """
    
    @server.tool(
        name="update",
        description="Updates the memory bank with new information from the conversation"
    )
    async def update(bank_type: str, bank_id: str, target_file: str, operation: str, content: str,
                     position: Optional[str] = None, trigger_type: Optional[str] = None,
                     conversation_id: Optional[str] = None, update_count: Optional[int] = None) -> Dict[str, Any]:
        """Update a memory bank with new information.
        
        Args:
            bank_type: Type of memory bank to update (global, project, code)
            bank_id: Identifier for the specific memory bank to update
            target_file: Specific file to update (e.g., 'doc/design.md')
            operation: How to apply the update (replace, append, insert)
            content: Content to add to the memory bank
            position: Position identifier for insert operations (e.g., section name)
            trigger_type: What triggered this update
            conversation_id: Identifier for the current conversation
            update_count: Counter for updates in this conversation
            
        Returns:
            Dict containing update status and information
        """
        logger.info(f"Updating {bank_type} memory bank: {bank_id}, file: {target_file}, operation: {operation}")
        
        try:
            # Get memory bank
            bank = storage.get_bank(bank_type, bank_id)
            if not bank:
                raise McpError(
                    ErrorData(
                        code=404,  # Not Found
                        message=f"Memory bank not found: {bank_type}/{bank_id}"
                    )
                )
            
            # Validate operation
            if operation not in ["append", "replace", "insert"]:
                raise McpError(
                    ErrorData(
                        code=400,  # Bad Request
                        message=f"Invalid operation: {operation}. Must be one of: append, replace, insert."
                    )
                )
            
            # Add context to content if extra metadata is provided
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
            
            # Update the file
            success = bank.update_file(target_file, content, operation, position)
            if not success:
                raise McpError(
                    ErrorData(
                        code=500,  # Internal Server Error
                        message=f"Failed to update file: {target_file}"
                    )
                )
            
            # Generate verification string
            verification = f"// Update #{update_count or 'N/A'} for conversation {conversation_id or 'unknown'}"
            
            # Determine if we should perform LLM optimization on this update
            cache_optimized = False
            optimize_with_llm = False
            
            # Optimization triggers
            if trigger_type in ["architecture", "technology", "progress"]:
                # Important updates should trigger LLM optimization
                optimize_with_llm = True
                logger.info(f"Triggering LLM optimization due to {trigger_type} update")
            elif update_count and update_count % 5 == 0:
                # Periodic optimization every 5 updates
                optimize_with_llm = True
                logger.info("Triggering periodic LLM optimization")
                
            # Perform optimization if needed
            if optimize_with_llm:
                # Get all content for optimization
                all_content = bank.load_all_content()
                
                # Get bank type
                bank_type = bank.__class__.__name__.replace("MemoryBank", "").lower()
                
                # Import here to avoid circular imports
                from memory_bank.cache.optimizer import optimize_cache
                result, messages = optimize_cache(bank.root_path, all_content, bank_type, optimization_preference="llm")
                
                if result:
                    logger.info(f"Successfully optimized cache for {bank_type}/{bank.bank_id}")
                else:
                    logger.warning(f"Failed to optimize cache for {bank_type}/{bank.bank_id}")
            
            return {
                "status": "success",
                "updated_file": target_file,
                "operation": operation,
                "cache_updated": True,
                "cache_optimized": cache_optimized,
                "trigger_type": trigger_type,
                "verification": verification,
                "next_actions": []
            }
            
        except Exception as e:
            logger.error(f"Error updating memory bank: {e}")
            raise McpError(
                ErrorData(
                    code=500,  # Internal Server Error
                    message=f"Failed to update memory bank: {str(e)}"
                )
            )
