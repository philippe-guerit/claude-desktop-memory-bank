"""
Content analysis module for memory bank.

Provides content categorization and file targeting logic with support for
both LLM-based and rule-based processing strategies.
"""

import re
import asyncio
from typing import Dict, Any, Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """Analyzes content to determine file targets and update operations."""
    
    # Content category patterns - improved pattern matching
    PATTERNS = {
        "architecture": [
            r"(?i)architecture\s+decision",
            r"(?i)decided\s+to\s+use\s+([a-z0-9_\-]+)",
            r"(?i)system\s+design",
            r"(?i)technical\s+architecture",
            r"(?i)architectural\s+approach",
            r"(?i)microservice",
            r"(?i)service\s+oriented",
            r"(?i)component\s+structure"
        ],
        "technology": [
            r"(?i)technology\s+stack",
            r"(?i)using\s+([a-z0-9_\-]+)\s+for",
            r"(?i)technical\s+stack",
            r"(?i)framework\s+selection",
            r"(?i)library\s+choice",
            r"(?i)database\s+choice",
            r"(?i)tech\s+choice"
        ],
        "design": [
            r"(?i)design\s+pattern",
            r"(?i)ui\s+design",
            r"(?i)user\s+interface",
            r"(?i)interaction\s+design",
            r"(?i)visual\s+layout",
            r"(?i)user\s+experience",
            r"(?i)ux\s+considerations"
        ],
        "api": [
            r"(?i)api\s+design",
            r"(?i)endpoint\s+definition",
            r"(?i)rest\s+interface",
            r"(?i)api\s+specification",
            r"(?i)graphql\s+schema",
            r"(?i)rest\s+endpoint",
            r"(?i)swagger\s+spec"
        ],
        "progress": [
            r"(?i)progress\s+update",
            r"(?i)status\s+report",
            r"(?i)milestone\s+complete",
            r"(?i)completed\s+tasks",
            r"(?i)current\s+status",
            r"(?i)task\s+completion",
            r"(?i)progress\s+report"
        ],
        "tasks": [
            r"(?i)todo\s+list",
            r"(?i)planned\s+tasks",
            r"(?i)action\s+items",
            r"(?i)needs\s+to\s+be\s+done",
            r"(?i)backlog\s+items",
            r"(?i)task\s+list",
            r"(?i)pending\s+work"
        ],
        "meeting": [
            r"(?i)meeting\s+summary",
            r"(?i)discussion\s+notes",
            r"(?i)discussed\s+in\s+meeting",
            r"(?i)meeting\s+outcome",
            r"(?i)team\s+discussion",
            r"(?i)meeting\s+notes",
            r"(?i)team\s+meeting"
        ],
        "code": [
            r"(?i)code\s+snippet",
            r"(?i)implementation\s+example",
            r"(?i)code\s+structure",
            r"(?i)class\s+definition",
            r"(?i)function\s+implementation",
            r"(?i)module\s+organization",
            r"(?i)pattern\s+implementation"
        ],
        "preferences": [
            r"(?i)user\s+preference",
            r"(?i)preferred\s+approach",
            r"(?i)communication\s+style",
            r"(?i)likes\s+to",
            r"(?i)prefers\s+to",
            r"(?i)user\s+likes",
            r"(?i)brief\s+responses"
        ]
    }
    
    # File mapping by bank type and category
    FILE_MAPPING = {
        "global": {
            "default": "context.md",
            "preferences": "preferences.md",
            "reference": "references.md",
            "meeting": "context.md",
            "architecture": "context.md",
            "technology": "context.md",
            "design": "context.md",
            "progress": "context.md",
            "tasks": "context.md",
            "code": "context.md",
            "api": "context.md"
        },
        "project": {
            "default": "readme.md",
            "architecture": "doc/architecture.md",
            "design": "doc/design.md",
            "progress": "doc/progress.md",
            "tasks": "tasks.md",
            "meeting": "notes/meeting_notes.md",
            "reference": "notes/research.md",
            "technology": "doc/architecture.md",
            "code": "doc/design.md",
            "api": "doc/design.md",
            "preferences": "readme.md"
        },
        "code": {
            "default": "readme.md",
            "architecture": "doc/architecture.md",
            "design": "doc/design.md",
            "api": "doc/api.md",
            "code": "snippets.md",
            "structure": "structure.md",
            "technology": "doc/architecture.md",
            "progress": "doc/progress.md",
            "tasks": "readme.md",
            "meeting": "readme.md",
            "preferences": "readme.md",
            "reference": "doc/api.md"
        }
    }
    
    @classmethod
    async def process_content(cls, content: str, existing_cache: Dict[str, str], 
                        bank_type: str, processor_preference: str = "auto") -> Dict[str, Any]:
        """Process content using the appropriate processor.
        
        This is the main entry point for content processing in the memory bank.
        It uses either LLM-based or rule-based processing based on preference
        and availability.
        
        Args:
            content: Text content to process
            existing_cache: Existing memory bank content
            bank_type: Type of bank (global, project, code)
            processor_preference: Processor preference: "auto", "llm", or "rule"
            
        Returns:
            Dict with processing results including target_file, operation, etc.
        """
        # Import here to avoid circular imports
        from memory_bank.content.processors import get_content_processor
        
        # Get the appropriate processor
        processor = get_content_processor(processor_preference)
        
        try:
            # Process the content
            result = await processor.process_content(content, existing_cache, bank_type)
            logger.info(f"Content processed using {processor.__class__.__name__}")
            
            # Cleanup resources if needed (e.g., for LLM processor)
            if hasattr(processor, 'close'):
                await processor.close()
                
            return result
            
        except Exception as e:
            logger.error(f"Error processing content: {e}")
            # Fallback to basic content analysis in case of error
            logger.info("Falling back to basic content analysis")
            return cls.determine_target_file(bank_type, content)
    
    @classmethod
    def analyze_content(cls, content: str) -> Tuple[str, float]:
        """Analyze content to determine its primary category.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Tuple of (category, confidence)
        """
        # Check title first (highest priority)
        title_match = re.search(r"(?i)^#\s*(.*?)$", content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).lower()
            
            # Direct title matches have highest priority
            for category in cls.PATTERNS.keys():
                category_name = category.lower()
                if category_name in title:
                    return category, 1.0
            
            # Check specific patterns in the title
            for category, patterns in cls.PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, title):
                        return category, 0.9
        
        # Count matches for each category in the full content
        scores = {}
        for category, patterns in cls.PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, content)
                score += len(matches)
            scores[category] = score
        
        # Find the category with the highest score
        if not scores or max(scores.values()) == 0:
            return "default", 0.0
        
        best_category = max(scores.items(), key=lambda x: x[1])
        total_matches = sum(scores.values())
        confidence = best_category[1] / total_matches if total_matches > 0 else 0
        
        return best_category[0], confidence
    
    @classmethod
    def determine_target_file(cls, bank_type: str, content: str) -> Dict[str, Any]:
        """Determine target file and operation based on content analysis.
        
        This method is maintained for backward compatibility and is used as a fallback
        when the processors are unavailable or encounter errors.
        
        Args:
            bank_type: Type of bank (global, project, code)
            content: Content to analyze
            
        Returns:
            Dict with target_file, operation, and position
        """
        # Analyze content
        category, confidence = cls.analyze_content(content)
        
        # Default to append operation
        operation = "append"
        position = None
        
        # Map category to target file
        if bank_type in cls.FILE_MAPPING:
            target_file = cls.FILE_MAPPING[bank_type].get(
                category, cls.FILE_MAPPING[bank_type]["default"]
            )
        else:
            target_file = "context.md"  # Fallback
        
        # Create subdirectories if needed
        if "/" in target_file and target_file.startswith("notes/"):
            operation = "append"  # Always append to notes
        
        return {
            "target_file": target_file,
            "operation": operation,
            "position": position,
            "category": category,
            "confidence": confidence
        }
        
    @classmethod
    def extract_key_concepts(cls, content: str) -> Dict[str, List[str]]:
        """Extract key concepts from content.
        
        This is a basic implementation maintained for backward compatibility.
        For more advanced concept extraction, use a ContentProcessor.
        
        Args:
            content: Content to analyze
            
        Returns:
            Dict mapping concept categories to lists of key concepts
        """
        # Import here to avoid circular imports
        from memory_bank.content.processors import get_content_processor
        
        # Get a rule-based processor for synchronous operation
        processor = get_content_processor("rule")
        return processor.extract_key_concepts(content)
