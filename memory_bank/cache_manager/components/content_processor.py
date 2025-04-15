"""
Content processing functionality for the cache manager.

This module provides content processing and analysis for memory banks.
"""

import logging
from typing import Dict, Any

from ..content_processing import ContentProcessor as BaseContentProcessor

logger = logging.getLogger(__name__)


class ContentProcessor:
    """Processes and analyzes memory bank content."""

    def __init__(self, cache_manager):
        """Initialize the content processor.
        
        Args:
            cache_manager: The cache manager instance
        """
        self.cache_manager = cache_manager
        
    @staticmethod
    def process_content(content: str, existing_cache: Dict[str, str]) -> Dict[str, str]:
        """Process content using LLM-based or rule-based approach.
        
        Args:
            content: New content to process
            existing_cache: Existing cache content
            
        Returns:
            Processed content
        """
        return BaseContentProcessor.process_content(content, existing_cache)
        
    @staticmethod
    def merge_content(existing: Dict[str, str], new: Dict[str, str]) -> Dict[str, str]:
        """Merge new content with existing content.
        
        Args:
            existing: Existing content
            new: New content to merge
            
        Returns:
            Merged content
        """
        return BaseContentProcessor.merge_content(existing, new)
