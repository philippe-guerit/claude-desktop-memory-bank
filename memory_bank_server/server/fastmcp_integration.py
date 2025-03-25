"""
FastMCP integration for Memory Bank.

This module contains adapter functions that connect the core business logic
to the FastMCP framework.
"""

import os
import json  # Added import
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

from mcp.server import FastMCP

from ..core import (
    start_memory_bank,
    select_memory_bank,
    list_memory_banks,
    detect_repository,
    initialize_repository_memory_bank,
    create_project,
    get_context,
    update_context,
    search_context,
    bulk_update_context,
    auto_summarize_context,
    prune_context,
    get_all_context,
    get_memory_bank_info
)

logger = logging.getLogger(__name__)

class FastMCPIntegration:
    """Integration layer between Memory Bank core logic and FastMCP."""
    
    def __init__(self, context_service):
        """Initialize the FastMCP integration.
        
        Args:
            context_service: The context service instance
        """
        self.context_service = context_service
        self.server = None
    
    def initialize(self, custom_instructions: str) -> None:
        """Initialize the FastMCP server.
        
        Args:
            custom_instructions: Custom instructions for the FastMCP server
        """
        try:
            # Configure MCP server with correct JSON-RPC formatting
            import json
            self.server = FastMCP(
                name="memory-bank",
                instructions=custom_instructions,
                json_serializer=lambda obj: json.dumps(obj, separators=(',', ':'), ensure_ascii=True)
            )
            
            # Store custom instructions for default prompt
            self.custom_instructions = custom_instructions
            
            logger.info("FastMCP integration initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing FastMCP: {str(e)}")
            logger.warning("Operating in limited mode without FastMCP")
            self.server = None
    
    def is_available(self) -> bool:
        """Check if FastMCP integration is available.
        
        Returns:
            True if FastMCP is available, False otherwise
        """
        return self.server is not None
    
    def register_handlers(self) -> None:
        """Register handlers with the FastMCP server."""
        if not self.is_available():
            logger.warning("Skipping handler registration - FastMCP not available")
            return
        
        self._register_resource_handlers()
        self._register_tool_handlers()
        self._register_prompt_handlers()
    
    # Resource handlers
    
    def _register_resource_handlers(self) -> None:
        """Register resource handlers with the FastMCP server."""
        # Project brief resource
        @self.server.resource("resource://project-brief", name="Project Brief", description="Current project brief")
        async def get_project_brief_resource() -> str:
            try:
                return await get_context(self.context_service, "project_brief")
            except Exception as e:
                logger.error(f"Error retrieving project brief: {str(e)}")
                return f"Error retrieving project brief: {str(e)}"
        
        # Active context resource
        @self.server.resource("resource://active-context", name="Active Context", description="Active context for the current session")
        async def get_active_context_resource() -> str:
            try:
                return await get_context(self.context_service, "active_context")
            except Exception as e:
                logger.error(f"Error retrieving active context: {str(e)}")
                return f"Error retrieving active context: {str(e)}"
        
        # Progress resource
        @self.server.resource("resource://progress", name="Progress", description="Project progress notes")
        async def get_progress_resource() -> str:
            try:
                return await get_context(self.context_service, "progress")
            except Exception as e:
                logger.error(f"Error retrieving progress: {str(e)}")
                return f"Error retrieving progress: {str(e)}"
        
        # All context resource
        @self.server.resource("resource://all-context", name="All Context", description="All context files combined")
        async def get_all_context_resource() -> str:
            try:
                contexts = await get_all_context(self.context_service)
                bank_info = await get_memory_bank_info(self.context_service)
                current_memory_bank = bank_info["current"]
                
                # Format memory bank info
                memory_bank_info = f"""# Memory Bank Information
Type: {current_memory_bank['type']}
"""
                
                if current_memory_bank['type'] == 'repository':
                    repo_info = current_memory_bank.get('repo_info', {})
                    memory_bank_info += f"""Repository: {repo_info.get('name', '')}
Path: {repo_info.get('path', '')}
Branch: {repo_info.get('branch', '')}
"""
                elif current_memory_bank['type'] == 'project':
                    memory_bank_info += f"""Project: {current_memory_bank.get('project', '')}
"""
                
                # Add memory bank info at the beginning
                combined = memory_bank_info + "\n\n" + "\n\n".join([
                    f"# {key.replace('_', ' ').title()}\n\n{value}" 
                    for key, value in contexts.items()
                ])
                
                return combined
            except Exception as e:
                logger.error(f"Error retrieving all context: {str(e)}")
                return f"Error retrieving all context: {str(e)}"
        
        # Memory bank info resource
        @self.server.resource("resource://memory-bank-info", name="Memory Bank Info", description="Information about the current memory bank")
        async def get_memory_bank_info_resource() -> str:
            try:
                bank_info = await get_memory_bank_info(self.context_service)
                current_memory_bank = bank_info["current"]
                all_memory_banks = bank_info["all"]
                
                output = f"""# Memory Bank Information

## Current Memory Bank
Type: {current_memory_bank['type']}
"""
                
                if current_memory_bank['type'] == 'repository':
                    repo_info = current_memory_bank.get('repo_info', {})
                    output += f"""Repository: {repo_info.get('name', '')}
Path: {repo_info.get('path', '')}
Branch: {repo_info.get('branch', '')}
"""
                    if 'project' in current_memory_bank:
                        output += f"Associated Project: {current_memory_bank['project']}\n"
                
                elif current_memory_bank['type'] == 'project':
                    output += f"Project: {current_memory_bank.get('project', '')}\n"
                
                output += "\n## Available Memory Banks\n"
                
                # Add global memory bank
                output += "\n### Global Memory Bank\n"
                output += f"Path: {all_memory_banks['global'][0]['path']}\n"
                
                # Add project memory banks
                if all_memory_banks['projects']:
                    output += "\n### Project Memory Banks\n"
                    for project in all_memory_banks['projects']:
                        output += f"- {project['name']}\n"
                        if 'repository' in project.get('metadata', {}):
                            output += f"  Repository: {project['metadata']['repository']}\n"
                
                # Add repository memory banks
                if all_memory_banks['repositories']:
                    output += "\n### Repository Memory Banks\n"
                    for repo in all_memory_banks['repositories']:
                        output += f"- {repo['name']} ({repo['repo_path']})\n"
                        if repo.get('project'):
                            output += f"  Associated Project: {repo['project']}\n"
                
                return output
            except Exception as e:
                logger.error(f"Error retrieving memory bank information: {str(e)}")
                return f"Error retrieving memory bank information: {str(e)}"
    
    # Tool handlers
    
    def _register_tool_handlers(self) -> None:
        """Register tool handlers with the FastMCP server."""
        # Memory bank start tool
        @self.server.tool(name="memory-bank-start", description="Initialize the memory bank and load a custom prompt")
        async def memory_bank_start_tool(
            prompt_name: Optional[str] = None,
            auto_detect: bool = True,
            current_path: Optional[str] = None,
            force_type: Optional[str] = None
        ) -> str:
            """Initialize the memory bank and load a custom prompt."""
            try:
                logger.info(f"Starting memory bank with prompt: {prompt_name if prompt_name else 'default'}, " +
                           f"auto_detect: {auto_detect}, path: {current_path}, force_type: {force_type}")
                
                # Call the core business logic
                result = await start_memory_bank(
                    self.context_service,
                    prompt_name=prompt_name,
                    auto_detect=auto_detect,
                    current_path=current_path,
                    force_type=force_type
                )
                
                selected_memory_bank = result["selected_memory_bank"]
                actions_taken = result["actions_taken"]
                
                # Actually retrieve and apply the prompt content using the standard MCP Prompt API
                if prompt_name:
                    logger.info(f"Attempting to load prompt content for: {prompt_name}")
                    
                    try:
                        # Import MCP types needed for prompt handling
                        import mcp.types as types
                        
                        # Get the prompt handler from the server
                        prompt_handler = self.server.get_prompt_handler()
                        
                        if prompt_handler:
                            # Call the handler with the prompt name and empty arguments
                            result = await prompt_handler(prompt_name, None)
                            
                            if isinstance(result, types.GetPromptResult):
                                # Successfully got prompt result, now extract content
                                prompt_content = None
                                
                                # Extract content from messages
                                if result.messages and len(result.messages) > 0:
                                    for message in result.messages:
                                        if hasattr(message, 'role') and message.role == 'user':
                                            if hasattr(message, 'content'):
                                                content = message.content
                                                if hasattr(content, 'type') and content.type == 'text':
                                                    if hasattr(content, 'text'):
                                                        prompt_content = content.text
                                                        break
                                
                                if prompt_content:
                                    # Update the server's instructions with the prompt content
                                    self.custom_instructions = prompt_content
                                    self.server.instructions = prompt_content
                                    logger.info(f"Successfully loaded and applied prompt: {prompt_name}")
                                    actions_taken.append(f"Loaded and applied custom prompt: {prompt_name}")
                                else:
                                    logger.warning(f"Failed to extract content from prompt: {prompt_name}")
                                    prompt_name = "default"
                                    actions_taken.append(f"Failed to extract content from prompt, using default prompt")
                            else:
                                logger.warning(f"Unexpected result type from prompt handler: {type(result)}")
                                prompt_name = "default"
                                actions_taken.append(f"Error retrieving prompt content, using default prompt")
                        else:
                            logger.warning("No prompt handler available")
                            prompt_name = "default"
                            actions_taken.append("No prompt handler available, using default prompt")
                            
                    except Exception as e:
                        logger.error(f"Error retrieving prompt content: {str(e)}")
                        prompt_name = "default"
                        actions_taken.append(f"Error retrieving prompt: {str(e)}, using default prompt")
                else:
                    # No prompt specified, use default
                    prompt_name = "default"
                    actions_taken.append("Using default memory bank custom instructions")
                
                # Format technical details for logging
                tech_details = "Actions performed:\n"
                for action in actions_taken:
                    tech_details += f"- {action}\n"
                
                tech_details += f"\nActive memory bank: {selected_memory_bank['type']}\n"
                
                if selected_memory_bank['type'] == 'repository':
                    repo_info = selected_memory_bank.get('repo_info', {})
                    tech_details += f"Repository: {repo_info.get('name', '')}\n"
                    tech_details += f"Path: {repo_info.get('path', '')}\n"
                    if repo_info.get('branch'):
                        tech_details += f"Branch: {repo_info.get('branch', '')}\n"
                    if selected_memory_bank.get('project'):
                        tech_details += f"Associated Project: {selected_memory_bank['project']}\n"
                
                elif selected_memory_bank['type'] == 'project':
                    tech_details += f"Project: {selected_memory_bank.get('project', '')}\n"
                
                # Get the actual content of the prompt to return directly in the response
                prompt_content = None
                if prompt_name == "default":
                    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompt_templates", "default_custom_instruction.md"), 'r', encoding='utf-8') as f:
                        prompt_content = f.read()
                elif prompt_name == "create-project-brief" and hasattr(self, 'create_project_brief'):
                    result = self.create_project_brief()
                    if isinstance(result, list) and result and 'content' in result[0]:
                        prompt_content = result[0]['content']
                elif prompt_name == "create-update" and hasattr(self, 'create_update'):
                    result = self.create_update()
                    if isinstance(result, list) and result and 'content' in result[0]:
                        prompt_content = result[0]['content']
                elif prompt_name == "associate-repository" and hasattr(self, 'associate_repository'):
                    result = self.associate_repository()
                    if isinstance(result, list) and result and 'content' in result[0]:
                        prompt_content = result[0]['content']
                
                # Get all context from the selected memory bank
                contexts = await get_all_context(self.context_service)
                
                # Add special tag for Claude to recognize and format
                result_text = f"<claude_display>\nThe memory bank was started successfully with the \"{prompt_name}\" prompt.\n</claude_display>\n\n"
                
                # Add technical details
                result_text += f"Technical details:\n{tech_details}\n\n"
                
                # Add memory bank content
                result_text += "## Memory Bank Content\n\n"
                for context_type, content in contexts.items():
                    result_text += f"### {context_type.replace('_', ' ').title()}\n\n{content}\n\n"
                
                # Add the actual prompt content directly in the response
                if prompt_content:
                    result_text += "Custom instructions applied:\n\n"
                    result_text += prompt_content
                
                return result_text
            except Exception as e:
                logger.error(f"Error starting memory bank: {str(e)}")
                return f"Error starting memory bank: {str(e)}"
        
        # Select memory bank tool
        @self.server.tool(name="select-memory-bank", description="Select which memory bank to use for the conversation")
        async def select_memory_bank_tool(
            type: str = "global", 
            project: Optional[str] = None, 
            repository_path: Optional[str] = None
        ) -> str:
            """Select which memory bank to use for the conversation."""
            try:
                logger.info(f"Selecting memory bank: type={type}, project={project}, repository_path={repository_path}")
                
                # Call the core business logic
                try:
                    memory_bank = await select_memory_bank(
                        self.context_service,
                        type=type,
                        project_name=project,
                        repository_path=repository_path
                    )
                    
                    # Format result based on memory bank type
                    result_text = f"Selected memory bank: {memory_bank['type']}\n"
                    
                    if memory_bank['type'] == 'repository':
                        repo_info = memory_bank.get('repo_info', {})
                        result_text += f"Repository: {repo_info.get('name', '')}\n"
                        result_text += f"Path: {repo_info.get('path', '')}\n"
                        if repo_info.get('branch'):
                            result_text += f"Branch: {repo_info.get('branch', '')}\n"
                        if memory_bank.get('project'):
                            result_text += f"Associated Project: {memory_bank['project']}\n"
                    
                    elif memory_bank['type'] == 'project':
                        result_text += f"Project: {memory_bank.get('project', '')}\n"
                    
                    return result_text
                except ValueError as e:
                    return str(e)
                
            except Exception as e:
                logger.error(f"Error selecting memory bank: {str(e)}")
                return f"Error selecting memory bank: {str(e)}"
        
        # Create project tool
        @self.server.tool(name="create-project", description="Create a new project in the memory bank")
        async def create_project_tool(
            name: str, 
            description: str, 
            repository_path: Optional[str] = None
        ) -> str:
            """Create a new project in the memory bank."""
            try:
                logger.info(f"Creating project: name={name}, repository_path={repository_path}")
                
                # Call the core business logic
                try:
                    project = await create_project(
                        self.context_service,
                        name, 
                        description, 
                        repository_path
                    )
                    
                    result_text = f"Project '{name}' created successfully.\n"
                    if repository_path:
                        result_text += f"Associated with repository: {repository_path}\n"
                    result_text += "This memory bank is now selected for the current conversation."
                    
                    return result_text
                except ValueError as e:
                    return str(e)
                
            except Exception as e:
                logger.error(f"Error creating project: {str(e)}")
                return f"Error creating project: {str(e)}"
        
        # List memory banks tool
        @self.server.tool(name="list-memory-banks", description="List all available memory banks")
        async def list_memory_banks_tool() -> str:
            """List all available memory banks."""
            try:
                logger.info("Listing all memory banks")
                
                # Call the core business logic
                result = await list_memory_banks(self.context_service)
                
                current_memory_bank = result["current"]
                memory_banks = result["available"]
                
                result_text = "# Available Memory Banks\n\n"
                
                # Add current memory bank info
                result_text += "## Current Memory Bank\n"
                result_text += f"Type: {current_memory_bank['type']}\n"
                
                if current_memory_bank['type'] == 'repository':
                    repo_info = current_memory_bank.get('repo_info', {})
                    result_text += f"Repository: {repo_info.get('name', '')}\n"
                    result_text += f"Path: {repo_info.get('path', '')}\n"
                    if repo_info.get('branch'):
                        result_text += f"Branch: {repo_info.get('branch', '')}\n"
                    if current_memory_bank.get('project'):
                        result_text += f"Associated Project: {current_memory_bank['project']}\n"
                
                elif current_memory_bank['type'] == 'project':
                    result_text += f"Project: {current_memory_bank.get('project', '')}\n"
                
                # Add global memory bank
                result_text += "\n## Global Memory Bank\n"
                result_text += f"Path: {memory_banks['global'][0]['path']}\n"
                
                # Add project memory banks
                if memory_banks['projects']:
                    result_text += "\n## Project Memory Banks\n"
                    for project in memory_banks['projects']:
                        result_text += f"- {project['name']}\n"
                        if 'repository' in project.get('metadata', {}):
                            result_text += f"  Repository: {project['metadata']['repository']}\n"
                
                # Add repository memory banks
                if memory_banks['repositories']:
                    result_text += "\n## Repository Memory Banks\n"
                    for repo in memory_banks['repositories']:
                        result_text += f"- {repo['name']} ({repo['repo_path']})\n"
                        if repo.get('project'):
                            result_text += f"  Associated Project: {repo['project']}\n"
                
                return result_text
            except Exception as e:
                logger.error(f"Error listing memory banks: {str(e)}")
                return f"Error listing memory banks: {str(e)}"
        
        # Detect repository tool
        @self.server.tool(name="detect-repository", description="Detect if a path is within a Git repository")
        async def detect_repository_tool(path: str) -> str:
            """Detect if a path is within a Git repository."""
            try:
                logger.info(f"Detecting repository at path: {path}")
                
                # Call the core business logic
                repo_info = await detect_repository(self.context_service, path)
                
                if not repo_info:
                    return f"No Git repository found at or above {path}."
                
                result_text = f"Git repository detected:\n"
                result_text += f"Name: {repo_info.get('name', '')}\n"
                result_text += f"Path: {repo_info.get('path', '')}\n"
                
                if repo_info.get('branch'):
                    result_text += f"Branch: {repo_info.get('branch', '')}\n"
                
                if repo_info.get('remote_url'):
                    result_text += f"Remote URL: {repo_info.get('remote_url', '')}\n"
                
                # Check if repository has a memory bank
                memory_bank_path = repo_info.get('memory_bank_path')
                if memory_bank_path and os.path.exists(memory_bank_path):
                    result_text += f"Memory bank exists: Yes\n"
                else:
                    result_text += f"Memory bank exists: No\n"
                    result_text += "Use the initialize-repository-memory-bank tool to create one."
                
                return result_text
            except Exception as e:
                logger.error(f"Error detecting repository: {str(e)}")
                return f"Error detecting repository: {str(e)}"
        
        # Initialize repository memory bank tool
        @self.server.tool(name="initialize-repository-memory-bank", description="Initialize a memory bank within a Git repository")
        async def initialize_repository_memory_bank_tool(
            repository_path: str, 
            claude_project: Optional[str] = None
        ) -> str:
            """Initialize a memory bank within a Git repository."""
            try:
                logger.info(f"Initializing repository memory bank: path={repository_path}, project={claude_project}")
                
                # Call the core business logic
                memory_bank = await initialize_repository_memory_bank(
                    self.context_service,
                    repository_path, 
                    claude_project
                )
                
                result_text = f"Repository memory bank initialized:\n"
                result_text += f"Path: {memory_bank['path']}\n"
                
                repo_info = memory_bank.get('repo_info', {})
                result_text += f"Repository: {repo_info.get('name', '')}\n"
                result_text += f"Repository path: {repo_info.get('path', '')}\n"
                
                if claude_project:
                    result_text += f"Associated Claude project: {claude_project}\n"
                
                result_text += "This memory bank is now selected for the current conversation."
                
                return result_text
            except Exception as e:
                logger.error(f"Error initializing repository memory bank: {str(e)}")
                return f"Error initializing repository memory bank: {str(e)}"
        
        # Update context tool
        @self.server.tool(name="update-context", description="Update a context file in the current memory bank")
        async def update_context_tool(context_type: str, content: str) -> str:
            """Update a context file in the current memory bank."""
            try:
                logger.info(f"Updating context: type={context_type}")
                
                # Call the core business logic
                try:
                    memory_bank = await update_context(
                        self.context_service,
                        context_type,
                        content
                    )
                    
                    # Wait for a moment to ensure file operations complete
                    await asyncio.sleep(0.1)
                    
                    # Verify that the file was actually updated
                    try:
                        # Get the file path
                        file_name = self.context_service.CONTEXT_FILES[context_type]
                        file_path = Path(memory_bank['path']) / file_name
                        
                        # Read back from file to verify it was written
                        read_content = await self.context_service.get_context(context_type)
                        
                        # Check if content matches what we tried to write
                        if read_content != content:
                            logger.error(f"Verification failed for context update: content mismatch for {context_type}")
                            return f"Error: Content verification failed for {context_type}. The file may not have been updated correctly."
                        
                        logger.info(f"Successfully verified context update for {context_type}")
                    except Exception as e:
                        logger.error(f"Error verifying context update: {str(e)}")
                    
                    
                    result_text = f"Context '{context_type}' updated successfully in "
                    result_text += f"{memory_bank['type']} memory bank."
                    
                    if memory_bank['type'] == 'repository':
                        repo_info = memory_bank.get('repo_info', {})
                        result_text += f"\nRepository: {repo_info.get('name', '')}"
                        if memory_bank.get('project'):
                            result_text += f"\nAssociated Project: {memory_bank['project']}"
                    
                    elif memory_bank['type'] == 'project':
                        result_text += f"\nProject: {memory_bank.get('project', '')}"
                    
                    return result_text
                except ValueError as e:
                    return str(e)
                
            except Exception as e:
                logger.error(f"Error updating context: {str(e)}")
                return f"Error updating context: {str(e)}"
        
        # Search context tool
        @self.server.tool(name="search-context", description="Search through context files in the current memory bank")
        async def search_context_tool(query: str) -> str:
            """Search through context files in the current memory bank."""
            try:
                logger.info(f"Searching context for: {query}")
                
                # Call the core business logic
                results = await search_context(self.context_service, query)
                current_memory_bank = await self.context_service.get_current_memory_bank()
                
                if not results:
                    return f"No results found for query: {query} in {current_memory_bank['type']} memory bank."
                
                result_text = f"Search results for '{query}' in {current_memory_bank['type']} memory bank:\n\n"
                
                # Add memory bank info
                if current_memory_bank['type'] == 'repository':
                    repo_info = current_memory_bank.get('repo_info', {})
                    result_text += f"Repository: {repo_info.get('name', '')}\n"
                    if current_memory_bank.get('project'):
                        result_text += f"Associated Project: {current_memory_bank['project']}\n"
                
                elif current_memory_bank['type'] == 'project':
                    result_text += f"Project: {current_memory_bank.get('project', '')}\n"
                
                result_text += "\n"
                
                # Add search results
                for context_type, lines in results.items():
                    result_text += f"## {context_type.replace('_', ' ').title()}\n\n"
                    for line in lines:
                        result_text += f"- {line}\n"
                    result_text += "\n"
                
                return result_text
            except Exception as e:
                logger.error(f"Error searching context: {str(e)}")
                return f"Error searching context: {str(e)}"
        
        # Bulk update context tool
        @self.server.tool(name="bulk-update-context", description="Update multiple context files in one operation")
        async def bulk_update_context_tool(updates: Dict[str, str]) -> str:
            """Update multiple context files in one operation."""
            try:
                logger.info(f"Bulk updating context with {len(updates)} updates")
                
                # Call the core business logic
                try:
                    memory_bank = await bulk_update_context(self.context_service, updates)
                    
                    # Wait for a moment to ensure file operations complete
                    await asyncio.sleep(0.1)
                    
                    # Verify that the files were actually updated
                    verification_passed = True
                    for context_type, content in updates.items():
                        try:
                            # Read back from file to verify it was written
                            read_content = await self.context_service.get_context(context_type)
                            
                            # Check if content matches what we tried to write
                            if read_content != content:
                                logger.error(f"Verification failed for bulk update: content mismatch for {context_type}")
                                verification_passed = False
                        except Exception as e:
                            logger.error(f"Error verifying bulk update for {context_type}: {str(e)}")
                            verification_passed = False
                    
                    if not verification_passed:
                        return f"Error: Content verification failed for some context files. The updates may not have been applied correctly."
                    
                    logger.info(f"Successfully verified bulk update for {len(updates)} context files")
                    
                    result_text = f"Successfully updated {len(updates)} context files in "
                    result_text += f"{memory_bank['type']} memory bank.\n\n"
                    result_text += f"Updated context types: {', '.join(updates.keys())}"
                    
                    if memory_bank['type'] == 'repository':
                        repo_info = memory_bank.get('repo_info', {})
                        result_text += f"\nRepository: {repo_info.get('name', '')}"
                        if memory_bank.get('project'):
                            result_text += f"\nAssociated Project: {memory_bank['project']}"
                    
                    elif memory_bank['type'] == 'project':
                        result_text += f"\nProject: {memory_bank.get('project', '')}"
                    
                    return result_text
                except ValueError as e:
                    return str(e)
                
            except Exception as e:
                logger.error(f"Error bulk updating context: {str(e)}")
                return f"Error bulk updating context: {str(e)}"
        
        # Auto summarize context tool
        @self.server.tool(name="auto-summarize-context", description="Automatically extract and update context from conversation")
        async def auto_summarize_context_tool(conversation_text: str) -> str:
            """Extract relevant information from conversation and update context automatically."""
            try:
                logger.info("Auto-summarizing context from conversation")
                
                # Call the core business logic
                suggested_updates = await auto_summarize_context(
                    self.context_service,
                    conversation_text
                )
                
                if not suggested_updates:
                    return "No relevant information found to update context."
                
                # Apply all suggested updates
                memory_bank = await bulk_update_context(
                    self.context_service,
                    suggested_updates
                )
                
                result_text = f"Successfully extracted and updated {len(suggested_updates)} context files:\n\n"
                
                # List what was updated
                for context_type in suggested_updates.keys():
                    result_text += f"- {context_type.replace('_', ' ').title()}\n"
                
                # Add memory bank info
                result_text += f"\nUpdates applied to {memory_bank['type']} memory bank."
                
                if memory_bank['type'] == 'repository':
                    repo_info = memory_bank.get('repo_info', {})
                    result_text += f"\nRepository: {repo_info.get('name', '')}"
                    if memory_bank.get('project'):
                        result_text += f"\nAssociated Project: {memory_bank['project']}"
                
                elif memory_bank['type'] == 'project':
                    result_text += f"\nProject: {memory_bank.get('project', '')}"
                
                return result_text
            except Exception as e:
                logger.error(f"Error auto-summarizing context: {str(e)}")
                return f"Error auto-summarizing context: {str(e)}"
        
        # Prune context tool
        @self.server.tool(name="prune-context", description="Remove outdated information from context files")
        async def prune_context_tool(max_age_days: int = 90) -> str:
            """Remove outdated information from context files."""
            try:
                logger.info(f"Pruning context older than {max_age_days} days")
                
                # Call the core business logic
                pruning_results = await prune_context(
                    self.context_service,
                    max_age_days
                )
                
                if not pruning_results:
                    return "No outdated content found to prune."
                
                memory_bank_info = await get_memory_bank_info(self.context_service)
                current_memory_bank = memory_bank_info["current"]
                
                result_text = f"Pruning results for {current_memory_bank['type']} memory bank:\n\n"
                
                pruned_total = 0
                kept_total = 0
                
                # Add details for each context type
                for context_type, result in pruning_results.items():
                    if "error" in result:
                        result_text += f"- {context_type.replace('_', ' ').title()}: Error - {result['error']}\n"
                    else:
                        pruned = result.get("pruned_sections", 0)
                        kept = result.get("kept_sections", 0)
                        
                        if pruned > 0:
                            result_text += f"- {context_type.replace('_', ' ').title()}: Pruned {pruned} sections, kept {kept} sections\n"
                            pruned_total += pruned
                            kept_total += kept
                
                if pruned_total > 0:
                    result_text += f"\nTotal: Pruned {pruned_total} sections, kept {kept_total} sections"
                else:
                    result_text += "\nNo sections were old enough to prune."
                
                return result_text
            except Exception as e:
                logger.error(f"Error pruning context: {str(e)}")
                return f"Error pruning context: {str(e)}"
    
    # Prompt handlers
    
    def _register_prompt_handlers(self) -> None:
        """Register prompt handlers with the FastMCP server."""
        # Default memory bank prompt - store reference to function
        @self.server.prompt(name="default", description="Default memory bank prompt with custom instructions")
        def default_memory_bank_prompt() -> str:
            """Default memory bank prompt with custom instructions."""
            return self.custom_instructions
        
        # Store reference to the function
        self.default_memory_bank_prompt = default_memory_bank_prompt
            
        # Create project brief prompt
        @self.server.prompt(name="create-project-brief", description="Template for creating a project brief")
        def create_project_brief() -> list:
            return [
                {
                    "role": "user",
                    "content": """# Project Brief Template

## Project Name
[Enter the project name here]

## Purpose
[Describe the primary purpose of this project]

## Goals
[List the main goals of the project]

## Requirements
[List key requirements]

## Scope
[Define what is in and out of scope]

## Timeline
[Provide a high-level timeline]

## Stakeholders
[List key stakeholders]

## Repository
[If applicable, specify the path to the Git repository]
"""
                }
            ]
        
        # Store reference to the function
        self.create_project_brief = create_project_brief
        
        # Create update prompt
        @self.server.prompt(name="create-update", description="Template for updating project progress")
        def create_update() -> list:
            return [
                {
                    "role": "user",
                    "content": """# Progress Update Template

## Completed
[List recently completed items]

## In Progress
[List items currently being worked on]

## Pending
[List upcoming items]

## Issues
[List any issues or blockers]

## Notes
[Any additional notes]
"""
                }
            ]
        
        # Store reference to the function
        self.create_update = create_update
        
        # Associate repository prompt
        @self.server.prompt(name="associate-repository", description="Template for associating a repository with a project")
        def associate_repository() -> list:
            return [
                {
                    "role": "user",
                    "content": """# Associate Repository with Project

## Project Name
[Enter the Claude Desktop project name]

## Repository Path
[Enter the absolute path to the Git repository]

## Description
[Briefly describe the repository and its relation to the project]
"""
                }
            ]
        
        # Store reference to the function
        self.associate_repository = associate_repository
    
    async def run(self) -> None:
        """Run the FastMCP server."""
        if not self.is_available():
            raise RuntimeError("FastMCP server is not available")
        
        # Override the server's JSON serialization to ensure proper formatting
        import json
        import sys
        
        # Store original methods
        original_stdout_write = sys.stdout.write
        original_json_dumps = json.dumps
        
        # Define a wrapper for stdout.write to ensure proper message formatting
        def custom_stdout_write(data):
            # If this looks like JSON, ensure it's properly formatted
            if data.strip().startswith('{'):
                try:
                    # Parse and re-serialize to ensure clean JSON
                    parsed = json.loads(data)
                    clean_data = original_json_dumps(parsed, separators=(',', ':'), ensure_ascii=True) + '\n'
                    return original_stdout_write(clean_data)
                except:
                    pass
            # For non-JSON data, proceed as normal
            return original_stdout_write(data)
        
        # Replace stdout.write with our custom version
        sys.stdout.write = custom_stdout_write
        
        logger.info("Memory Bank server running with FastMCP integration")
        await self.server.run_stdio_async()
    
    # Utility methods
    
    def format_result(self, result: Any) -> str:
        """Format a result for FastMCP response.
        
        Args:
            result: Result to format
            
        Returns:
            Formatted result string
        """
        if isinstance(result, dict):
            # Ensure the result is a proper JSON-RPC 2.0 response
            if "jsonrpc" not in result:
                result["jsonrpc"] = "2.0"
            if "id" not in result:
                result["id"] = 0
            
            # Format dictionary without any extra whitespace or newlines
            return json.dumps(result, separators=(',', ':'))
        elif isinstance(result, str):
            # For string results, ensure no embedded newlines
            return result.replace('\n', ' ')
        else:
            # Convert other types to string, ensure no newlines
            return str(result).replace('\n', ' ')
