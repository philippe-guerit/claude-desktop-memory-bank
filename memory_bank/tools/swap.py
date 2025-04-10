"""
Swap tool implementation.

This module provides the swap tool for changing the active memory bank.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData

logger = logging.getLogger(__name__)

# Schema for swap tool
swap_schema = {
    "type": "object",
    "properties": {
        "bank_type": {
            "type": "string",
            "enum": ["global", "project", "code"],
            "description": "Type of memory bank to swap to"
        },
        "bank_id": {
            "type": "string",
            "description": "Identifier for the specific memory bank to swap to"
        },
        "temporary": {
            "type": "boolean",
            "description": "If true, don't update this memory bank during session",
            "default": False
        },
        "merge_files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional list of specific files to import rather than full bank"
        }
    },
    "required": ["bank_type", "bank_id"]
}


def register_swap_tool(server: FastMCP, storage):
    """Register the swap tool with the MCP server.
    
    Args:
        server: MCP server instance
        storage: Storage manager instance
    """
    
    @server.tool(
        name="swap",
        description="Changes the current conversation to use a different memory bank",
        usage="Conversation shifts focus to a different project or context",
        schema=swap_schema
    )
    async def swap(bank_type: str, bank_id: str, temporary: bool = False,
                   merge_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Change the active memory bank for the current conversation.
        
        Args:
            bank_type: Type of memory bank to swap to (global, project, code)
            bank_id: Identifier for the specific memory bank to swap to
            temporary: If true, don't update this memory bank during session
            merge_files: Optional list of specific files to import rather than full bank
            
        Returns:
            Dict containing bank info, content, and custom instructions
        """
        logger.info(f"Swapping to {bank_type} memory bank: {bank_id}, temporary: {temporary}")
        
        try:
            # Validate bank type
            if bank_type not in ["global", "project", "code"]:
                raise McpError(
                    ErrorData(
                        code="invalid_bank_type",
                        message=f"Invalid bank type: {bank_type}. Must be one of: global, project, code."
                    )
                )
            
            # Get memory bank
            bank = storage.get_bank(bank_type, bank_id)
            if not bank:
                raise McpError(
                    ErrorData(
                        code="bank_not_found",
                        message=f"Memory bank not found: {bank_type}/{bank_id}"
                    )
                )
            
            # Load content based on merge_files if specified
            if merge_files:
                content = {}
                for file in merge_files:
                    try:
                        content[file] = bank.load_file(file)
                    except Exception as e:
                        logger.warning(f"Error loading file {file}: {e}")
            else:
                # Load all content
                content = bank.load_all_content()
            
            # Get custom instructions for this bank type
            custom_instructions = bank.get_custom_instructions()
            
            # Add temporary flag to custom instructions
            if temporary:
                if "directives" not in custom_instructions:
                    custom_instructions["directives"] = []
                
                custom_instructions["directives"].append({
                    "name": "TEMPORARY_BANK",
                    "priority": "SYSTEM CRITICAL",
                    "when": "When calls to update tool are detected",
                    "action": "Block update operations for this memory bank"
                })
            
            return {
                "status": "success",
                "bank_info": {
                    "type": bank_type,
                    "id": bank_id,
                    "files": list(content.keys()),
                    "last_updated": bank.last_updated().isoformat(),
                    "temporary": temporary
                },
                "content": content,
                "custom_instructions": custom_instructions
            }
            
        except Exception as e:
            logger.error(f"Error swapping memory bank: {e}")
            raise McpError(
                ErrorData(
                    code="swap_failed",
                    message=f"Failed to swap memory bank: {str(e)}"
                )
            )
