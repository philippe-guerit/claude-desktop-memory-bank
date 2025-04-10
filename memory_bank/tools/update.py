"""
Update tool implementation.

This module provides the update tool for updating memory banks.
"""

from typing import Dict, Any, Optional
import logging

from mcp import MCPServer
from mcp.errors import MCPError

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


def register_update_tool(server: MCPServer, storage):
    """Register the update tool with the MCP server.
    
    Args:
        server: MCP server instance
        storage: Storage manager instance
    """
    
    @server.tool(
        id="update",
        description="Updates the memory bank with new information from the conversation",
        use_when="Significant new information is discussed that should be persisted",
        parameters=update_schema
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
                raise MCPError(
                    code="bank_not_found",
                    message=f"Memory bank not found: {bank_type}/{bank_id}"
                )
            
            # Validate operation
            if operation not in ["append", "replace", "insert"]:
                raise MCPError(
                    code="invalid_operation",
                    message=f"Invalid operation: {operation}. Must be one of: append, replace, insert."
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
                raise MCPError(
                    code="update_failed",
                    message=f"Failed to update file: {target_file}"
                )
            
            # Generate verification string
            verification = f"// Update #{update_count or 'N/A'} for conversation {conversation_id or 'unknown'}"
            
            return {
                "status": "success",
                "updated_file": target_file,
                "operation": operation,
                "cache_updated": True,
                "cache_optimized": False,  # Cache optimization would be done periodically, not every update
                "verification": verification,
                "next_actions": []
            }
            
        except Exception as e:
            logger.error(f"Error updating memory bank: {e}")
            raise MCPError(
                code="update_failed",
                message=f"Failed to update memory bank: {str(e)}"
            )
