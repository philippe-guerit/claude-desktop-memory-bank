"""
Tests for the update tool.
"""

import pytest
import asyncio
import json

from tests.conftest import parse_response


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
    
    # Verify that the file was updated correctly
    bank = server.storage.active_banks["global"].get("default")
    assert bank is not None
    
    # The content should be stored in a file determined by the analyzer
    target_file = response["updated_file"]
    loaded_content = bank.load_file(target_file)
    assert test_content in loaded_content


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
