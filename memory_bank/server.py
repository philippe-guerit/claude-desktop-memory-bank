"""
MCP server implementation for Claude Desktop Memory Bank.

This module provides the main MCP server implementation for the memory bank.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, TextContent

logger = logging.getLogger(__name__)


class MemoryBankServer:
    """MCP server for Claude Desktop Memory Bank."""
    
    def __init__(self, storage_root: Optional[Path] = None):
        """Initialize the memory bank server.
        
        Args:
            storage_root: Path to the storage directory. If None, uses ~/.claude-desktop/memory/
        """
        # Import here to avoid circular imports
        from .tools.activate import register_activate_tool
        from .tools.list import register_list_tool
        from .tools.swap import register_swap_tool
        from .tools.update import register_update_tool
        from .storage.manager import StorageManager
        
        self.server = FastMCP(
            name="Claude Desktop Memory Bank",
            version="2.0.0",
            description="MCP server for managing conversation context across sessions"
        )
        
        # Initialize storage
        self.storage_root = storage_root or Path.home() / ".claude-desktop" / "memory"
        self.storage = StorageManager(self.storage_root)
        
        # Register tools
        register_activate_tool(self.server, self.storage)
        register_list_tool(self.server, self.storage)
        register_swap_tool(self.server, self.storage)
        register_update_tool(self.server, self.storage)
        
        # For test mode
        self.mock_transport = None
        
        logger.info(f"Memory Bank Server initialized with storage at {self.storage_root}")
    
    async def start(self, test_mode: bool = False):
        """Start the MCP server.
        
        Args:
            test_mode: If True, use a mock transport instead of stdio.
        """
        if test_mode:
            logger.info("Starting Memory Bank MCP Server in test mode...")
            # Import mock transport from tests package
            import sys
            from tests.test_utils.test_transport.mock_transport import MockTransport
            
            # Create a mock transport for testing
            self.mock_transport = MockTransport()
            
            # Call tools directly in test mode
            logger.info("Server ready for direct tool calls in test mode")
        else:
            logger.info("Starting Memory Bank MCP Server using stdio transport...")
            try:
                await self.server.run_stdio_async()
            except Exception as e:
                logger.error(f"Error starting server with stdio: {e}")
                raise
    
    async def stop(self):
        """Stop the MCP server."""
        logger.info("Stopping Memory Bank MCP Server...")
        # Currently no additional cleanup needed
    
    async def call_tool_test(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Call a tool directly for testing, bypassing transport.
        
        Args:
            tool_name: The name of the tool to call.
            params: The parameters to pass to the tool.
            
        Returns:
            The tool response.
        """
        if self.mock_transport is None:
            raise RuntimeError("Server not started in test mode")
        
        # Call the tool handler directly
        from mcp.types import TextContent
        
        try:
            # Call the tool through the FastMCP API
            result = await self.server.call_tool(tool_name, params)
            
            # Convert to dict for consistent response format
            if isinstance(result, list) and len(result) > 0 and isinstance(result[0], TextContent):
                try:
                    return json.loads(result[0].text)
                except json.JSONDecodeError:
                    # If not valid JSON, return as is
                    return result
            
            return result
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise
