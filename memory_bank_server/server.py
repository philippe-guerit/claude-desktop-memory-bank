import os
import json
import asyncio
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

import mcp.types as types
from mcp.server import FastMCP
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
        
        # Load custom instructions
        custom_instructions = self._load_custom_instructions()
        
        # Initialize MCP server with custom instructions
        self.server = FastMCP(
            name="memory-bank",
            instructions=custom_instructions
        )
        
        # Register handlers
        self._register_resource_handlers()
        self._register_tool_handlers()
        self._register_prompt_handlers()
    
    def _load_custom_instructions(self) -> str:
        """Load custom instructions from file."""
        try:
            # Load custom instructions from the prompt_templates directory
            prompt_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompt_templates")
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
    
    def _register_resource_handlers(self):
        """Register resource handlers for the MCP server."""
        # Resources are registered directly with the FastMCP API
        # No need for the resources/list handler as it's built-in to FastMCP
        @self.server.resource("resource://project-brief", name="Project Brief", description="Current project brief")
        async def get_project_brief() -> str:
            try:
                context = await self.context_manager.get_context("project_brief")
                return context
            except Exception as e:
                logger.error(f"Error retrieving project brief: {str(e)}")
                return f"Error retrieving project brief: {str(e)}"
        
        @self.server.resource("resource://active-context", name="Active Context", description="Active context for the current session")
        async def get_active_context() -> str:
            try:
                context = await self.context_manager.get_context("active_context")
                return context
            except Exception as e:
                logger.error(f"Error retrieving active context: {str(e)}")
                return f"Error retrieving active context: {str(e)}"
        
        @self.server.resource("resource://progress", name="Progress", description="Project progress notes")
        async def get_progress() -> str:
            try:
                context = await self.context_manager.get_context("progress")
                return context
            except Exception as e:
                logger.error(f"Error retrieving progress: {str(e)}")
                return f"Error retrieving progress: {str(e)}"
        
        @self.server.resource("resource://all-context", name="All Context", description="All context files combined")
        async def get_all_context() -> str:
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
                
                return combined
            except Exception as e:
                logger.error(f"Error retrieving all context: {str(e)}")
                return f"Error retrieving all context: {str(e)}"
        
        @self.server.resource("resource://memory-bank-info", name="Memory Bank Info", description="Information about the current memory bank")
        async def get_memory_bank_info() -> str:
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
                
                return output
            except Exception as e:
                logger.error(f"Error retrieving memory bank information: {str(e)}")
                return f"Error retrieving memory bank information: {str(e)}"
    
    def _register_tool_handlers(self):
        """Register tool handlers for the MCP server."""
        
        @self.server.tool(name="memory-bank-start", description="Initialize the memory bank and load a custom prompt")
        async def memory_bank_start(
            prompt_name: Optional[str] = None,
            auto_detect: bool = True,
            current_path: Optional[str] = None,
            force_type: Optional[str] = None
        ) -> str:
            """Initialize the memory bank and load a custom prompt.
            
            Args:
                prompt_name: Optional name of the prompt to load. If not provided, 
                            the default custom instruction will be used.
                auto_detect: Whether to automatically detect repositories. Default: True
                current_path: Path to check for repository. Default: Current working directory
                force_type: Force a specific memory bank type ('global', 'project', or 'repository')
                            overriding auto-detection.
            
            Returns:
                Confirmation message about the initialization
            """
            try:
                logger.info(f"Starting memory bank with prompt: {prompt_name if prompt_name else 'default'}, " +
                           f"auto_detect: {auto_detect}, path: {current_path}, force_type: {force_type}")
                
                # Initialize tracking variables
                actions_taken = []
                selected_memory_bank = None
                
                # Use current working directory if path not provided
                if not current_path:
                    current_path = os.getcwd()
                    logger.info(f"Using current working directory: {current_path}")
                
                # Step 1: Auto-detect repository if enabled
                detected_repo = None
                if auto_detect and not force_type:
                    logger.info(f"Attempting repository detection at: {current_path}")
                    detected_repo = await self.context_manager.detect_repository(current_path)
                    
                    if detected_repo:
                        actions_taken.append(f"Detected repository: {detected_repo.get('name', '')}")
                        logger.info(f"Repository detected: {detected_repo}")
                
                # Step 2: Initialize repository memory bank if needed
                if detected_repo and not force_type:
                    # Check if memory bank exists for this repository
                    memory_bank_path = detected_repo.get('memory_bank_path', '')
                    if not memory_bank_path or not os.path.exists(memory_bank_path):
                        logger.info(f"Initializing repository memory bank for: {detected_repo.get('path', '')}")
                        repo_memory_bank = await self.context_manager.initialize_repository_memory_bank(
                            detected_repo.get('path', '')
                        )
                        actions_taken.append(f"Initialized repository memory bank for: {detected_repo.get('name', '')}")
                        selected_memory_bank = repo_memory_bank
                    else:
                        actions_taken.append(f"Using existing repository memory bank: {detected_repo.get('name', '')}")
                
                # Step 3: Select appropriate memory bank based on detection or force_type
                if force_type:
                    logger.info(f"Forcing memory bank type: {force_type}")
                    if force_type == "global":
                        selected_memory_bank = await self.context_manager.set_memory_bank()
                        actions_taken.append("Forced selection of global memory bank")
                    elif force_type == "project" and force_type.startswith("project:"):
                        project_name = force_type.split(":", 1)[1]
                        selected_memory_bank = await self.context_manager.set_memory_bank(claude_project=project_name)
                        actions_taken.append(f"Forced selection of project memory bank: {project_name}")
                    elif force_type == "repository" and force_type.startswith("repository:"):
                        repo_path = force_type.split(":", 1)[1]
                        selected_memory_bank = await self.context_manager.set_memory_bank(repository_path=repo_path)
                        actions_taken.append(f"Forced selection of repository memory bank: {repo_path}")
                    else:
                        actions_taken.append(f"Warning: Invalid force_type: {force_type}. Using default selection.")
                        
                elif detected_repo and not selected_memory_bank:
                    # We detected a repo but didn't initialize a memory bank (it already existed)
                    logger.info(f"Selecting detected repository memory bank: {detected_repo.get('path', '')}")
                    selected_memory_bank = await self.context_manager.set_memory_bank(
                        repository_path=detected_repo.get('path', '')
                    )
                    actions_taken.append(f"Selected repository memory bank: {detected_repo.get('name', '')}")
                
                # If no memory bank was selected yet, get the current memory bank
                if not selected_memory_bank:
                    selected_memory_bank = await self.context_manager.get_current_memory_bank()
                    actions_taken.append(f"Using current memory bank: {selected_memory_bank['type']}")
                
                # Step 4: Get available prompts
                prompts_data = self.server.handle_message({"type": "prompts/list"})
                available_prompts = {prompt["id"]: prompt["name"] for prompt in prompts_data.get("prompts", [])}
                
                # Step 5: Load the specified prompt or default
                if prompt_name and prompt_name in available_prompts:
                    # Load the specified prompt
                    prompt_data = self.server.handle_message({
                        "type": "prompts/get",
                        "prompt_id": prompt_name
                    })
                    actions_taken.append(f"Loaded custom prompt: {available_prompts[prompt_name]}")
                else:
                    # No valid prompt specified, load the default custom instruction
                    # This is already loaded when the server initializes
                    actions_taken.append("Loaded default memory bank custom instructions")
                
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
                
                # Create response with special wrapper for Claude
                prompt_name_display = prompt_name if prompt_name and prompt_name in available_prompts else "default"
                
                # Add special tag for Claude to recognize and format
                result_text = f"<claude_display>\nThe memory bank was started successfully with the \"{prompt_name_display}\" prompt.\n</claude_display>\n\n"
                result_text += f"Technical details:\n{tech_details}"
                
                return result_text
            except Exception as e:
                logger.error(f"Error starting memory bank: {str(e)}")
                return f"Error starting memory bank: {str(e)}"
        @self.server.tool(name="select-memory-bank", description="Select which memory bank to use for the conversation")
        async def select_memory_bank(
            type: str = "global", 
            project: Optional[str] = None, 
            repository_path: Optional[str] = None
        ) -> str:
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
                        return "Project name is required for project memory bank selection."
                    memory_bank = await self.context_manager.set_memory_bank(claude_project=project)
                elif type == "repository":
                    if not repository_path:
                        return "Repository path is required for repository memory bank selection."
                    memory_bank = await self.context_manager.set_memory_bank(repository_path=repository_path)
                else:
                    return f"Unknown memory bank type: {type}. Use 'global', 'project', or 'repository'."
                
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
            except Exception as e:
                logger.error(f"Error selecting memory bank: {str(e)}")
                return f"Error selecting memory bank: {str(e)}"
        
        @self.server.tool(name="create-project", description="Create a new project in the memory bank")
        async def create_project(
            name: str, 
            description: str, 
            repository_path: Optional[str] = None
        ) -> str:
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
                        return f"The path {repository_path} is not a valid Git repository."
                
                # Create project
                project = await self.context_manager.create_project(name, description, repository_path)
                
                result_text = f"Project '{name}' created successfully.\n"
                if repository_path:
                    result_text += f"Associated with repository: {repository_path}\n"
                result_text += "This memory bank is now selected for the current conversation."
                
                return result_text
            except Exception as e:
                logger.error(f"Error creating project: {str(e)}")
                return f"Error creating project: {str(e)}"
        
        @self.server.tool(name="list-memory-banks", description="List all available memory banks")
        async def list_memory_banks() -> str:
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
                
                return result_text
            except Exception as e:
                logger.error(f"Error listing memory banks: {str(e)}")
                return f"Error listing memory banks: {str(e)}"
        
        @self.server.tool(name="detect-repository", description="Detect if a path is within a Git repository")
        async def detect_repository(path: str) -> str:
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
                    return f"No Git repository found at or above {path}."
                
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
                
                return result_text
            except Exception as e:
                logger.error(f"Error detecting repository: {str(e)}")
                return f"Error detecting repository: {str(e)}"
        
        @self.server.tool(name="initialize-repository-memory-bank", description="Initialize a memory bank within a Git repository")
        async def initialize_repository_memory_bank(
            repository_path: str, 
            claude_project: Optional[str] = None
        ) -> str:
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
                
                return result_text
            except Exception as e:
                logger.error(f"Error initializing repository memory bank: {str(e)}")
                return f"Error initializing repository memory bank: {str(e)}"
        
        @self.server.tool(name="update-context", description="Update a context file in the current memory bank")
        async def update_context(context_type: str, content: str) -> str:
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
                
                return result_text
            except Exception as e:
                logger.error(f"Error updating context: {str(e)}")
                return f"Error updating context: {str(e)}"
        
        @self.server.tool(name="search-context", description="Search through context files in the current memory bank")
        async def search_context(query: str) -> str:
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
                
        @self.server.tool(name="bulk-update-context", description="Update multiple context files in one operation")
        async def bulk_update_context(updates: Dict[str, str]) -> str:
            """Update multiple context files in one operation.
            
            Args:
                updates: Dictionary mapping context types to content
                  - Keys can be: project_brief, product_context, system_patterns, 
                                tech_context, active_context, progress
                  - Values are the new content for each context file
            
            Returns:
                A confirmation message
            """
            try:
                logger.info(f"Bulk updating context with {len(updates)} updates")
                memory_bank = await self.context_manager.bulk_update_context(updates)
                
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
            except Exception as e:
                logger.error(f"Error bulk updating context: {str(e)}")
                return f"Error bulk updating context: {str(e)}"
                
        @self.server.tool(name="auto-summarize-context", description="Automatically extract and update context from conversation")
        async def auto_summarize_context(conversation_text: str) -> str:
            """Extract relevant information from conversation and update context automatically.
            
            Args:
                conversation_text: Text of the conversation to summarize
            
            Returns:
                Summary of updates made
            """
            try:
                logger.info("Auto-summarizing context from conversation")
                suggested_updates = await self.context_manager.auto_summarize_context(conversation_text)
                
                if not suggested_updates:
                    return "No relevant information found to update context."
                
                # Apply all suggested updates
                memory_bank = await self.context_manager.bulk_update_context(suggested_updates)
                
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
                
        @self.server.tool(name="prune-context", description="Remove outdated information from context files")
        async def prune_context(max_age_days: int = 90) -> str:
            """Remove outdated information from context files.
            
            Args:
                max_age_days: Maximum age of content to retain (in days, default: 90)
            
            Returns:
                Summary of pruning results
            """
            try:
                logger.info(f"Pruning context older than {max_age_days} days")
                pruning_results = await self.context_manager.prune_context(max_age_days)
                
                if not pruning_results:
                    return "No outdated content found to prune."
                
                current_memory_bank = await self.context_manager.get_current_memory_bank()
                
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
    
    def _register_prompt_handlers(self):
        """Register prompt handlers for the MCP server."""
        # No need to register a separate prompts/list handler in FastMCP
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
    
    async def initialize(self) -> None:
        """Initialize the server."""
        logger.info("Initializing Memory Bank server")
        await self.context_manager.initialize()
    
    async def run(self) -> None:
        """Run the server."""
        logger.info("Starting Memory Bank server")
        
        try:
            # Initialize the server
            await self.initialize()
            
            # Run the server
            logger.info("Memory Bank server running")
            await self.server.run_stdio_async()
        except Exception as e:
            # Log any unexpected errors to stderr to help with debugging
            import sys
            print(f"Memory Bank server error: {str(e)}", file=sys.stderr)
            logger.error(f"Memory Bank server error: {str(e)}", exc_info=True)
            raise  # Re-raise the exception to properly exit the server

# Main entry point
async def main():
    # Get root path for the memory bank from environment or use default
    root_path = os.environ.get("MEMORY_BANK_ROOT", os.path.expanduser("~/memory-bank"))
    
    logger.info(f"Starting Memory Bank MCP server with root path: {root_path}")
    
    try:
        # Create and run the server
        server = MemoryBankServer(root_path)
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        print(f"Fatal error in Memory Bank MCP server: {str(e)}", file=sys.stderr)
        logger.error(f"Fatal error in Memory Bank MCP server: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
