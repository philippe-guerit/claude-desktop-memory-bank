"""
Activate tool implementation.

This module provides the activate tool for activating memory banks.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from mcp import MCPServer
from mcp.errors import MCPError

logger = logging.getLogger(__name__)

# Schema for activate tool
activate_schema = {
    "type": "object",
    "properties": {
        "bank_type": {
            "type": "string",
            "enum": ["global", "project", "code"],
            "description": "Type of memory bank to activate"
        },
        "bank_id": {
            "type": "string",
            "description": "Identifier for the specific memory bank instance"
        },
        "current_path": {
            "type": "string",
            "description": "Current path for code context detection"
        },
        "project_name": {
            "type": "string",
            "description": "Project name for creating new projects"
        },
        "project_description": {
            "type": "string",
            "description": "Project description for creating new projects"
        }
    },
    "required": ["bank_type", "bank_id"]
}


def register_activate_tool(server: MCPServer, storage):
    """Register the activate tool with the MCP server.
    
    Args:
        server: MCP server instance
        storage: Storage manager instance
    """
    
    @server.tool(
        id="activate",
        description="Activates and loads a memory bank for the current conversation",
        use_when="At the beginning of a conversation to establish context",
        parameters=activate_schema
    )
    async def activate(bank_type: str, bank_id: str,
                       current_path: Optional[str] = None,
                       project_name: Optional[str] = None,
                       project_description: Optional[str] = None) -> Dict[str, Any]:
        """Activate a memory bank for the current conversation.
        
        Args:
            bank_type: Type of memory bank to activate (global, project, code)
            bank_id: Identifier for the specific memory bank instance
            current_path: Current path for code context detection
            project_name: Project name for creating new projects
            project_description: Project description for creating new projects
            
        Returns:
            Dict containing bank info, content, and custom instructions
        """
        logger.info(f"Activating {bank_type} memory bank: {bank_id}")
        
        try:
            # Validate bank type
            if bank_type not in ["global", "project", "code"]:
                raise MCPError(
                    code="invalid_bank_type",
                    message=f"Invalid bank type: {bank_type}. Must be one of: global, project, code."
                )
            
            # Handle code bank with path detection
            repo_path = None
            if bank_type == "code" and current_path:
                # Try to detect Git repository
                repo_info = storage.detect_repo(current_path)
                if repo_info:
                    repo_path = Path(repo_info["repo_path"])
                    
                    # Use repo name as bank_id if not specified
                    if bank_id == "auto" or not bank_id:
                        bank_id = repo_info["repo_name"].replace(" ", "_").lower()
            
            # Create bank_id for new projects
            if bank_type == "project" and (bank_id == "auto" or not bank_id) and project_name:
                bank_id = project_name.replace(" ", "_").lower()
            
            # Use "default" for global banks with auto ID
            if bank_type == "global" and (bank_id == "auto" or not bank_id):
                bank_id = "default"
            
            # Load or create memory bank
            bank = storage.get_bank(bank_type, bank_id, repo_path)
            if not bank:
                # Create a new bank
                bank = storage.create_bank(bank_type, bank_id, repo_path)
                
                # Initialize project information if provided
                if bank_type == "project" and project_name and project_description:
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
            raise MCPError(
                code="activation_failed",
                message=f"Failed to activate memory bank: {str(e)}"
            )
