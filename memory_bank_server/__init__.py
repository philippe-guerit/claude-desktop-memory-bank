import sys
from . import server
from .utils import logger

__all__ = ["server"]

def main():
    """Main entry point for the package."""
    import asyncio
    
    try:
        # Print startup message to stderr for debugging
        print("Starting Memory Bank MCP server...", file=sys.stderr)
        
        # Run the server
        asyncio.run(server.main())
    except Exception as e:
        # Log any uncaught exceptions
        print(f"Error in Memory Bank MCP server: {str(e)}", file=sys.stderr)
        logger.error(f"Error in Memory Bank MCP server: {str(e)}", exc_info=True)
        sys.exit(1)
