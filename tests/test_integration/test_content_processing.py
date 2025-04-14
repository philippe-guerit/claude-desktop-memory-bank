"""
Integration tests for content processing with the cache manager.

These tests verify that the content processing system works correctly
with the cache manager in an integrated manner.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import os

from memory_bank.cache_manager.cache_manager import CacheManager
from memory_bank.content.content_analyzer import ContentAnalyzer
from memory_bank.content.processors import get_content_processor


@pytest.fixture
def temp_bank_path():
    """Fixture to create a temporary directory for a memory bank."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


class TestContentProcessingIntegration:
    """Integration tests for content processing with cache manager."""

    @pytest.mark.asyncio
    async def test_cache_manager_update_with_processor(self, temp_bank_path):
        """Test that the cache manager correctly uses content processors for updates."""
        # Setup temporary memory bank files
        (temp_bank_path / "doc").mkdir(exist_ok=True)
        (temp_bank_path / "doc" / "architecture.md").write_text("# Architecture\n\nInitial content")
        (temp_bank_path / "readme.md").write_text("# Project Overview\n\nThis is a test project")
        
        # Create a cache manager instance
        cache_manager = CacheManager(debug_memory_dump=True)
        
        # Mock the process_content method to return a known result
        with patch('memory_bank.content.content_analyzer.ContentAnalyzer.process_content') as mock_process:
            # Since ContentAnalyzer.process_content is async but CacheManager expects a sync result
            # We need to make our mock return a simple dict directly
            mock_process.return_value = {
                "target_file": "doc/architecture.md",
                "operation": "append",
                "position": None,
                "content": "## New Technology\n\nWe've decided to use React and Express.",
                "metadata": {
                    "category": "technology",
                    "processing_method": "rule",
                    "concepts": {
                        "technology_choices": ["React", "Express"]
                    }
                }
            }
            
            # Create a test bank and add content
            bank_type = "project"
            bank_id = "test_project"
            bank_key = cache_manager.get_bank_key(bank_type, bank_id)
            
            # Override the bank path for testing
            cache_manager._bank_paths = {bank_key: temp_bank_path}
            
            # Load the bank
            cache_manager._load_bank_from_disk(bank_type, bank_id)
            
            # Add new content
            content = "# Technology Selection\n\nWe've decided to use React and Express."
            result = cache_manager.update_bank(bank_type, bank_id, content)
            
            # Verify the content was processed correctly
            mock_process.assert_called_once()
            assert mock_process.call_args[0][0] == content  # First argument (content)
            assert isinstance(mock_process.call_args[0][1], dict)  # Second argument (existing_cache)
            assert mock_process.call_args[0][2] == bank_type  # Third argument (bank_type)
            
            # Verify the result
            assert result["status"] == "success"
            
            # Verify that the bank was updated in memory
            assert bank_key in cache_manager.cache
            
            # Verify that the content was updated
            bank_content = cache_manager.cache[bank_key]
            assert "doc/architecture.md" in bank_content
            assert "## New Technology" in bank_content["doc/architecture.md"]
            
            # Verify that the change was queued for synchronization
            assert bank_key in cache_manager.pending_updates
            assert cache_manager.pending_updates[bank_key] is True

    @pytest.mark.asyncio
    async def test_rule_based_processing_integration(self, temp_bank_path):
        """Test actual rule-based content processing with the cache manager."""
        # Setup temporary memory bank files
        (temp_bank_path / "doc").mkdir(exist_ok=True)
        (temp_bank_path / "doc" / "architecture.md").write_text("# Architecture\n\nInitial content")
        (temp_bank_path / "readme.md").write_text("# Project Overview\n\nThis is a test project")
        
        # Create a cache manager instance
        cache_manager = CacheManager(debug_memory_dump=True)
        
        # Use the actual ContentAnalyzer but force rule-based processing
        with patch('memory_bank.content.processors.get_content_processor') as mock_factory:
            # Get actual rule processor but wrapped in a spy
            real_processor = get_content_processor("rule")
            mock_processor = MagicMock(wraps=real_processor)
            mock_factory.return_value = mock_processor
            
            # Create a test bank and add content
            bank_type = "project"
            bank_id = "test_project"
            bank_key = cache_manager.get_bank_key(bank_type, bank_id)
            
            # Override the bank path for testing
            cache_manager._bank_paths = {bank_key: temp_bank_path}
            
            # Load the bank
            cache_manager._load_bank_from_disk(bank_type, bank_id)
            
            # Add new content about architecture decisions
            content = """# Architecture Decision
            
            We've decided to implement a microservices architecture using Docker containers.
            This will allow us to scale individual components independently."""
            
            result = cache_manager.update_bank(bank_type, bank_id, content)
            
            # Verify the processor was used
            mock_factory.assert_called()
            mock_processor.process_content.assert_called_once()
            
            # Verify the result
            assert result["status"] == "success"
            
            # Verify that the bank was updated with the architecture content
            assert bank_key in cache_manager.cache
            assert "doc/architecture.md" in cache_manager.cache[bank_key]
            assert "microservices architecture" in cache_manager.cache[bank_key]["doc/architecture.md"]
            
            # Now add content about progress
            progress_content = """# Progress Update
            
            We've completed the initial setup of the development environment
            and defined the core API endpoints."""
            
            cache_manager.update_bank(bank_type, bank_id, progress_content)
            
            # Verify that the content was categorized correctly and sent to the proper file
            assert "doc/progress.md" in cache_manager.cache[bank_key]
            assert "initial setup" in cache_manager.cache[bank_key]["doc/progress.md"]

    @pytest.mark.asyncio
    async def test_llm_processing_fallback(self, temp_bank_path):
        """Test LLM processing with fallback to rule-based when needed."""
        # Setup temporary memory bank files
        (temp_bank_path / "doc").mkdir(exist_ok=True)
        (temp_bank_path / "doc" / "architecture.md").write_text("# Architecture\n\nInitial content")
        
        # Create a cache manager instance
        cache_manager = CacheManager(debug_memory_dump=True)
        
        # First, simulate LLM being configured but failing during processing
        with patch('memory_bank.utils.service_config.is_llm_configured') as mock_config:
            mock_config.return_value = True
            
            with patch('memory_bank.utils.service_config.llm_config') as mock_llm_config:
                mock_llm_config.get_status.return_value = "CONFIGURED"
                
                with patch('memory_bank.cache.llm.optimizer.LLMCacheOptimizer.call_llm') as mock_call_llm:
                    mock_call_llm.side_effect = Exception("LLM API error")
                    
                    # Create a test bank
                    bank_type = "project"
                    bank_id = "test_project"
                    bank_key = cache_manager.get_bank_key(bank_type, bank_id)
                    
                    # Override the bank path for testing
                    cache_manager._bank_paths = {bank_key: temp_bank_path}
                    
                    # Load the bank
                    cache_manager._load_bank_from_disk(bank_type, bank_id)
                    
                    # Add new content
                    content = """# Technology Selection
                    
                    We've decided to use GraphQL for our API layer with Apollo Client."""
                    
                    result = cache_manager.update_bank(bank_type, bank_id, content)
                    
                    # Verify the result
                    assert result["status"] == "success"
                    
                    # Even though LLM failed, we should still have processed the content
                    assert bank_key in cache_manager.cache
                    assert "doc/architecture.md" in cache_manager.cache[bank_key]
                    assert "GraphQL" in cache_manager.cache[bank_key]["doc/architecture.md"]
                    
                    # Verify that mock_call_llm was called (attempted to use LLM)
                    mock_call_llm.assert_called()
