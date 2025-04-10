"""
Code memory bank implementation.

This module provides the CodeMemoryBank implementation for code repository context.
"""

from pathlib import Path
import os
from typing import Dict, Any, Optional

from .bank import MemoryBank


class CodeMemoryBank(MemoryBank):
    """Implementation for code memory banks."""
    
    def __init__(self, storage_root: Path, bank_id: str, repo_path: Optional[Path] = None):
        """Initialize a code memory bank.
        
        Args:
            storage_root: Root storage path
            bank_id: Identifier for this memory bank
            repo_path: Path to the Git repository (optional)
        """
        super().__init__(storage_root / "code" / bank_id, bank_id)
        
        # Store repo path if provided
        self.repo_path = repo_path
        
        # Initialize Git integration if this is a Git repository
        self.git_info = self._init_git()
        
        # Initialize default files if they don't exist
        self._init_default_files()
    
    def _init_git(self) -> Dict[str, Any]:
        """Initialize Git integration for this code memory bank.
        
        Returns:
            Dict containing Git information, or empty dict if not a Git repo
        """
        try:
            # Only import if needed
            import git
            
            # Check if repo_path is provided and is a Git repo
            if self.repo_path and (self.repo_path / ".git").exists():
                repo = git.Repo(self.repo_path)
                
                # Get basic Git info
                return {
                    "is_git_repo": True,
                    "repo_path": str(self.repo_path),
                    "current_branch": repo.active_branch.name,
                    "remote_url": next(repo.remotes.origin.urls) if repo.remotes else None,
                    "last_commit": {
                        "id": repo.head.commit.hexsha,
                        "message": repo.head.commit.message,
                        "author": f"{repo.head.commit.author.name} <{repo.head.commit.author.email}>",
                        "date": repo.head.commit.committed_datetime.isoformat()
                    }
                }
        except Exception as e:
            # Log error but continue
            import logging
            logging.getLogger(__name__).error(f"Error initializing Git integration: {e}")
        
        # Not a Git repo or error occurred
        return {"is_git_repo": False}
    
    def _init_default_files(self) -> None:
        """Initialize default files for this bank type."""
        # Readme file
        if not (self.root_path / "readme.md").exists():
            repo_name = self.bank_id.replace('_', ' ').title()
            if self.repo_path:
                repo_name = os.path.basename(self.repo_path)
            
            self.update_file("readme.md", f"""# {repo_name}

## Repository Overview
A brief description of the codebase.

## Structure
High-level structure of the repository.

## Key Components
Major components and their purpose.
""")
        
        # Create doc directory
        (self.root_path / "doc").mkdir(exist_ok=True)
        
        # Architecture doc
        if not (self.root_path / "doc" / "architecture.md").exists():
            self.update_file("doc/architecture.md", """# Code Architecture

## Architecture Overview
Overview of the code architecture.

## Design Patterns
Key design patterns used in the codebase.

## Dependencies
Major dependencies and their purpose.
""")
        
        # Design doc
        if not (self.root_path / "doc" / "design.md").exists():
            self.update_file("doc/design.md", """# Design

## Design Principles
Core design principles for the codebase.

## Code Organization
How the code is organized and why.

## Best Practices
Best practices followed in this codebase.
""")
        
        # API doc
        if not (self.root_path / "doc" / "api.md").exists():
            self.update_file("doc/api.md", """# API Documentation

## Public API
Documentation for the public API.

## Internal API
Documentation for the internal API.

## Examples
Example usage of key APIs.
""")
        
        # Structure file
        if not (self.root_path / "structure.md").exists():
            self.update_file("structure.md", """# Code Structure

## Directory Structure
Overview of the directory structure.

## Module Organization
How modules are organized and their dependencies.

## Key Files
Important files and their purpose.
""")
        
        # Snippets file
        if not (self.root_path / "snippets.md").exists():
            self.update_file("snippets.md", """# Code Snippets

## Important Snippets
Code snippets that are important to remember.

## Examples
Example usage of important functions or features.

## Common Patterns
Common coding patterns used in this codebase.
""")
    
    def get_custom_instructions(self) -> Dict[str, Any]:
        """Get custom instructions for code memory banks.
        
        Returns:
            Dict containing custom instructions
        """
        # Start with base instructions
        instructions = super().get_custom_instructions()
        
        # Get repo name
        repo_name = self.bank_id.replace('_', ' ').title()
        if self.repo_path:
            repo_name = os.path.basename(self.repo_path)
        
        # Add code-specific instructions
        instructions["prompts"].append({
            "id": "code_default",
            "text": f"""You're a coding assistant with access to the code memory bank for "{repo_name}".
Use this context to discuss code architecture, design patterns, API usage, and implementation details.

{f"This repository is currently on branch: {self.git_info.get('current_branch')}" if self.git_info.get('is_git_repo') else ""}

Pay special attention to architecture decisions, design patterns, and API usage.
Update the memory bank when you observe important context that should persist
across conversations about this codebase."""
        })
        
        # Add code-specific directives
        instructions["directives"].append({
            "name": "CODE_ARCHITECTURE_UPDATE",
            "priority": "HIGH",
            "when": "User discusses code architecture or design decisions",
            "action": "CALL update with target_file='doc/architecture.md'"
        })
        
        instructions["directives"].append({
            "name": "API_UPDATE",
            "priority": "HIGH",
            "when": "User discusses API design or usage",
            "action": "CALL update with target_file='doc/api.md'"
        })
        
        instructions["directives"].append({
            "name": "SNIPPET_CAPTURE",
            "priority": "MEDIUM",
            "when": "User shares important code patterns or examples",
            "action": "CALL update with target_file='snippets.md'"
        })
        
        return instructions
    
    def get_meta(self) -> Dict[str, Any]:
        """Get metadata about this memory bank.
        
        Returns:
            Dict containing metadata
        """
        # Get base metadata
        meta = super().get_meta()
        
        # Add Git info if available
        if self.git_info.get("is_git_repo"):
            meta["git"] = self.git_info
        
        return meta
