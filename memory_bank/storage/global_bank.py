"""
Global memory bank implementation.

This module provides the GlobalMemoryBank implementation for general context.
"""

from pathlib import Path
from typing import Dict, Any

from .bank import MemoryBank


class GlobalMemoryBank(MemoryBank):
    """Implementation for global memory banks."""
    
    def __init__(self, storage_root: Path, bank_id: str):
        """Initialize a global memory bank.
        
        Args:
            storage_root: Root storage path
            bank_id: Identifier for this memory bank
        """
        super().__init__(storage_root / "global" / bank_id, bank_id)
        
        # Initialize default files if they don't exist
        self._init_default_files()
    
    def _init_default_files(self) -> None:
        """Initialize default files for this bank type."""
        # Context file
        self.load_file("context.md")
        
        # Preferences file
        if not (self.root_path / "preferences.md").exists():
            self.update_file("preferences.md", """# User Preferences

## General Preferences
Preferences and patterns observed from user interactions.

## Communication Style
Notes on the user's preferred communication style and tone.

## Frequently Referenced Topics
Topics and themes that come up often in conversations.
""")
        
        # References file
        if not (self.root_path / "references.md").exists():
            self.update_file("references.md", """# References

## Frequently Cited Sources
Sources and materials referenced often by the user.

## Useful Resources
Resources that have been helpful in past conversations.
""")
    
    def get_custom_instructions(self) -> Dict[str, Any]:
        """Get custom instructions for global memory banks.
        
        Returns:
            Dict containing custom instructions
        """
        # Start with base instructions
        instructions = super().get_custom_instructions()
        
        # Add global-specific instructions
        instructions["prompts"].append({
            "id": "global_default",
            "text": """You're an assistant with access to the global memory bank. Use this context to remember
user preferences, communication style, and frequently referenced resources across conversations.

Pay special attention to patterns in how the user likes to communicate, frequent topics,
and preferred resources. Update the memory bank when you observe new preferences or 
important context that should persist across conversations."""
        })
        
        return instructions
