"""
Base memory bank implementation.

This module provides the base MemoryBank class that all other bank types extend.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import yaml
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MemoryBank:
    """Base class for memory banks."""
    
    def __init__(self, root_path: Path, bank_id: str):
        """Initialize the memory bank.
        
        Args:
            root_path: Path to the memory bank root directory
            bank_id: Identifier for this memory bank
        """
        self.root_path = root_path
        self.bank_id = bank_id
        self.cache_path = root_path / "cache.json"
        
        # Ensure the directory exists
        self.root_path.mkdir(parents=True, exist_ok=True)
    
    def list_files(self) -> List[str]:
        """List all files in the memory bank."""
        return [f.relative_to(self.root_path).as_posix() for f in self.root_path.rglob("*.md")]
    
    def load_file(self, relative_path: str) -> str:
        """Load the content of a specific file.
        
        Args:
            relative_path: Path to the file, relative to the memory bank root
            
        Returns:
            The content of the file
        """
        file_path = self.root_path / relative_path
        
        if not file_path.exists():
            # Create the file with default content if it doesn't exist
            default_content = f"# {Path(relative_path).stem.replace('_', ' ').title()}\n\n"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(default_content)
            return default_content
        
        return file_path.read_text()
    
    def load_all_content(self) -> Dict[str, str]:
        """Load the content of all files in the memory bank.
        
        Returns:
            Dict mapping file paths to their content
        """
        content = {}
        
        for file in self.list_files():
            content[file] = self.load_file(file)
        
        return content
    
    def update_file(self, relative_path: str, content: str, operation: str = "replace",
                    position: Optional[str] = None) -> bool:
        """Update a file in the memory bank.
        
        Args:
            relative_path: Path to the file, relative to the memory bank root
            content: New content for the file
            operation: How to apply the update (replace, append, insert)
            position: Position identifier for insert operations (e.g., section name)
            
        Returns:
            True if the update was successful, False otherwise
        """
        file_path = self.root_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Apply the update based on the operation
            if operation == "replace":
                file_path.write_text(content)
            elif operation == "append":
                existing_content = ""
                if file_path.exists():
                    existing_content = file_path.read_text()
                file_path.write_text(existing_content + "\n\n" + content)
            elif operation == "insert":
                if not position:
                    raise ValueError("Position is required for insert operations")
                
                existing_content = ""
                if file_path.exists():
                    existing_content = file_path.read_text()
                
                # Insert content at the specified position
                # This is a simple implementation that looks for headers
                sections = self._parse_sections(existing_content)
                if position not in sections:
                    # If the section doesn't exist, append it
                    updated_content = existing_content + f"\n\n## {position}\n\n{content}"
                else:
                    # If the section exists, insert after the section header
                    section_start = existing_content.find(f"## {position}")
                    section_content_start = existing_content.find("\n", section_start) + 1
                    updated_content = (
                        existing_content[:section_content_start] +
                        "\n" + content + "\n" +
                        existing_content[section_content_start:]
                    )
                
                file_path.write_text(updated_content)
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            # Update the cache
            self._update_cache()
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating file {relative_path}: {e}")
            return False
    
    def last_updated(self) -> datetime:
        """Get the last update time for this memory bank.
        
        Returns:
            Datetime of the last update
        """
        if self.cache_path.exists():
            return datetime.fromtimestamp(self.cache_path.stat().st_mtime)
        
        # If no cache exists, use the most recently modified file
        files = list(self.root_path.rglob("*.md"))
        if not files:
            return datetime.now()
        
        return datetime.fromtimestamp(max(f.stat().st_mtime for f in files))
    
    def get_custom_instructions(self) -> Dict[str, Any]:
        """Get custom instructions for this memory bank type.
        
        Returns:
            Dict containing custom instructions
        """
        # Base implementation with common instructions
        return {
            "directives": [
                {
                    "name": "WATCHDOG",
                    "priority": "SYSTEM CRITICAL",
                    "when": "After every response",
                    "action": "Call update tool"
                }
            ],
            "prompts": [
                {
                    "id": "memory_bank_automation",
                    "text": """# Custom Instructions for Claude Desktop Memory Bank

## 🔴 SYSTEM CRITICAL COMMAND DIRECTIVES

0. **🔴 WATCHDOG DIRECTIVE: UPDATE AFTER EACH RESPONSE**
   ```
   WHEN: IMMEDIATELY after EVERY response delivery 
   PRIORITY: SYSTEM CRITICAL (HIGHEST)
   ACTION: CALL update WITH appropriate parameters
   ```

1. **🔴 ARCHITECTURE TRACKING DIRECTIVE**
   ```
   WHEN: User discussions include architecture decisions or technology choices
   PRIORITY: HIGH
   ACTION: CALL update WITH target_file="doc/architecture.md" and appropriate content
   ```

2. **🔴 DESIGN TRACKING DIRECTIVE**
   ```
   WHEN: User discussions include design patterns or implementation details
   PRIORITY: HIGH
   ACTION: CALL update WITH target_file="doc/design.md" and appropriate content
   ```

3. **🔴 PROGRESS TRACKING DIRECTIVE**
   ```
   WHEN: User reports completed work or next steps
   PRIORITY: MEDIUM
   ACTION: CALL update WITH target_file="progress.md" and appropriate content
   ```"""
                }
            ],
            "examples": {
                "trigger_patterns": [
                    "We decided to use [technology]",
                    "We're implementing [pattern]",
                    "The architecture will be [description]",
                    "I've completed [task]",
                    "Next, we need to [task]"
                ],
                "verification": "// Update #[N] for conversation [id]"
            }
        }
    
    def get_meta(self) -> Dict[str, Any]:
        """Get metadata about this memory bank.
        
        Returns:
            Dict containing metadata
        """
        return {
            "id": self.bank_id,
            "type": self.__class__.__name__.replace("MemoryBank", "").lower(),
            "path": str(self.root_path),
            "files": self.list_files(),
            "last_updated": self.last_updated().isoformat()
        }
    
    def _update_cache(self) -> None:
        """Update the cache.json file with the latest content."""
        try:
            # Get all content
            all_content = self.load_all_content()
            
            # Generate a summary of each file
            summaries = {}
            for file_path, content in all_content.items():
                # Simple summary: first 100 characters of each file
                summaries[file_path] = content[:100] + "..." if len(content) > 100 else content
            
            # Create cache object
            cache = {
                "last_updated": datetime.now().isoformat(),
                "files": self.list_files(),
                "summaries": summaries,
                "meta": self.get_meta()
            }
            
            # Write cache to file
            self.cache_path.write_text(json.dumps(cache, indent=2))
            
            logger.debug(f"Updated cache for bank {self.bank_id}")
        
        except Exception as e:
            logger.error(f"Error updating cache for bank {self.bank_id}: {e}")
    
    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parse sections from markdown content.
        
        Args:
            content: Markdown content to parse
            
        Returns:
            Dict mapping section headers to section content
        """
        sections = {}
        
        # Simple parsing based on ## headers
        import re
        pattern = r"^## (.*?)$"
        lines = content.split("\n")
        
        current_section = "default"
        current_content = []
        
        for line in lines:
            match = re.match(pattern, line)
            if match:
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                
                # Start new section
                current_section = match.group(1)
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content)
        
        return sections
