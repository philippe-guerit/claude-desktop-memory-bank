"""
Entry point for the Memory Bank server.

This module is the entry point for running the Memory Bank server.
"""

import os
import sys
import asyncio
import logging
import json
import io

from .server import MemoryBankServer

# Fix for JSON-RPC message encoding 
class FixedJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        # Force specific JSON formatting options
        kwargs['separators'] = (',', ':')
        kwargs['ensure_ascii'] = True
        super().__init__(*args, **kwargs)

# Replace the default JSON encoder
json._default_encoder = FixedJSONEncoder()
json.dumps = lambda obj, **kwargs: json._default_encoder.encode(obj)

# Use UTF-8 encoding for stdout/stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)  # Use stderr for logging to avoid mixing with JSON messages
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main entry point for the Memory Bank server."""
    # Get root path for the memory bank from environment or use default
    root_path = os.environ.get("MEMORY_BANK_ROOT", os.path.expanduser("~/memory-bank"))
    
    logger.info(f"Starting Memory Bank server with root path: {root_path}")
    
    try:
        # Create and run the server
        server = MemoryBankServer(root_path)
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        print(f"Fatal error in Memory Bank server: {str(e)}", file=sys.stderr)
        logger.error(f"Fatal error in Memory Bank server: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
