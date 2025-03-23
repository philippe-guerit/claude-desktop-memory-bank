import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from .storage_manager import StorageManager
from .memory_bank_selector import MemoryBankSelector

class ContextManager:
    def __init__(self, storage_manager: StorageManager, memory_bank_selector: MemoryBankSelector):
        self.storage_manager = storage_manager
        self.memory_bank_selector = memory_bank_selector
    
    async def initialize(self) -> None:
        """Initialize the context manager."""
        await self.storage_manager.initialize_templates()
        await self.memory_bank_selector.initialize()
    
    async def create_project(self, project_name: str, description: str, 
                         repository_path: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project with initial context files."""
        metadata = {
            "name": project_name,
            "description": description,
            "created": self.storage_manager._get_current_timestamp(),
            "lastModified": self.storage_manager._get_current_timestamp()
        }
        
        # Add repository if specified
        if repository_path:
            metadata["repository"] = repository_path
        
        # Create project memory bank
        await self.storage_manager.create_project_memory_bank(project_name, metadata)
        
        # If repository is specified, register it
        if repository_path:
            await self.storage_manager.register_repository(repository_path, project_name)
        
        # Select this memory bank
        await self.memory_bank_selector.select_memory_bank(claude_project=project_name)
        
        return metadata
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects with their metadata."""
        project_names = await self.storage_manager.get_project_memory_banks()
        projects = []
        
        for name in project_names:
            try:
                metadata = await self.storage_manager.get_project_metadata(name)
                projects.append(metadata)
            except Exception:
                # Skip projects with errors
                pass
        
        return projects
    
    async def set_memory_bank(self, 
                          claude_project: Optional[str] = None, 
                          repository_path: Optional[str] = None) -> Dict[str, Any]:
        """Set the active memory bank."""
        return await self.memory_bank_selector.select_memory_bank(
            claude_project=claude_project,
            repo_path=repository_path
        )
    
    async def get_context(self, context_type: str) -> str:
        """Get the content of a specific context file from the current memory bank."""
        memory_bank_info = await self.memory_bank_selector.get_current_memory_bank()
        memory_bank_path = memory_bank_info["path"]
        
        file_mapping = {
            "project_brief": "projectbrief.md",
            "product_context": "productContext.md",
            "system_patterns": "systemPatterns.md",
            "tech_context": "techContext.md",
            "active_context": "activeContext.md",
            "progress": "progress.md"
        }
        
        if context_type not in file_mapping:
            raise ValueError(f"Unknown context type: {context_type}")
        
        return await self.storage_manager.get_context_file(
            memory_bank_path, 
            file_mapping[context_type]
        )
    
    async def update_context(self, context_type: str, content: str) -> Dict[str, Any]:
        """Update a specific context file in the current memory bank."""
        memory_bank_info = await self.memory_bank_selector.get_current_memory_bank()
        memory_bank_path = memory_bank_info["path"]
        
        file_mapping = {
            "project_brief": "projectbrief.md",
            "product_context": "productContext.md",
            "system_patterns": "systemPatterns.md",
            "tech_context": "techContext.md",
            "active_context": "activeContext.md",
            "progress": "progress.md"
        }
        
        if context_type not in file_mapping:
            raise ValueError(f"Unknown context type: {context_type}")
        
        await self.storage_manager.update_context_file(
            memory_bank_path,
            file_mapping[context_type],
            content
        )
        
        return memory_bank_info
    
    async def search_context(self, query: str) -> Dict[str, List[str]]:
        """Search through context files in the current memory bank for the given query."""
        memory_bank_info = await self.memory_bank_selector.get_current_memory_bank()
        memory_bank_path = memory_bank_info["path"]
        
        file_mapping = {
            "projectbrief.md": "project_brief",
            "productContext.md": "product_context",
            "systemPatterns.md": "system_patterns",
            "techContext.md": "tech_context",
            "activeContext.md": "active_context",
            "progress.md": "progress"
        }
        
        results = {}
        
        for file_name, context_type in file_mapping.items():
            try:
                content = await self.storage_manager.get_context_file(
                    memory_bank_path, 
                    file_name
                )
                
                # Simple search implementation - can be improved
                if query.lower() in content.lower():
                    lines = content.split('\n')
                    matching_lines = [
                        line.strip() for line in lines 
                        if query.lower() in line.lower()
                    ]
                    if matching_lines:
                        results[context_type] = matching_lines
            except Exception:
                # Skip files with errors
                pass
        
        return results
    
    async def get_all_context(self) -> Dict[str, str]:
        """Get all context files from the current memory bank."""
        memory_bank_info = await self.memory_bank_selector.get_current_memory_bank()
        memory_bank_path = memory_bank_info["path"]
        
        file_mapping = {
            "project_brief": "projectbrief.md",
            "product_context": "productContext.md",
            "system_patterns": "systemPatterns.md",
            "tech_context": "techContext.md",
            "active_context": "activeContext.md",
            "progress": "progress.md"
        }
        
        result = {}
        
        for context_type, file_name in file_mapping.items():
            try:
                content = await self.storage_manager.get_context_file(
                    memory_bank_path,
                    file_name
                )
                result[context_type] = content
            except Exception:
                # Skip files with errors
                result[context_type] = f"Error retrieving {context_type}"
        
        return result
    
    async def detect_repository(self, path: str) -> Optional[Dict[str, Any]]:
        """Detect if a path is within a Git repository."""
        return await self.memory_bank_selector.detect_repository(path)
    
    async def initialize_repository_memory_bank(self, repo_path: str, 
                                           claude_project: Optional[str] = None) -> Dict[str, Any]:
        """Initialize a repository memory bank."""
        return await self.memory_bank_selector.initialize_repository_memory_bank(
            repo_path, 
            claude_project
        )
    
    async def get_memory_banks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available memory banks."""
        return await self.memory_bank_selector.get_all_memory_banks()
    
    async def get_current_memory_bank(self) -> Dict[str, Any]:
        """Get information about the current memory bank."""
        return await self.memory_bank_selector.get_current_memory_bank()
        
    async def bulk_update_context(self, updates: Dict[str, str]) -> Dict[str, Any]:
        """Update multiple context files in the current memory bank in one operation.
        
        Args:
            updates: Dictionary mapping context_type to content
            
        Returns:
            Information about the current memory bank
        """
        memory_bank_info = await self.memory_bank_selector.get_current_memory_bank()
        memory_bank_path = memory_bank_info["path"]
        
        file_mapping = {
            "project_brief": "projectbrief.md",
            "product_context": "productContext.md",
            "system_patterns": "systemPatterns.md",
            "tech_context": "techContext.md",
            "active_context": "activeContext.md",
            "progress": "progress.md"
        }
        
        # Validate all context types before updating
        for context_type in updates.keys():
            if context_type not in file_mapping:
                raise ValueError(f"Unknown context type: {context_type}")
        
        # Update all specified context files
        for context_type, content in updates.items():
            await self.storage_manager.update_context_file(
                memory_bank_path,
                file_mapping[context_type],
                content
            )
        
        return memory_bank_info
    
    async def auto_summarize_context(self, conversation_text: str) -> Dict[str, str]:
        """Extract relevant information from conversation and create context summaries.
        
        Args:
            conversation_text: Text of the conversation to summarize
            
        Returns:
            Dictionary of suggested context updates by context type
        """
        # This would ideally use more sophisticated NLP techniques
        # For now, we'll implement a simple keyword-based approach
        
        # Define keyword categories for each context type
        keywords = {
            "project_brief": ["purpose", "goal", "objective", "requirement", "scope", "timeline"],
            "product_context": ["problem", "solution", "user", "stakeholder", "experience"],
            "system_patterns": ["architecture", "pattern", "design", "relationship", "structure"],
            "tech_context": ["technology", "setup", "framework", "library", "dependency", "constraint"],
            "active_context": ["focus", "current", "change", "recent", "next", "decision"],
            "progress": ["complete", "finish", "done", "progress", "pending", "issue", "block"]
        }
        
        result = {}
        
        # Get existing context
        all_context = await self.get_all_context()
        
        # Split conversation into paragraphs
        paragraphs = conversation_text.split('\n\n')
        
        # Categorize paragraphs by context type based on keywords
        for context_type, terms in keywords.items():
            # Filter paragraphs containing keywords for this context type
            relevant_paragraphs = []
            for paragraph in paragraphs:
                if any(term.lower() in paragraph.lower() for term in terms):
                    relevant_paragraphs.append(paragraph)
            
            # If we found relevant content, create a summary
            if relevant_paragraphs:
                # Create a suggested update combining existing content and new content
                existing_content = all_context.get(context_type, "")
                
                # Format new content with timestamp and header
                from datetime import datetime
                timestamp = datetime.utcnow().strftime("%Y-%m-%d")
                new_content = f"\n\n## Update {timestamp}\n\n"
                new_content += "\n\n".join(relevant_paragraphs)
                
                # Combine existing and new content
                result[context_type] = existing_content + new_content
        
        return result
    
    async def prune_context(self, max_age_days: int = 90) -> Dict[str, Any]:
        """Remove outdated information from context files.
        
        Args:
            max_age_days: Maximum age of content to retain (in days)
            
        Returns:
            Information about what was pruned
        """
        memory_bank_info = await self.memory_bank_selector.get_current_memory_bank()
        memory_bank_path = memory_bank_info["path"]
        
        file_mapping = {
            "project_brief": "projectbrief.md",
            "product_context": "productContext.md",
            "system_patterns": "systemPatterns.md",
            "tech_context": "techContext.md",
            "active_context": "activeContext.md",
            "progress": "progress.md"
        }
        
        from datetime import datetime, timedelta
        import re
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        result = {}
        
        # Process each context file
        for context_type, file_name in file_mapping.items():
            try:
                # Get current content
                content = await self.storage_manager.get_context_file(
                    memory_bank_path,
                    file_name
                )
                
                # Look for date headers in the format "## Update YYYY-MM-DD"
                sections = re.split(r'(## Update \d{4}-\d{2}-\d{2})', content)
                
                # First section is the main content without a date
                pruned_content = sections[0]
                
                # Track what we keep and remove
                kept_sections = 0
                pruned_sections = 0
                
                # Process dated sections
                for i in range(1, len(sections), 2):
                    if i+1 < len(sections):
                        date_header = sections[i]
                        section_content = sections[i+1]
                        
                        # Extract date from header
                        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_header)
                        if date_match:
                            date_str = date_match.group(1)
                            try:
                                section_date = datetime.strptime(date_str, "%Y-%m-%d")
                                
                                # Keep section if it's newer than the cutoff date
                                if section_date >= cutoff_date:
                                    pruned_content += date_header + section_content
                                    kept_sections += 1
                                else:
                                    pruned_sections += 1
                            except ValueError:
                                # If date parsing fails, keep the section
                                pruned_content += date_header + section_content
                                kept_sections += 1
                        else:
                            # If no date found, keep the section
                            pruned_content += date_header + section_content
                            kept_sections += 1
                
                # Only update if something was pruned
                if pruned_sections > 0:
                    await self.storage_manager.update_context_file(
                        memory_bank_path,
                        file_name,
                        pruned_content
                    )
                    
                    result[context_type] = {
                        "pruned_sections": pruned_sections,
                        "kept_sections": kept_sections
                    }
            except Exception as e:
                # Skip files with errors
                result[context_type] = {"error": str(e)}
        
        return result
