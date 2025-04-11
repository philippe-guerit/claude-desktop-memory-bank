"""
Entry point for the Claude Desktop Memory Bank.

This module provides the main entry point for running the memory bank server.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from .patches import apply_patches
from .server import MemoryBankServer

# Apply patches to third-party libraries
apply_patches()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


async def main():
    """Run the memory bank server."""
    logger.info("Starting Claude Desktop Memory Bank...")
    
    # Get storage root from environment or use default
    storage_root = os.environ.get("MEMORY_BANK_ROOT")
    if storage_root:
        storage_root = Path(storage_root)
    else:
        storage_root = Path.home() / ".claude-desktop" / "memory"
    
    # Create server
    server = MemoryBankServer(storage_root=storage_root)
    
    try:
        # Start server - this will block until terminated
        await server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        raise
    finally:
        # Ensure server is stopped
        await server.stop()
        logger.info("Server stopped.")


if __name__ == "__main__":
    asyncio.run(main())
