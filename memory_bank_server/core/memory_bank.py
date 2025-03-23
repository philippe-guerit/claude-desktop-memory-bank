"""
Core business logic for Memory Bank management.

This module contains pure, framework-agnostic functions for
managing memory banks, independent of the FastMCP integration.
"""

import os
from typing import Dict, List, Optional, Any

async def start_memory_bank(
    context_service,
    prompt_name: Optional[str] = None,
    auto_detect: bool = True,
    current_path: Optional[str] = None,
    force_type: Optional[str] = None
) -> Dict[str, Any]:
    """Core business logic for starting a memory bank.
    
    Args:
        context_service: The context service instance
        prompt_name: Optional name of the prompt to load
        auto_detect: Whether to automatically detect repositories
        current_path: Path to check for repository
        force_type: Force a specific memory bank type
        
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
        detected_repo = await detect_repository(context_service, current_path)
        
        if detected_repo:
            actions_taken.append(f"Detected repository: {detected_repo.get('name', '')}")
    
    # Step 2: Initialize repository memory bank if needed
    if detected_repo and not force_type:
        # Check if memory bank exists for this repository
        memory_bank_path = detected_repo.get('memory_bank_path')
        if not memory_bank_path or not os.path.exists(memory_bank_path):
            repo_memory_bank = await initialize_repository_memory_bank(
                context_service,
                detected_repo.get('path', '')
            )
            actions_taken.append(f"Initialized repository memory bank for: {detected_repo.get('name', '')}")
            selected_memory_bank = repo_memory_bank
        else:
            actions_taken.append(f"Using existing repository memory bank: {detected_repo.get('name', '')}")
    
    # Step 3: Select appropriate memory bank based on detection or force_type
    if force_type:
        if force_type == "global":
            selected_memory_bank = await select_memory_bank(context_service)
            actions_taken.append("Forced selection of global memory bank")
        elif force_type.startswith("project:"):
            project_name = force_type.split(":", 1)[1]
            selected_memory_bank = await select_memory_bank(
                context_service, 
                type="project", 
                project_name=project_name
            )
            actions_taken.append(f"Forced selection of project memory bank: {project_name}")
        elif force_type.startswith("repository:"):
            repo_path = force_type.split(":", 1)[1]
            selected_memory_bank = await select_memory_bank(
                context_service,
                type="repository",
                repository_path=repo_path
            )
            actions_taken.append(f"Forced selection of repository memory bank: {repo_path}")
        else:
            actions_taken.append(f"Warning: Invalid force_type: {force_type}. Using default selection.")
            
    elif detected_repo and not selected_memory_bank:
        # We detected a repo but didn't initialize a memory bank (it already existed)
        selected_memory_bank = await select_memory_bank(
            context_service,
            type="repository",
            repository_path=detected_repo.get('path', '')
        )
        actions_taken.append(f"Selected repository memory bank: {detected_repo.get('name', '')}")
    
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

async def select_memory_bank(
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

async def list_memory_banks(context_service) -> Dict[str, Any]:
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

async def detect_repository(context_service, path: str) -> Optional[Dict[str, Any]]:
    """Core logic for detecting if a path is within a Git repository.
    
    Args:
        context_service: The context service instance
        path: The path to check
        
    Returns:
        Repository information if detected, None otherwise
    """
    return await context_service.repository_service.detect_repository(path)

async def initialize_repository_memory_bank(
    context_service,
    repository_path: str, 
    project_name: Optional[str] = None
) -> Dict[str, Any]:
    """Core logic for initializing a memory bank within a Git repository.
    
    Args:
        context_service: The context service instance
        repository_path: Path to the Git repository
        project_name: Optional project name to associate with this repository
        
    Returns:
        Dictionary with memory bank information
    """
    return await context_service.repository_service.initialize_repository_memory_bank(
        repository_path,
        project_name
    )

async def create_project(
    context_service,
    name: str, 
    description: str, 
    repository_path: Optional[str] = None
) -> Dict[str, Any]:
    """Core logic for creating a new project in the memory bank.
    
    Args:
        context_service: The context service instance
        name: The name of the project to create
        description: A brief description of the project
        repository_path: Optional path to a Git repository
        
    Returns:
        Dictionary with project information
    """
    return await context_service.create_project(
        name,
        description,
        repository_path
    )
