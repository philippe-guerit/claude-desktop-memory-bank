"""
Tests for the integration of ContentAnalyzer with processors.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from memory_bank.content.content_analyzer import ContentAnalyzer


class TestContentAnalyzerIntegration:
    """Tests for the integration of ContentAnalyzer with processors."""

    @pytest.mark.asyncio
    async def test_process_content_method(self):
        """Test the process_content method of ContentAnalyzer."""
        with patch('memory_bank.content.processors.get_content_processor') as mock_factory:
            mock_processor = MagicMock()
            mock_processor.process_content = MagicMock()
            mock_processor.process_content.return_value = asyncio.Future()
            mock_processor.process_content.return_value.set_result({
                "target_file": "doc/architecture.md",
                "operation": "append",
                "position": None,
                "content": "Processed content",
                "metadata": {"category": "technology"}
            })
            mock_factory.return_value = mock_processor
            
            content = "# Technology Decision\n\nWe've decided to use React."
            existing_cache = {"doc/architecture.md": "# Architecture"}
            
            result = await ContentAnalyzer.process_content(
                content, existing_cache, "project", processor_preference="auto"
            )
            
            assert result is not None
            assert result["target_file"] == "doc/architecture.md"
            
            # Verify the processor was called with correct arguments
            mock_factory.assert_called_once_with("auto")
            mock_processor.process_content.assert_called_once_with(
                content, existing_cache, "project"
            )

    def test_extract_key_concepts_integration(self):
        """Test the extract_key_concepts method of ContentAnalyzer."""
        with patch('memory_bank.content.processors.get_content_processor') as mock_factory:
            mock_processor = MagicMock()
            mock_processor.extract_key_concepts.return_value = {
                "technology_choices": ["React"]
            }
            mock_factory.return_value = mock_processor
            
            content = "# Technology Decision\n\nWe've decided to use React."
            
            concepts = ContentAnalyzer.extract_key_concepts(content)
            
            assert concepts == {"technology_choices": ["React"]}
            mock_factory.assert_called_once_with("rule")
            mock_processor.extract_key_concepts.assert_called_once_with(content)

    @pytest.mark.asyncio
    async def test_fallback_to_basic_analysis(self):
        """Test fallback to basic analysis when processor encounters an error."""
        with patch('memory_bank.content.processors.get_content_processor') as mock_factory:
            mock_processor = MagicMock()
            mock_processor.process_content = MagicMock()
            mock_processor.process_content.side_effect = Exception("Processor error")
            mock_factory.return_value = mock_processor
            
            content = "# Technology Decision\n\nWe've decided to use React."
            existing_cache = {"doc/architecture.md": "# Architecture"}
            
            # This should fall back to the basic analysis
            result = await ContentAnalyzer.process_content(
                content, existing_cache, "project"
            )
            
            assert result is not None
            # Check that we got a result from basic analysis
            assert "target_file" in result
            assert "operation" in result
            assert "category" in result
            # Should be either "technology" or "default" based on pattern matching
            assert result["category"] in ["technology", "default"]
