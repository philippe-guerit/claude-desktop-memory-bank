import sys
from .utils import logger
from . import server

if __name__ == "__main__":
    """Entry point for running the package as a module."""
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
