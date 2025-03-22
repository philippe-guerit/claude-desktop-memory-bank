import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .context_manager import ContextManager
from .storage_manager import StorageManager
from .memory_bank_selector import MemoryBankSelector
from .repository_utils import RepositoryUtils
from .utils import logger

class MemoryBankServer:
    def __init__(self, root_path: str):
        logger.info(f"Initializing Memory Bank Server with root path: {root_path}")
        
        # Initialize managers
        self.storage_manager = StorageManager(root_path)
        self.memory_bank_selector = MemoryBankSelector(self.storage_manager)
        self.context_manager = ContextManager(self.storage_manager, self.memory_bank_selector)
        
        # Initialize MCP server
        self.server = Server(
            name="memory-bank",
            description="Memory Bank for Claude Desktop"
        )
        
        # Register handlers
        self._register_resource_handlers()
        self._register_tool_handlers()
        self._register_prompt_handlers()
    
    def _register_resource_handlers(self):
        """Register resource handlers for the MCP server."""
        @self.server.resource("project-brief")
        async def get_project_brief(uri: str) -> types.GetResourceResult:
            try:
                context = await self.context_manager.get_context("project_brief")
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=context
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error retrieving project brief: {str(e)}")
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=f"Error retrieving project brief: {str(e)}"
                        )
                    ]
                )
        
        @self.server.resource("active-context")
        async def get_active_context(uri: str) -> types.GetResourceResult:
            try:
                context = await self.context_manager.get_context("active_context")
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=context
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error retrieving active context: {str(e)}")
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=f"Error retrieving active context: {str(e)}"
                        )
                    ]
                )
        
        @self.server.resource("progress")
        async def get_progress(uri: str) -> types.GetResourceResult:
            try:
                context = await self.context_manager.get_context("progress")
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=context
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error retrieving progress: {str(e)}")
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=f"Error retrieving progress: {str(e)}"
                        )
                    ]
                )
        
        @self.server.resource("all-context")
        async def get_all_context(uri: str) -> types.GetResourceResult:
            try:
                contexts = await self.context_manager.get_all_context()
                current_memory_bank = await self.context_manager.get_current_memory_bank()
                
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
                
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=combined
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error retrieving all context: {str(e)}")
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=f"Error retrieving all context: {str(e)}"
                        )
                    ]
                )
        
        @self.server.resource("memory-bank-info")
        async def get_memory_bank_info(uri: str) -> types.GetResourceResult:
            try:
                current_memory_bank = await self.context_manager.get_current_memory_bank()
                all_memory_banks = await self.context_manager.get_memory_banks()
                
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
                
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=output
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error retrieving memory bank information: {str(e)}")
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=f"Error retrieving memory bank information: {str(e)}"
                        )
                    ]
                )
    
    def _register_tool_handlers(self):
        """Register tool handlers for the MCP server."""
        @self.server.tool("select-memory-bank")
        async def select_memory_bank(
            type: str = "global", 
            project: Optional[str] = None, 
            repository_path: Optional[str] = None
        ) -> types.Result:
            """Select which memory bank to use for the conversation.
            
            Args:
                type: The type of memory bank to use ('global', 'project', or 'repository')
                project: The name of the project (for 'project' type)
                repository_path: The path to the repository (for 'repository' type)
            
            Returns:
                Information about the selected memory bank
            """
            try:
                logger.info(f"Selecting memory bank: type={type}, project={project}, repository_path={repository_path}")
                
                if type == "global":
                    memory_bank = await self.context_manager.set_memory_bank()
                elif type == "project":
                    if not project:
                        return types.Result(
                            content=[
                                types.TextContent(
                                    type="text",
                                    text="Project name is required for project memory bank selection."
                                )
                            ]
                        )
                    memory_bank = await self.context_manager.set_memory_bank(claude_project=project)
                elif type == "repository":
                    if not repository_path:
                        return types.Result(
                            content=[
                                types.TextContent(
                                    type="text",
                                    text="Repository path is required for repository memory bank selection."
                                )
                            ]
                        )
                    memory_bank = await self.context_manager.set_memory_bank(repository_path=repository_path)
                else:
                    return types.Result(
                        content=[
                            types.TextContent(
                                type="text",
                                text=f"Unknown memory bank type: {type}. Use 'global', 'project', or 'repository'."
                            )
                        ]
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
                
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error selecting memory bank: {str(e)}")
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error selecting memory bank: {str(e)}"
                        )
                    ]
                )
        
        @self.server.tool("create-project")
        async def create_project(
            name: str, 
            description: str, 
            repository_path: Optional[str] = None
        ) -> types.Result:
            """Create a new project in the memory bank.
            
            Args:
                name: The name of the project to create
                description: A brief description of the project
                repository_path: Optional path to a Git repository to associate with the project
            
            Returns:
                A confirmation message
            """
            try:
                logger.info(f"Creating project: name={name}, repository_path={repository_path}")
                
                # Validate repository path if provided
                if repository_path:
                    if not RepositoryUtils.is_git_repository(repository_path):
                        return types.Result(
                            content=[
                                types.TextContent(
                                    type="text",
                                    text=f"The path {repository_path} is not a valid Git repository."
                                )
                            ]
                        )
                
                # Create project
                project = await self.context_manager.create_project(name, description, repository_path)
                
                result_text = f"Project '{name}' created successfully.\n"
                if repository_path:
                    result_text += f"Associated with repository: {repository_path}\n"
                result_text += "This memory bank is now selected for the current conversation."
                
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error creating project: {str(e)}")
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error creating project: {str(e)}"
                        )
                    ]
                )
        
        @self.server.tool("list-memory-banks")
        async def list_memory_banks() -> types.Result:
            """List all available memory banks.
            
            Returns:
                A list of available memory banks
            """
            try:
                logger.info("Listing all memory banks")
                memory_banks = await self.context_manager.get_memory_banks()
                current_memory_bank = await self.context_manager.get_current_memory_bank()
                
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
                
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error listing memory banks: {str(e)}")
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error listing memory banks: {str(e)}"
                        )
                    ]
                )
        
        @self.server.tool("detect-repository")
        async def detect_repository(path: str) -> types.Result:
            """Detect if a path is within a Git repository.
            
            Args:
                path: The path to check
            
            Returns:
                Information about the detected repository, if any
            """
            try:
                logger.info(f"Detecting repository at path: {path}")
                repo_info = await self.context_manager.detect_repository(path)
                
                if not repo_info:
                    return types.Result(
                        content=[
                            types.TextContent(
                                type="text",
                                text=f"No Git repository found at or above {path}."
                            )
                        ]
                    )
                
                result_text = f"Git repository detected:\n"
                result_text += f"Name: {repo_info.get('name', '')}\n"
                result_text += f"Path: {repo_info.get('path', '')}\n"
                
                if repo_info.get('branch'):
                    result_text += f"Branch: {repo_info.get('branch', '')}\n"
                
                if repo_info.get('remote_url'):
                    result_text += f"Remote URL: {repo_info.get('remote_url', '')}\n"
                
                # Check if repository has a memory bank
                memory_bank_path = repo_info.get('memory_bank_path', '')
                if memory_bank_path and os.path.exists(memory_bank_path):
                    result_text += f"Memory bank exists: Yes\n"
                else:
                    result_text += f"Memory bank exists: No\n"
                    result_text += "Use the initialize-repository-memory-bank tool to create one."
                
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error detecting repository: {str(e)}")
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error detecting repository: {str(e)}"
                        )
                    ]
                )
        
        @self.server.tool("initialize-repository-memory-bank")
        async def initialize_repository_memory_bank(
            repository_path: str, 
            claude_project: Optional[str] = None
        ) -> types.Result:
            """Initialize a memory bank within a Git repository.
            
            Args:
                repository_path: Path to the Git repository
                claude_project: Optional Claude Desktop project to associate with this repository
            
            Returns:
                Information about the initialized memory bank
            """
            try:
                logger.info(f"Initializing repository memory bank: path={repository_path}, project={claude_project}")
                memory_bank = await self.context_manager.initialize_repository_memory_bank(
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
                
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error initializing repository memory bank: {str(e)}")
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error initializing repository memory bank: {str(e)}"
                        )
                    ]
                )
        
        @self.server.tool("update-context")
        async def update_context(context_type: str, content: str) -> types.Result:
            """Update a context file in the current memory bank.
            
            Args:
                context_type: The type of context to update (project_brief, product_context, 
                               system_patterns, tech_context, active_context, progress)
                content: The new content for the context file
            
            Returns:
                A confirmation message
            """
            try:
                logger.info(f"Updating context: type={context_type}")
                memory_bank = await self.context_manager.update_context(context_type, content)
                
                result_text = f"Context '{context_type}' updated successfully in "
                result_text += f"{memory_bank['type']} memory bank."
                
                if memory_bank['type'] == 'repository':
                    repo_info = memory_bank.get('repo_info', {})
                    result_text += f"\nRepository: {repo_info.get('name', '')}"
                    if memory_bank.get('project'):
                        result_text += f"\nAssociated Project: {memory_bank['project']}"
                
                elif memory_bank['type'] == 'project':
                    result_text += f"\nProject: {memory_bank.get('project', '')}"
                
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error updating context: {str(e)}")
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error updating context: {str(e)}"
                        )
                    ]
                )
        
        @self.server.tool("search-context")
        async def search_context(query: str) -> types.Result:
            """Search through context files in the current memory bank.
            
            Args:
                query: The search term to look for in context files
            
            Returns:
                Search results with matching lines
            """
            try:
                logger.info(f"Searching context for: {query}")
                results = await self.context_manager.search_context(query)
                current_memory_bank = await self.context_manager.get_current_memory_bank()
                
                if not results:
                    return types.Result(
                        content=[
                            types.TextContent(
                                type="text",
                                text=f"No results found for query: {query} in {current_memory_bank['type']} memory bank."
                            )
                        ]
                    )
                
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
                
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error searching context: {str(e)}")
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error searching context: {str(e)}"
                        )
                    ]
                )
    
    def _register_prompt_handlers(self):
        """Register prompt handlers for the MCP server."""
        @self.server.prompt("create-project-brief")
        def create_project_brief() -> types.Prompt:
            return types.Prompt(
                name="Create Project Brief",
                description="Template for creating a project brief",
                content=[
                    types.TextContent(
                        type="text",
                        text="""# Project Brief Template

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
                    )
                ]
            )
        
        @self.server.prompt("create-update")
        def create_update() -> types.Prompt:
            return types.Prompt(
                name="Create Progress Update",
                description="Template for updating project progress",
                content=[
                    types.TextContent(
                        type="text",
                        text="""# Progress Update Template

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
                    )
                ]
            )
        
        @self.server.prompt("associate-repository")
        def associate_repository() -> types.Prompt:
            return types.Prompt(
                name="Associate Repository",
                description="Template for associating a repository with a project",
                content=[
                    types.TextContent(
                        type="text",
                        text="""# Associate Repository with Project

## Project Name
[Enter the Claude Desktop project name]

## Repository Path
[Enter the absolute path to the Git repository]

## Description
[Briefly describe the repository and its relation to the project]
"""
                    )
                ]
            )
    
    async def initialize(self) -> None:
        """Initialize the server."""
        logger.info("Initializing Memory Bank server")
        await self.context_manager.initialize()
    
    async def run(self) -> None:
        """Run the server."""
        logger.info("Starting Memory Bank server")
        
        # Import here to avoid circular imports
        import mcp.server.stdio
        
        # Initialize the server
        await self.initialize()
        
        # Run the server using stdin/stdout streams
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("Memory Bank server running")
            await self.server.run(
                read_stream, 
                write_stream,
                InitializationOptions(
                    server_name="memory-bank",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

# Main entry point
async def main():
    # Get root path for the memory bank from environment or use default
    root_path = os.environ.get("MEMORY_BANK_ROOT", os.path.expanduser("~/memory-bank"))
    
    logger.info(f"Starting Memory Bank MCP server with root path: {root_path}")
    
    # Create and run the server
    server = MemoryBankServer(root_path)
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
