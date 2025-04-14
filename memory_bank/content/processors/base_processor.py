"""
Base content processor for memory bank.

Defines the interface for content processors that analyze, categorize, 
and organize content for memory banks.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)


class ContentProcessor(ABC):
    """Base class for content processors.
    
    Content processors analyze new content from conversations to determine 
    appropriate categorization, storage location, and contextual relationships.
    
    All concrete implementations must implement the process_content method.
    """
    
    @abstractmethod
    async def process_content(self, content: str, existing_cache: Dict[str, str],
                         bank_type: str) -> Dict[str, Any]:
        """Process content to determine target file, operation, etc.
        
        Args:
            content: New conversation content to process
            existing_cache: Existing memory bank content
            bank_type: Type of bank (global, project, code)
            
        Returns:
            Dict with processing results including:
            - target_file: Path to target file within the bank
            - operation_type: Operation to perform (append, replace, insert)
            - content: Processed content (may be modified from input)
            - metadata: Additional metadata for the content
            - position: Position identifier for insert operations
        """
        pass
        
    @abstractmethod
    def extract_key_concepts(self, content: str) -> Dict[str, List[str]]:
        """Extract key concepts from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Dict mapping concept categories to lists of key concepts
        """
        pass
        
    @abstractmethod
    def determine_content_relationships(self, content: str, 
                                   existing_cache: Dict[str, str]) -> Dict[str, List[str]]:
        """Determine relationships between new content and existing cache content.
        
        Args:
            content: New content to analyze
            existing_cache: Existing memory bank content
            
        Returns:
            Dict mapping relationship types to lists of related files
        """
        pass
