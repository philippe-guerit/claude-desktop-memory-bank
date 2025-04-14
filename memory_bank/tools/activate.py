"""
Activate tool implementation with Cache Manager integration.

This module provides the activate tool for activating memory banks with in-memory cache support.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData

from memory_bank.cache_manager.cache_manager import CacheManager

logger = logging.getLogger(__name__)

# Schema for activate tool
activate_schema = {
    "type": "object",
    "properties": {
        "conversation_type": {
            "type": "string",
            "enum": ["global", "project"],
            "description": "Type of conversation (global or project)"
        },
        "project_name": {
            "type": "string",
            "description": "Name of the project (required for project type)"
        },
        "current_path": {
            "type": "string",
            "description": "Current path hint for code repository detection"
        },
        "project_description": {
            "type": "string",
            "description": "Project description for creating new projects"
        }
    },
    "required": ["conversation_type"]
}


def register_activate_tool(server: FastMCP, storage):
    """Register the activate tool with the MCP server.
    
    Args:
        server: MCP server instance
        storage: Storage manager instance
    """
    # Get the cache manager singleton instance
    cache_manager = CacheManager.get_instance()
    
    @server.tool(
        name="activate",
        description="Activates memory for the current conversation"
    )
    async def activate(conversation_type: str,
                       project_name: Optional[str] = None,
                       current_path: Optional[str] = None,
                       project_description: Optional[str] = None) -> Dict[str, Any]:
        """Activate a memory bank for the current conversation.
        
        Args:
            conversation_type: Type of conversation (global or project)
            project_name: Name of the project (required for project type)
            current_path: Current path hint for code repository detection
            project_description: Project description for creating new projects
            
        Returns:
            Dict containing bank info, content, and custom instructions
        """
        logger.info(f"Activating {conversation_type} conversation")
        
        try:
            # Validate conversation type
            if conversation_type not in ["global", "project"]:
                raise McpError(
                    ErrorData(
                        code=-32001,  # Custom error code for invalid conversation type
                        message=f"Invalid conversation type: {conversation_type}. Must be one of: global, project."
                    )
                )
            
            # For global conversations, use a standard bank_id
            if conversation_type == "global":
                bank_type = "global"
                bank_id = "default"
                repo_path = None
            
            # For project conversations, require project_name
            elif conversation_type == "project":
                if not project_name:
                    raise McpError(
                        ErrorData(
                            code=-32002,  # Custom error code for missing project name
                            message="Project name is required for project conversations."
                        )
                    )
                
                # Create a normalized bank_id from project_name
                normalized_project_name = project_name.replace(" ", "_").lower()
                
                # Detect if this is a code project by checking for a Git repository
                repo_path = None
                bank_type = "project"  # Default to standard project
                
                if current_path:
                    # Try to detect Git repository
                    repo_info = storage.detect_repo(current_path)
                    if repo_info:
                        repo_path = Path(repo_info["repo_path"])
                        bank_type = "code"  # This is a code project
                        bank_id = normalized_project_name
                    else:
                        # No Git repository, use standard project
                        bank_id = normalized_project_name
                else:
                    # No path hint, use standard project
                    bank_id = normalized_project_name
            
            # Phase 4 Enhancement: Check if bank exists in cache first
            cache_hit = cache_manager.has_bank(bank_type, bank_id)
            logger.info(f"Cache {'' if cache_hit else 'not '}found for {bank_type}:{bank_id}")
            
            if cache_hit:
                # Get content from cache
                content = cache_manager.get_bank(bank_type, bank_id)
                logger.info(f"Loaded content from cache for {bank_type}:{bank_id}")
                
                # Get bank from storage for additional information
                bank = storage.get_bank(bank_type, bank_id, repo_path)
                
                # If bank doesn't exist in storage but exists in cache,
                # we might be in an inconsistent state, but we'll use the cache
                if not bank:
                    logger.warning(f"Bank {bank_type}:{bank_id} exists in cache but not in storage")
                    # Create a new bank
                    bank = storage.create_bank(bank_type, bank_id, repo_path)
                    if not bank:
                        raise Exception(f"Failed to create bank {bank_type}:{bank_id}")
            else:
                # Load or create memory bank from storage
                bank = storage.get_bank(bank_type, bank_id, repo_path)
                if not bank:
                    # Create a new bank
                    bank = storage.create_bank(bank_type, bank_id, repo_path)
                    
                    # Initialize project information if provided
                    if bank_type in ["project", "code"] and project_name and project_description:
                        bank.update_file("readme.md", f"""# {project_name}

## Project Overview
{project_description}

## Goals
Project goals and objectives.

## Stakeholders
Key stakeholders and their roles.
""", "replace")
                
                # Load content from all files
                content = bank.load_all_content()
                
                # Update cache with content from storage
                # This will trigger a cache update for future use
                update_result = cache_manager.update_bank(
                    bank_type,
                    bank_id,
                    "",  # No new content to add
                    immediate_sync=False
                )
                if update_result["status"] == "error":
                    logger.warning(f"Failed to update cache for {bank_type}:{bank_id}: {update_result.get('error')}")
            
            # Get custom instructions for this bank type
            custom_instructions = bank.get_custom_instructions()
            
            # Get previous errors from cache manager
            previous_errors = cache_manager.get_error_history()
            
            # Calculate approximate token count for content
            total_chars = sum(len(content_str) for content_str in content.values())
            approximate_tokens = total_chars // 4  # Rough estimate: 1 token ≈ 4 characters
            
            # Determine if cache optimization might be needed
            optimization_recommended = approximate_tokens > 6000  # Recommend optimization above 6K tokens
            
            # Enhanced response with cache information
            return {
                "status": "success",
                "bank_info": {
                    "type": bank_type,
                    "id": bank_id,
                    "files": bank.list_files(),
                    "last_updated": bank.last_updated().isoformat(),
                    "cache_info": {
                        "cache_hit": cache_hit,
                        "approximate_tokens": approximate_tokens,
                        "optimization_recommended": optimization_recommended
                    }
                },
                "content": content,
                "custom_instructions": custom_instructions,
                "previous_errors": previous_errors
            }
            
        except Exception as e:
            logger.error(f"Error activating memory bank: {e}")
            
            # Get error history from cache manager if available
            previous_errors = []
            try:
                previous_errors = cache_manager.get_error_history()
            except Exception:
                pass
            
            # Include error history in the error response
            raise McpError(
                ErrorData(
                    code=-32000,  # General error code for activation failure
                    message=f"Failed to activate memory bank: {str(e)}",
                    data={"previous_errors": previous_errors}
                )
            )
