#!/usr/bin/env python3
"""
Run script for the Claude Desktop Memory Bank server.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
import argparse

from memory_bank.server import MemoryBankServer


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Claude Desktop Memory Bank Server")
    parser.add_argument(
        "--storage-root",
        type=str,
        default=os.environ.get("MEMORY_BANK_ROOT", str(Path.home() / ".claude-desktop" / "memory")),
        help="Root directory for memory bank storage",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.environ.get("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    return parser.parse_args()


async def main():
    """Run the memory bank server."""
    args = parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Claude Desktop Memory Bank with storage root: {args.storage_root}")
    
    # Create storage root directory if it doesn't exist
    storage_root = Path(args.storage_root)
    storage_root.mkdir(parents=True, exist_ok=True)
    
    # Create server
    server = MemoryBankServer(storage_root=storage_root)
    
    try:
        # Start server
        await server.start()
        logger.info("Server started. Press Ctrl+C to stop.")
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
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
