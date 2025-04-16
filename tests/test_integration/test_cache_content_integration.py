"""
Integration tests for CacheManager and ContentProcessor interaction.

Verifies that the CacheManager correctly interacts with the content
processing components across the async/sync boundary.
"""

import pytest
from unittest.mock import patch, MagicMock
import asyncio
import tempfile
from pathlib import Path
import shutil
from typing import Dict, Any

from memory_bank.cache_manager.cache_manager import CacheManager
from memory_bank.content.content_analyzer import ContentAnalyzer


class TestCacheContentIntegration:
    """Integration tests for CacheManager and ContentProcessor."""
    
    @pytest.fixture
    def temp_storage_root(self):
        """Create a temporary directory for storage."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
        
    @pytest.fixture
    def cache_manager(self, temp_storage_root):
        """Create a CacheManager instance with temporary storage."""
        # Reset the singleton instance
        CacheManager._instance = None
        
        # Create a cache manager with debug enabled
        manager = CacheManager.get_instance(debug_memory_dump=True)
        
        # Override the storage root
        manager.storage_root = temp_storage_root
        manager.storage_root.mkdir(parents=True, exist_ok=True)
        
        # Set up subdirectories
        (temp_storage_root / "global").mkdir(parents=True, exist_ok=True)
        (temp_storage_root / "projects").mkdir(parents=True, exist_ok=True)
        (temp_storage_root / "code").mkdir(parents=True, exist_ok=True)
        
        # Debug dump path
        manager.debug_dump_path = temp_storage_root / "cache_memory_dump.json"
        
        yield manager
        
        # Cleanup
        manager.close()
        
    @pytest.fixture
    def mock_content_analyzer(self):
        """Mock the ContentAnalyzer for testing."""
        with patch('memory_bank.content.content_analyzer.ContentAnalyzer') as mock_analyzer:
            # Set up the process_content mock to return a test result
            mock_analyzer.process_content = MagicMock()
            
            # Create a coroutine function that resolves to a test result
            async def mock_process(*args, **kwargs):
                return {
                    "target_file": "doc/architecture.md",
                    "operation": "append",
                    "content": "# Test Content\n\nThis is test content.",
                    "category": "architecture",
                    "confidence": 0.9
                }
                
            # Assign the mock coroutine
            mock_analyzer.process_content.side_effect = mock_process
            
            yield mock_analyzer
    
    def test_update_bank_content_processing(self, cache_manager, mock_content_analyzer):
        """Test that CacheManager correctly processes content during update."""
        # Setup test data
        bank_type = "project"
        bank_id = "test_project"
        content = """# Architecture Decision
        
        We've decided to use a microservice architecture for this project.
        This will allow us to scale each component independently."""
        
        # Update the bank
        result = cache_manager.update_bank(bank_type, bank_id, content)
        
        # Verify the result
        assert result["status"] == "success"
        
        # Verify the cache was updated
        bank_key = cache_manager.get_bank_key(bank_type, bank_id)
        assert bank_key in cache_manager.cache
        
        # Verify ContentAnalyzer was called
        mock_content_analyzer.process_content.assert_called_once()
        
        # Verify the content was processed correctly
        bank_content = cache_manager.get_bank(bank_type, bank_id)
        assert "doc/architecture.md" in bank_content
        assert "# Test Content" in bank_content["doc/architecture.md"]
    
    # Redundant test removed - this functionality is already tested in:
    # 1. test_llm_processing_fallback in test_content_processing.py
    # 2. test_llm_not_configured_fallback in test_llm_processor.py
    
    @pytest.mark.asyncio
    async def test_async_content_processing_integration(self, cache_manager):
        """Test the full async integration with real content processing."""
        # This test uses the real ContentAnalyzer without mocking
        
        # Setup test data
        bank_type = "project"
        bank_id = "test_project"
        content = """# Architecture Decision
        
        We've decided to use a microservice architecture for this project.
        This will allow us to scale each component independently."""
        
        # Update the bank
        result = cache_manager.update_bank(bank_type, bank_id, content)
        
        # Verify the result
        assert result["status"] == "success"
        
        # Verify the cache was updated
        bank_key = cache_manager.get_bank_key(bank_type, bank_id)
        assert bank_key in cache_manager.cache
        
        # Get the bank content
        bank_content = cache_manager.get_bank(bank_type, bank_id)
        
        # The content should be processed and stored in a file
        # The exact file depends on the content processing logic
        assert len(bank_content) > 0
        
        # At least one file should contain our content
        content_found = False
        for file_content in bank_content.values():
            if "microservice architecture" in file_content:
                content_found = True
                break
                
        assert content_found, "Processed content not found in any file"
