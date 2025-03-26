"""
Core business logic for Memory Bank management.

This module contains pure, framework-agnostic functions for
managing memory banks, independent of the FastMCP integration.
"""

import os
from typing import Dict, List, Optional, Any

async def activate(
    context_service,
    prompt_name: Optional[str] = None,
    auto_detect: bool = True,
    current_path: Optional[str] = None,
    force_type: Optional[str] = None,
    project_name: Optional[str] = None,
    project_description: Optional[str] = None
) -> Dict[str, Any]:
    """Core business logic for activating a memory bank.
    
    Args:
        context_service: The context service instance
        prompt_name: Optional name of the prompt to load
        auto_detect: Whether to automatically detect repositories
        current_path: Path to check for repository
        force_type: Force a specific memory bank type
        project_name: Optional name for creating a new project
        project_description: Optional description for creating a new project
        
    Returns:
        Dictionary containing the result data
    """
    # Initialize tracking variables
    actions_taken = []
    selected_memory_bank = None
    
    # Use current working directory if path not provided
    if not current_path:
        current_path = os.getcwd()
    
    # Step 1: Auto-detect repository if enabled
    detected_repo = None
    if auto_detect and not force_type:
        detected_repo = await _detect_repository_internal(context_service, current_path)
        
        if detected_repo:
            actions_taken.append(f"Detected repository: {detected_repo.get('name', '')}")
    
    # Step 2: Handle project creation if requested
    project_created = False
    if project_name and project_description:
        # Skip project creation when in a repository with existing memory bank
        # unless explicitly forced to create a project
        should_create_project = True
        
        if detected_repo and not force_type:
            # Check if memory bank exists for this repository
            memory_bank_path = detected_repo.get('memory_bank_path')
            has_memory_bank = memory_bank_path and os.path.exists(memory_bank_path)
            
            if has_memory_bank:
                # Skip project creation if in a repository with existing memory bank
                should_create_project = False
                actions_taken.append(f"Skipped project creation - using existing repository memory bank")
        
        if should_create_project:
            try:
                # If we detected a repository and no force_type is set, associate with repository
                repo_path = detected_repo.get('path') if detected_repo and not force_type else None
                
                # Create the project
                project_info = await _create_project_internal(
                    context_service,
                    project_name,
                    project_description,
                    repo_path
                )
                
                actions_taken.append(f"Created project: {project_name}")
                if repo_path:
                    actions_taken.append(f"Associated project with repository: {detected_repo.get('name', '')}")
                    
                # Set selected memory bank to the new project
                if not force_type:
                    selected_memory_bank = await context_service.set_memory_bank(
                        type="project",
                        project_name=project_name
                    )
                    actions_taken.append(f"Selected new project memory bank: {project_name}")
                    project_created = True
                    
            except Exception as e:
                error_msg = str(e)
                actions_taken.append(f"Failed to create project: {error_msg}")
    
    # Step 3: Initialize repository memory bank if needed and no project was created
    if detected_repo and not force_type and not selected_memory_bank:
        # Check if memory bank exists for this repository
        memory_bank_path = detected_repo.get('memory_bank_path')
        if not memory_bank_path or not os.path.exists(memory_bank_path):
            # Initialize and select in one step
            selected_memory_bank = await _initialize_repository_memory_bank_internal(
                context_service,
                detected_repo.get('path', '')
            )
            actions_taken.append(f"Initialized repository memory bank for: {detected_repo.get('name', '')}")
        else:
            # If memory bank exists, explicitly select it here
            actions_taken.append(f"Using existing repository memory bank: {detected_repo.get('name', '')}")
            # This is the key fix - select the memory bank immediately here
            selected_memory_bank = await context_service.set_memory_bank(
                type="repository",
                repository_path=detected_repo.get('path', '')
            )
            actions_taken.append(f"Selected repository memory bank: {detected_repo.get('name', '')}")
    
    # Step 4: Handle forced memory bank type if specified
    if force_type and not selected_memory_bank:
        if force_type == "global":
            selected_memory_bank = await context_service.set_memory_bank()
            actions_taken.append("Forced selection of global memory bank")
        elif force_type.startswith("project:"):
            project_name = force_type.split(":", 1)[1]
            selected_memory_bank = await context_service.set_memory_bank(
                type="project", 
                project_name=project_name
            )
            actions_taken.append(f"Forced selection of project memory bank: {project_name}")
        elif force_type.startswith("repository:"):
            repo_path = force_type.split(":", 1)[1]
            selected_memory_bank = await context_service.set_memory_bank(
                type="repository",
                repository_path=repo_path
            )
            actions_taken.append(f"Forced selection of repository memory bank: {repo_path}")
        else:
            actions_taken.append(f"Warning: Invalid force_type: {force_type}. Using default selection.")
    
    # If no memory bank was selected yet, get the current memory bank
    if not selected_memory_bank:
        selected_memory_bank = await context_service.get_current_memory_bank()
        actions_taken.append(f"Using current memory bank: {selected_memory_bank['type']}")
    
    # Format result
    result = {
        "selected_memory_bank": selected_memory_bank,
        "actions_taken": actions_taken,
        "prompt_name": prompt_name
    }
    
    return result

async def select(
    context_service,
    type: str = "global", 
    project_name: Optional[str] = None, 
    repository_path: Optional[str] = None
) -> Dict[str, Any]:
    """Core logic for selecting a memory bank.
    
    Args:
        context_service: The context service instance
        type: The type of memory bank to use
        project_name: The name of the project
        repository_path: The path to the repository
        
    Returns:
        Dictionary with memory bank information
    """
    return await context_service.set_memory_bank(
        type=type,
        project_name=project_name,
        repository_path=repository_path
    )

async def list(context_service) -> Dict[str, Any]:
    """Core logic for listing all available memory banks.
    
    Args:
        context_service: The context service instance
        
    Returns:
        Dictionary with current memory bank and all available memory banks
    """
    current_memory_bank = await context_service.get_current_memory_bank()
    all_memory_banks = await context_service.get_memory_banks()
    
    return {
        "current": current_memory_bank,
        "available": all_memory_banks
    }



# Internal helper functions for memory-bank-start
# These are not exposed directly as tools but used by memory-bank-start internally

async def _detect_repository_internal(context_service, path: str) -> Optional[Dict[str, Any]]:
    """Internal helper for detecting repositories.
    Not exposed as a tool - used by memory-bank-start.
    """
    return await context_service.repository_service.detect_repository(path)

async def _initialize_repository_memory_bank_internal(
    context_service,
    repository_path: str, 
    project_name: Optional[str] = None
) -> Dict[str, Any]:
    """Internal helper for initializing repository memory banks.
    Not exposed as a tool - used by memory-bank-start.
    """
    return await context_service.repository_service.initialize_repository_memory_bank(
        repository_path,
        project_name
    )

async def _create_project_internal(
    context_service,
    name: str, 
    description: str, 
    repository_path: Optional[str] = None
) -> Dict[str, Any]:
    """Internal helper for creating projects.
    Not exposed as a tool - used by memory-bank-start.
    """
    return await context_service.create_project(
        name,
        description,
        repository_path
    )
