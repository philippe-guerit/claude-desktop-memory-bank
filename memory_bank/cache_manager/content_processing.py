"""
Content processing functionality for cache manager.

This module provides methods for processing and merging content.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ContentProcessor:
    """Handles content processing and merging."""
    
    @staticmethod
    def process_content(content: str, existing_cache: Dict[str, str], bank_type: str = "global") -> Dict[str, str]:
        """Process content using ContentAnalyzer with LLM-based or rule-based processing.
        
        Args:
            content: New content to process
            existing_cache: Existing cache content
            bank_type: Type of bank (global, project, code)
            
        Returns:
            Processed content as a dict mapping file paths to content
        """
        try:
            # Import the new components from Phase 5
            from memory_bank.content.content_analyzer import ContentAnalyzer
            from memory_bank.content.async_bridge import AsyncBridge
            
            # Use the AsyncBridge to safely call the async ContentAnalyzer
            try:
                processing_result = AsyncBridge.process_content_sync(
                    ContentAnalyzer.process_content,
                    content,
                    existing_cache,
                    bank_type
                )
                
                # Convert the result to the format expected by the cache manager
                if processing_result and "target_file" in processing_result:
                    target_file = processing_result.get("target_file", "context.md")
                    file_content = processing_result.get("content", content)
                    
                    # Create a dict with the target file as key
                    return {target_file: file_content}
                    
            except Exception as e:
                logger.warning(f"Error using AsyncBridge for content processing: {e}")
                logger.info("Falling back to rule-based processing")
            
            # Fallback to rule-based processing if ContentAnalyzer integration fails
            return ContentProcessor.process_with_rules(content, existing_cache)
            
        except Exception as e:
            logger.error(f"Error processing content: {e}")
            logger.info("Falling back to rule-based processing")
            return ContentProcessor.process_with_rules(content, existing_cache)
    
    @staticmethod
    def process_with_rules(content: str, existing_cache: Dict[str, str]) -> Dict[str, str]:
        """Process content with rule-based approach.
        
        Args:
            content: New content to process
            existing_cache: Existing cache content
            
        Returns:
            Processed content as a dict mapping file paths to content
        """
        # In Phase 1, return a simple structure with context.md as the target
        # This will be enhanced in Phase 5 with proper content processing
        return {"context.md": content}
    
    @staticmethod
    def merge_content(existing_content: Dict[str, str], new_content: Dict[str, str]) -> Dict[str, str]:
        """Merge new content with existing content.
        
        Args:
            existing_content: Existing content in the cache
            new_content: New content to merge
            
        Returns:
            Merged content
        """
        result = existing_content.copy()
        
        # For each file in new content
        for file_path, content in new_content.items():
            if file_path in result:
                # Append to existing file
                result[file_path] = result[file_path] + "\n\n" + content
            else:
                # Create new file
                result[file_path] = content
        
        return result
