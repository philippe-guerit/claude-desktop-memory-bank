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
        """Initialize default files for the standardized project template."""
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
        
        # Objectives doc
        if not (self.root_path / "doc" / "objectives.md").exists():
            self.update_file("doc/objectives.md", """# Project Objectives

## Primary Goals
Main objectives of the project.

## Success Criteria
How success will be measured.

## Timeline
Expected timeline and milestones.
""")
        
        # Decisions doc
        if not (self.root_path / "doc" / "decisions.md").exists():
            self.update_file("doc/decisions.md", """# Key Decisions

## Technical Decisions
Important technical choices and their rationale.

## Process Decisions
Process and methodology decisions.

## Design Decisions
Key design choices and their justification.
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
        
        # References doc
        if not (self.root_path / "doc" / "references.md").exists():
            self.update_file("doc/references.md", """# Important References

## External Resources
Links to external documentation, articles, and resources.

## Internal Documents
References to internal documentation and resources.

## Standards & Guidelines
Relevant standards and guidelines for the project.
""")

        # Create notes directory
        (self.root_path / "notes").mkdir(exist_ok=True)
        
        # Meeting notes
        if not (self.root_path / "notes" / "meeting_notes.md").exists():
            self.update_file("notes/meeting_notes.md", """# Meeting Notes

## Recent Meetings
Notes from recent project meetings.

## Action Items
Action items from meetings.

## Decisions Made
Key decisions made during meetings.
""")
        
        # Ideas
        if not (self.root_path / "notes" / "ideas.md").exists():
            self.update_file("notes/ideas.md", """# Project Ideas

## Brainstorming
Ideas from brainstorming sessions.

## Future Possibilities
Potential future directions.

## Innovations
Innovative approaches being considered.
""")
        
        # Research
        if not (self.root_path / "notes" / "research.md").exists():
            self.update_file("notes/research.md", """# Research Findings

## Market Research
Findings from market research.

## Technical Research
Results of technical investigations.

## User Research
Insights from user research and feedback.
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
Use this standardized project memory bank to track objectives, decisions, progress, and project notes.

Pay special attention to key decisions, project objectives, research findings, and meeting outcomes.
Update the memory bank when you observe important information that should persist across 
conversations about this project."""
        })
        
        # Add project-specific directives
        instructions["directives"].extend([
            {
                "name": "DECISION_TRACKING",
                "priority": "HIGH",
                "when": "User mentions important decisions or technical choices",
                "action": "CALL update with target_file='doc/decisions.md'"
            },
            {
                "name": "PROGRESS_TRACKING",
                "priority": "HIGH",
                "when": "User mentions project progress, current state, or challenges",
                "action": "CALL update with target_file='doc/progress.md'"
            },
            {
                "name": "MEETING_NOTES",
                "priority": "MEDIUM",
                "when": "User discusses meeting outcomes or action items",
                "action": "CALL update with target_file='notes/meeting_notes.md'"
            },
            {
                "name": "IDEA_CAPTURE",
                "priority": "MEDIUM",
                "when": "User shares new ideas or brainstorming results",
                "action": "CALL update with target_file='notes/ideas.md'"
            },
            {
                "name": "RESEARCH_FINDINGS",
                "priority": "MEDIUM",
                "when": "User mentions research results or findings",
                "action": "CALL update with target_file='notes/research.md'"
            }
        ])
        
        return instructions
