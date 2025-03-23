"""
Main server class for Memory Bank.

This module contains the main server class that coordinates all components.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any

from ..services import StorageService, RepositoryService, ContextService
from .fastmcp_integration import FastMCPIntegration
from .direct_access import DirectAccess

logger = logging.getLogger(__name__)

class MemoryBankServer:
    """Main server class for Memory Bank system."""
    
    def __init__(self, root_path: str):
        """Initialize the Memory Bank server.
        
        Args:
            root_path: Root path for storing memory bank data
        """
        logger.info(f"Initializing Memory Bank Server with root path: {root_path}")
        
        # Initialize service layer
        self.storage_service = StorageService(root_path)
        self.repository_service = RepositoryService(self.storage_service)
        self.context_service = ContextService(self.storage_service, self.repository_service)
        
        # Initialize integration layers
        self._initialize_integrations()
        
        # Expose direct access methods
        self.direct = self.direct_access
    
    def _initialize_integrations(self):
        """Initialize integration layers."""
        # Initialize direct access methods
        self.direct_access = DirectAccess(self.context_service)
        
        # Initialize FastMCP integration
        self.fastmcp_integration = FastMCPIntegration(self.context_service)
        
        # Load custom instructions for FastMCP
        custom_instructions = self._load_custom_instructions()
        
        # Initialize FastMCP server
        self.fastmcp_integration.initialize(custom_instructions)
        
        # Register handlers
        if self.fastmcp_integration.is_available():
            self.fastmcp_integration.register_handlers()
    
    def _load_custom_instructions(self) -> str:
        """Load custom instructions for the FastMCP server.
        
        Returns:
            Custom instructions as a string
        """
        try:
            # Load custom instructions from the prompt_templates directory
            prompt_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompt_templates")
            instruction_path = os.path.join(prompt_dir, "default_custom_instruction.md")
            
            if os.path.exists(instruction_path):
                logger.info(f"Loading custom instructions from: {instruction_path}")
                with open(instruction_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"Custom instruction file not found at: {instruction_path}")
                return "Memory Bank for Claude Desktop - Autonomous context management system that maintains memory across conversations."
        except Exception as e:
            logger.error(f"Error loading custom instructions: {str(e)}")
            return "Memory Bank for Claude Desktop - Autonomous context management system that maintains memory across conversations."
    
    async def initialize(self) -> None:
        """Initialize the server."""
        logger.info("Initializing Memory Bank server")
        
        # Ensure all JSON messages are formatted correctly for JSON-RPC 2.0
        import json
        # Monkey patch json.dumps to ensure correct message formatting
        original_dumps = json.dumps
        def patched_dumps(*args, **kwargs):
            # Always use compact JSON format without extra whitespace
            kwargs['separators'] = (',', ':')
            # Ensure ASCII compatibility
            kwargs['ensure_ascii'] = True
            return original_dumps(*args, **kwargs)
        json.dumps = patched_dumps
        
        await self.context_service.initialize()
    
    async def run(self) -> None:
        """Run the server."""
        logger.info("Starting Memory Bank server")
        
        try:
            # Set up environment for MCP communication
            import os
            os.environ['MCP_STRICT_JSON'] = 'true'  # Tell MCP to use strict JSON formatting
            os.environ['MCP_USE_LF'] = 'true'  # Ensure line feeds are consistent
            
            # Fix potential JSON encoding issues
            import json
            json_dumps_original = json.dumps
            
            def json_dumps_fixed(obj, **kwargs):
                """Override JSON serialization to ensure consistent formatting."""
                # Force specific settings for JSON-RPC messages
                kwargs['separators'] = (',', ':')
                kwargs['ensure_ascii'] = True
                # Remove any BOM or other problematic characters
                result = json_dumps_original(obj, **kwargs)
                if result.startswith('\ufeff'):  # Remove BOM if present
                    result = result[1:]
                return result
            
            # Apply the fixed JSON dumps globally
            json.dumps = json_dumps_fixed
            
            # Initialize the server
            await self.initialize()
            
            # Check if FastMCP is available
            if self.fastmcp_integration.is_available():
                # Run the server with FastMCP
                logger.info("Memory Bank server running with FastMCP integration")
                await self.fastmcp_integration.run()
            else:
                # Run in standalone mode
                logger.info("Memory Bank server running in standalone mode")
                await self._run_standalone()
        except Exception as e:
            # Log any unexpected errors to stderr to help with debugging
            import sys
            print(f"Memory Bank server error: {str(e)}", file=sys.stderr)
            logger.error(f"Memory Bank server error: {str(e)}", exc_info=True)
            raise  # Re-raise the exception to properly exit the server
    
    async def _run_standalone(self) -> None:
        """Run the server in standalone mode without FastMCP."""
        # This is a placeholder for standalone operation
        # In a real implementation, this could:
        # - Start a REST API server
        # - Start a gRPC server
        # - Provide a CLI interface
        # - Perform background tasks
        
        logger.info("Standalone mode active - waiting for termination")
        
        try:
            # Create an event to keep the server alive
            stop_event = asyncio.Event()
            await stop_event.wait()
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Error in standalone mode: {str(e)}")
            raise
