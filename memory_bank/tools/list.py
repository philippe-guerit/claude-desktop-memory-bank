"""
List tool implementation.

This module provides the list tool for listing available memory banks.
"""

from typing import Dict, Any, Optional
import logging

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData

logger = logging.getLogger(__name__)

# Schema for list tool
list_schema = {
    "type": "object",
    "properties": {
        "bank_type": {
            "type": "string",
            "enum": ["global", "project", "code"],
            "description": "Optional type filter for banks to list"
        }
    }
}


def register_list_tool(server: FastMCP, storage):
    """Register the list tool with the MCP server.
    
    Args:
        server: MCP server instance
        storage: Storage manager instance
    """
    
    @server.tool(
        id="list",
        description="Lists all available memory banks by type",
        use_when="User wants to see available memory banks or choose which to use",
        schema=list_schema
    )
    async def list_banks(bank_type: Optional[str] = None) -> Dict[str, Any]:
        """List all available memory banks.
        
        Args:
            bank_type: Optional type filter (global, project, code)
            
        Returns:
            Dict mapping bank types to lists of bank info
        """
        logger.info(f"Listing memory banks, filter: {bank_type}")
        
        try:
            # Get banks from storage manager
            banks = storage.list_banks(bank_type)
            
            return banks
            
        except Exception as e:
            logger.error(f"Error listing memory banks: {e}")
            raise McpError(
                ErrorData(
                    code="list_failed",
                    message=f"Failed to list memory banks: {str(e)}"
                )
            )
