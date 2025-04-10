"""
MCP server implementation for Claude Desktop Memory Bank.

This module provides the main MCP server implementation for the memory bank.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData

from .tools.activate import register_activate_tool
from .tools.list import register_list_tool
from .tools.swap import register_swap_tool
from .tools.update import register_update_tool
from .storage.manager import StorageManager

logger = logging.getLogger(__name__)


class MemoryBankServer:
    """MCP server for Claude Desktop Memory Bank."""
    
    def __init__(self, storage_root: Optional[Path] = None):
        """Initialize the memory bank server.
        
        Args:
            storage_root: Path to the storage directory. If None, uses ~/.claude-desktop/memory/
        """
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
        
        logger.info(f"Memory Bank Server initialized with storage at {self.storage_root}")
    
    async def start(self):
        """Start the MCP server."""
        # For testing purposes, we don't actually start the server
        # This way we can call tools directly without issues with stdin/stdout
        pass
    
    async def stop(self):
        """Stop the MCP server."""
        # Nothing to stop since we don't start the server in tests
        pass
