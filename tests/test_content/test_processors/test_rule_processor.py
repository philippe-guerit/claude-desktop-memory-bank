"""
Tests for the rule-based content processor.
"""

import pytest
import asyncio
from typing import Dict, Any

from memory_bank.content.processors import RuleBasedProcessor, ContentProcessor


class TestRuleBasedProcessor:
    """Tests for the rule-based processor."""

    def test_initialization(self):
        """Test that the rule-based processor can be initialized."""
        processor = RuleBasedProcessor()
        assert processor is not None
        assert isinstance(processor, ContentProcessor)

    def test_extract_key_concepts(self):
        """Test key concept extraction with rule-based processor."""
        processor = RuleBasedProcessor()
        
        content = """# Architecture Decision
        
        We decided to use PostgreSQL for our database as it offers the best combination
        of features we need. Additionally, we'll be implementing the repository pattern
        for data access."""
        
        concepts = processor.extract_key_concepts(content)
        
        assert isinstance(concepts, dict)
        assert "architecture_decisions" in concepts
        assert any("PostgreSQL" in concept for concept in concepts.get("architecture_decisions", []))
        assert "implementation_patterns" in concepts
        assert any("repository pattern" in concept for concept in concepts.get("implementation_patterns", []))

    def test_determine_content_relationships(self):
        """Test relationship determination with rule-based processor."""
        processor = RuleBasedProcessor()
        
        content = """# API Documentation
        
        Our API uses RESTful principles and will be documented in doc/api.md.
        See the code structure in structure.md for more details."""
        
        existing_cache = {
            "doc/api.md": "# API Documentation\n\nOur API has the following endpoints...",
            "structure.md": "# Code Structure\n\nThe code is organized into the following modules...",
            "readme.md": "# Project Overview\n\nThis is a sample project..."
        }
        
        relationships = processor.determine_content_relationships(content, existing_cache)
        
        assert isinstance(relationships, dict)
        assert "referenced_files" in relationships
        assert "doc/api.md" in relationships["referenced_files"]
        assert "structure.md" in relationships["referenced_files"]

    @pytest.mark.asyncio
    async def test_process_content(self):
        """Test the full content processing with rule-based processor."""
        processor = RuleBasedProcessor()
        
        content = """# Technology Selection
        
        We've decided to use React for the frontend and Express for the backend.
        This gives us a solid JavaScript-based stack with good ecosystem support."""
        
        existing_cache = {
            "doc/architecture.md": "# Architecture\n\nThe system is based on microservices...",
            "readme.md": "# Project Overview\n\nThis is a sample project..."
        }
        
        result = await processor.process_content(content, existing_cache, "project")
        
        assert isinstance(result, dict)
        assert "target_file" in result
        assert result["target_file"] == "doc/architecture.md"  # Should match technology category
        assert "operation" in result
        assert "content" in result
        assert "metadata" in result
        assert "timestamp" in result["metadata"]
        assert "concepts" in result["metadata"]
        assert "relationships" in result["metadata"]
