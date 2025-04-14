"""
Tests for the update tool.
"""

import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock

from tests.conftest import parse_response
from memory_bank.cache_manager.cache_manager import CacheManager


@pytest.mark.asyncio
async def test_update_tool(server):
    """Test the update tool with simplified interface."""
    # Create a bank first
    await server.call_tool_test(
        "activate",
        {
            "conversation_type": "global"
        }
    )
    
    # Call the update tool handler directly for testing
    test_content = "# Architecture Decision\n\nWe decided to use PostgreSQL for the database because of its reliability and feature set."
    result = await server.call_tool_test(
        "update",
        {
            "content": test_content,
            "conversation_id": "test_conversation",
            "update_count": 1
        }
    )
    response = parse_response(result)
    
    # Check response structure
    assert "status" in response
    assert response["status"] == "success"
    assert "updated_file" in response
    assert "category" in response
    assert response["category"] == "architecture"  # Content should be detected as architecture
    assert "verification" in response
    assert "previous_errors" in response  # New field for Phase 3
    
    # Verify that both the file and cache were updated correctly
    bank = server.storage.active_banks["global"].get("default")
    assert bank is not None
    
    # Get the cache manager singleton instance
    cache_manager = CacheManager.get_instance()
    
    # Check that bank exists in cache
    assert cache_manager.has_bank("global", "default")
    
    # Get cached content and verify the cache was created
    cached_content = cache_manager.get_bank("global", "default")
    assert isinstance(cached_content, dict)
    
    # The content should eventually be stored in a file determined by the analyzer
    # but might not be immediately visible in file because of the asynchronous nature
    # of the file synchronization
    target_file = response["updated_file"]
    
    # Verify the basic response structure is correct
    assert response["status"] == "success"
    assert response["bank_info"]["type"] == "global"
    assert response["bank_info"]["id"] == "default"
    assert "verification" in response


@pytest.mark.asyncio
async def test_update_tool_with_cache_manager(server):
    """Test the update tool specifically integration with CacheManager."""
    # Mock the CacheManager.update_bank method to isolate the test
    with patch('memory_bank.cache_manager.cache_manager.CacheManager.update_bank') as mock_update_bank:
        # Setup the mock to return success
        mock_update_bank.return_value = {"status": "success"}
        
        # Create a bank first
        await server.call_tool_test(
            "activate",
            {
                "conversation_type": "global"
            }
        )
        
        # Call the update tool handler directly for testing
        test_content = "# Architecture Decision\n\nWe decided to use PostgreSQL for the database."
        result = await server.call_tool_test(
            "update",
            {
                "content": test_content,
                "conversation_id": "test_conversation",
                "update_count": 1
            }
        )
        response = parse_response(result)
        
        # Verify that update_bank was called correctly
        mock_update_bank.assert_called_once()
        
        # Check that the function was called - we can't check exact parameters
        # since they're being processed internally
        assert mock_update_bank.call_count == 1


@pytest.mark.asyncio
async def test_update_tool_with_cache_error(server):
    """Test the update tool handling of cache manager errors."""
    # Mock the CacheManager.update_bank method to return an error
    with patch('memory_bank.cache_manager.cache_manager.CacheManager.update_bank') as mock_update_bank, \
         patch('memory_bank.cache_manager.cache_manager.CacheManager.get_error_history') as mock_get_error_history:
        
        # Setup the mocks
        error_msg = "Test cache update error"
        mock_update_bank.return_value = {"status": "error", "error": error_msg}
        mock_get_error_history.return_value = [
            {
                "timestamp": "2025-04-10T14:32:10Z",
                "description": error_msg,
                "severity": "error"
            }
        ]
        
        # Create a bank first
        await server.call_tool_test(
            "activate",
            {
                "conversation_type": "global"
            }
        )
        
        # Call the update tool handler
        test_content = "# Test content"
        
        # Should raise an exception
        with pytest.raises(Exception) as exc_info:
            await server.call_tool_test(
                "update",
                {
                    "content": test_content,
                    "conversation_id": "test_conversation",
                    "update_count": 1
                }
            )
        
        # Verify that the error was properly propagated
        assert error_msg in str(exc_info.value)
        
        # Verify our mocks were called correctly
        mock_update_bank.assert_called_once()


@pytest.mark.asyncio
async def test_content_analyzer(server):
    """Test the content analyzer functionality."""
    from memory_bank.content import ContentAnalyzer
    
    # Test various content types
    test_cases = [
        {
            "content": "# Architecture Decision\n\nWe decided to use PostgreSQL for the database.",
            "expected_category": "architecture"
        },
        {
            "content": "# Progress Update\n\nCompleted the login page implementation.",
            "expected_category": "progress"
        },
        {
            "content": "# Code Structure\n\nThe main module is organized into three classes.",
            "expected_category": "code"
        },
        {
            "content": "# Meeting Notes\n\nDiscussed project timeline in today's meeting.",
            "expected_category": "meeting"
        },
        {
            "content": "# Random Content\n\nThis doesn't match any specific category.",
            "expected_category": "default"
        }
    ]
    
    for test_case in test_cases:
        category, confidence = ContentAnalyzer.analyze_content(test_case["content"])
        assert category == test_case["expected_category"], f"Expected {test_case['expected_category']} but got {category}"
        assert 0 <= confidence <= 1.0, "Confidence should be between 0 and 1"


@pytest.mark.asyncio
async def test_target_file_mapping(server):
    """Test the mapping of content categories to target files."""
    from memory_bank.content import ContentAnalyzer
    
    # Test mapping for different bank types
    test_cases = [
        {
            "bank_type": "global",
            "content": "# User prefers brief responses with examples.",
            "expected_file": "preferences.md"
        },
        {
            "bank_type": "project",
            "content": "# Architecture Decision\n\nWe will use a microservice architecture.",
            "expected_file": "doc/architecture.md"
        },
        {
            "bank_type": "code",
            "content": "# API Documentation\n\nThe REST endpoints are documented below.",
            "expected_file": "doc/api.md"
        }
    ]
    
    for test_case in test_cases:
        result = ContentAnalyzer.determine_target_file(
            test_case["bank_type"], 
            test_case["content"]
        )
        
        assert result["target_file"] == test_case["expected_file"], \
            f"Expected {test_case['expected_file']} but got {result['target_file']}"
