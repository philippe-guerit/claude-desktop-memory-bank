#!/usr/bin/env python3
"""
Wrapper script for the Claude Desktop Memory Bank MCP server.
This exposes the server for use with the MCP Inspector tool.
"""

import asyncio
import logging
import sys
from pathlib import Path
from memory_bank.server import MemoryBankServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting run_server.py wrapper...")
    
    # Create and configure the server
    storage_root = Path.home() / ".claude-desktop" / "memory"
    logger.info(f"Using storage root: {storage_root}")
    
    # Create server
    mcp_server = MemoryBankServer(storage_root=storage_root)
    
    # Start the server using the standardized start method
    logger.info("Starting server using start() method...")
    await mcp_server.start()

if __name__ == "__main__":
    asyncio.run(main())
