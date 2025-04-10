"""
Project memory bank implementation.

This module provides the ProjectMemoryBank implementation for project-specific context.
"""

from pathlib import Path
from typing import Dict, Any

from .bank import MemoryBank


class ProjectMemoryBank(MemoryBank):
    """Implementation for project memory banks."""
    
    def __init__(self, storage_root: Path, bank_id: str):
        """Initialize a project memory bank.
        
        Args:
            storage_root: Root storage path
            bank_id: Identifier for this memory bank
        """
        super().__init__(storage_root / "projects" / bank_id, bank_id)
        
        # Initialize default files if they don't exist
        self._init_default_files()
    
    def _init_default_files(self) -> None:
        """Initialize default files for this bank type."""
        # Readme file
        if not (self.root_path / "readme.md").exists():
            self.update_file("readme.md", f"""# {self.bank_id.replace('_', ' ').title()}

## Project Overview
A brief description of the project.

## Goals
Project goals and objectives.

## Stakeholders
Key stakeholders and their roles.
""")
        
        # Create doc directory
        (self.root_path / "doc").mkdir(exist_ok=True)
        
        # Architecture doc
        if not (self.root_path / "doc" / "architecture.md").exists():
            self.update_file("doc/architecture.md", """# Architecture

## System Architecture
Overview of the system architecture.

## Design Decisions
Key architecture decisions and their rationale.

## Components
Major components and their interactions.
""")
        
        # Design doc
        if not (self.root_path / "doc" / "design.md").exists():
            self.update_file("doc/design.md", """# Design

## Design Principles
Core design principles for the project.

## Patterns
Design patterns used in the project.

## User Experience
Design considerations for user experience.
""")
        
        # Progress doc
        if not (self.root_path / "doc" / "progress.md").exists():
            self.update_file("doc/progress.md", """# Progress

## Current State
Current state of the project.

## Next Steps
Upcoming tasks and milestones.

## Challenges
Current challenges and how they're being addressed.
""")
        
        # Tasks file
        if not (self.root_path / "tasks.md").exists():
            self.update_file("tasks.md", """# Tasks

## Active Tasks
Tasks currently in progress.

## Backlog
Tasks to be addressed in the future.

## Completed
Recently completed tasks.
""")
    
    def get_custom_instructions(self) -> Dict[str, Any]:
        """Get custom instructions for project memory banks.
        
        Returns:
            Dict containing custom instructions
        """
        # Start with base instructions
        instructions = super().get_custom_instructions()
        
        # Add project-specific instructions
        instructions["prompts"].append({
            "id": "project_default",
            "text": f"""You're an assistant working on the project "{self.bank_id.replace('_', ' ').title()}".
Use this context to discuss project architecture, design, progress, and tasks.

Pay special attention to architecture decisions, design patterns, technical decisions,
and project progress. Update the memory bank when you observe important context that
should persist across conversations about this project."""
        })
        
        # Add project-specific directives
        instructions["directives"].append({
            "name": "PROJECT_UPDATE",
            "priority": "HIGH",
            "when": "User mentions upcoming tasks or completed work",
            "action": "CALL update with target_file='tasks.md'"
        })
        
        return instructions
