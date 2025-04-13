"""
Activate tool implementation.

This module provides the activate tool for activating memory banks.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData

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
                        code="invalid_conversation_type",
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
                            code="missing_project_name",
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
            
            # Load or create memory bank
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
            
            # Get custom instructions for this bank type
            custom_instructions = bank.get_custom_instructions()
            
            return {
                "status": "success",
                "bank_info": {
                    "type": bank_type,
                    "id": bank_id,
                    "files": bank.list_files(),
                    "last_updated": bank.last_updated().isoformat()
                },
                "content": content,
                "custom_instructions": custom_instructions
            }
            
        except Exception as e:
            logger.error(f"Error activating memory bank: {e}")
            raise McpError(
                ErrorData(
                    code="activation_failed",
                    message=f"Failed to activate memory bank: {str(e)}"
                )
            )
