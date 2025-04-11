"""
Tests for the cache validator.
"""

import pytest
import json
import tempfile
from pathlib import Path
import shutil
from datetime import datetime

from memory_bank.cache.validator import (
    validate_cache, check_version_compatibility, repair_cache,
    CURRENT_VERSION, REQUIRED_FIELDS, VALID_OPTIMIZATION_TYPES,
    REQUIRED_CONSOLIDATED_SECTIONS
)


@pytest.fixture
def temp_cache_file():
    """Create a temporary cache file for testing."""
    temp_dir = tempfile.mkdtemp()
    cache_path = Path(temp_dir) / "cache.json"
    yield cache_path
    shutil.rmtree(temp_dir)


@pytest.fixture
def valid_cache_data():
    """Create valid cache data for testing."""
    return {
        "version": CURRENT_VERSION,
        "timestamp": datetime.now().isoformat(),
        "optimization_type": "simple",
        "files": ["file1.md", "file2.md"],
        "summaries": {
            "file1.md": "Summary of file 1",
            "file2.md": "Summary of file 2"
        },
        "concepts": {
            "concept1": ["related1", "related2"],
            "concept2": ["related3"]
        },
        "consolidated": {
            "architecture_decisions": "Architecture decisions consolidated view",
            "technology_choices": "Technology choices consolidated view",
            "current_status": "Current status consolidated view",
            "next_steps": "Next steps consolidated view"
        },
        "relevance_scores": {
            "file1.md": 0.8,
            "file2.md": 0.6
        }
    }


@pytest.fixture
def valid_llm_cache_data(valid_cache_data):
    """Create valid LLM cache data for testing."""
    data = valid_cache_data.copy()
    data["optimization_type"] = "llm"
    data["relationships"] = {
        "concept1": ["concept2"],
        "related1": ["related2"]
    }
    return data


class TestCacheValidator:
    """Tests for the cache validator module."""
    
    def test_validate_valid_simple_cache(self, temp_cache_file, valid_cache_data):
        """Test validation of a valid simple cache file."""
        # Write valid cache data to file
        with open(temp_cache_file, 'w') as f:
            json.dump(valid_cache_data, f)
        
        # Validate cache
        is_valid, errors = validate_cache(temp_cache_file)
        
        # Check result
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_valid_llm_cache(self, temp_cache_file, valid_llm_cache_data):
        """Test validation of a valid LLM cache file."""
        # Write valid LLM cache data to file
        with open(temp_cache_file, 'w') as f:
            json.dump(valid_llm_cache_data, f)
        
        # Validate cache
        is_valid, errors = validate_cache(temp_cache_file)
        
        # Check result
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_missing_required_fields(self, temp_cache_file, valid_cache_data):
        """Test validation of a cache file with missing required fields."""
        # Create a copy of valid data and remove a required field
        invalid_data = valid_cache_data.copy()
        del invalid_data["concepts"]
        
        # Write invalid cache data to file
        with open(temp_cache_file, 'w') as f:
            json.dump(invalid_data, f)
        
        # Validate cache
        is_valid, errors = validate_cache(temp_cache_file)
        
        # Check result
        assert is_valid is False
        assert len(errors) == 1
        assert "Missing required field: concepts" in errors
    
    def test_validate_missing_llm_required_fields(self, temp_cache_file, valid_cache_data):
        """Test validation of an LLM cache file missing required fields."""
        # Create LLM data without relationships
        invalid_data = valid_cache_data.copy()
        invalid_data["optimization_type"] = "llm"
        # Relationships is missing
        
        # Write invalid cache data to file
        with open(temp_cache_file, 'w') as f:
            json.dump(invalid_data, f)
        
        # Validate cache
        is_valid, errors = validate_cache(temp_cache_file)
        
        # Check result
        assert is_valid is False
        assert len(errors) == 1
        assert "Missing required field for LLM optimization: relationships" in errors
    
    def test_validate_invalid_optimization_type(self, temp_cache_file, valid_cache_data):
        """Test validation of a cache file with invalid optimization type."""
        # Create a copy of valid data with invalid optimization type
        invalid_data = valid_cache_data.copy()
        invalid_data["optimization_type"] = "invalid_type"
        
        # Write invalid cache data to file
        with open(temp_cache_file, 'w') as f:
            json.dump(invalid_data, f)
        
        # Validate cache
        is_valid, errors = validate_cache(temp_cache_file)
        
        # Check result
        assert is_valid is False
        assert len(errors) == 1
        assert "Invalid optimization_type: invalid_type" in errors
    
    def test_validate_wrong_field_types(self, temp_cache_file, valid_cache_data):
        """Test validation of a cache file with wrong field types."""
        # Create a copy of valid data with wrong types
        invalid_data = valid_cache_data.copy()
        invalid_data["files"] = {"file1.md": "This should be a list, not a dict"}
        
        # Write invalid cache data to file
        with open(temp_cache_file, 'w') as f:
            json.dump(invalid_data, f)
        
        # Validate cache
        is_valid, errors = validate_cache(temp_cache_file)
        
        # Check result
        assert is_valid is False
        assert len(errors) > 0
        assert any("Field files has wrong type" in error for error in errors)
    
    def test_validate_inconsistent_files(self, temp_cache_file, valid_cache_data):
        """Test validation of a cache file with inconsistent files lists."""
        # Create a copy of valid data with inconsistent files
        invalid_data = valid_cache_data.copy()
        invalid_data["files"] = ["file1.md", "file2.md", "file3.md"]  # Extra file
        
        # Write invalid cache data to file
        with open(temp_cache_file, 'w') as f:
            json.dump(invalid_data, f)
        
        # Validate cache
        is_valid, errors = validate_cache(temp_cache_file)
        
        # Check result
        assert is_valid is False
        assert len(errors) > 0
        assert "Files list does not match summary keys" in errors
    
    def test_validate_missing_consolidated_sections(self, temp_cache_file, valid_cache_data):
        """Test validation of a cache file with missing consolidated sections."""
        # Create a copy of valid data with missing consolidated section
        invalid_data = valid_cache_data.copy()
        invalid_data["consolidated"] = {
            "architecture_decisions": "Architecture decisions",
            "technology_choices": "Technology choices",
            # Missing current_status and next_steps
        }
        
        # Write invalid cache data to file
        with open(temp_cache_file, 'w') as f:
            json.dump(invalid_data, f)
        
        # Validate cache
        is_valid, errors = validate_cache(temp_cache_file)
        
        # Check result
        assert is_valid is False
        assert len(errors) >= 2
        assert "Missing required section in consolidated view: current_status" in errors
        assert "Missing required section in consolidated view: next_steps" in errors
    
    def test_validate_invalid_relevance_scores(self, temp_cache_file, valid_cache_data):
        """Test validation of a cache file with invalid relevance scores."""
        # Create a copy of valid data with invalid scores
        invalid_data = valid_cache_data.copy()
        invalid_data["relevance_scores"]["file1.md"] = 1.5  # Out of range
        
        # Write invalid cache data to file
        with open(temp_cache_file, 'w') as f:
            json.dump(invalid_data, f)
        
        # Validate cache
        is_valid, errors = validate_cache(temp_cache_file)
        
        # Check result
        assert is_valid is False
        assert len(errors) == 1
        assert "Invalid relevance score for file1.md: 1.5" in errors
    
    def test_check_version_compatibility(self):
        """Test version compatibility checking."""
        # Same version should be compatible
        assert check_version_compatibility(CURRENT_VERSION) is True
        
        # Different patch version should be compatible
        current_parts = CURRENT_VERSION.split('.')
        patch_version = f"{current_parts[0]}.{current_parts[1]}.{int(current_parts[2]) + 1}"
        assert check_version_compatibility(patch_version) is True
        
        # Different minor version should be compatible
        minor_version = f"{current_parts[0]}.{int(current_parts[1]) + 1}.0"
        assert check_version_compatibility(minor_version) is True
        
        # Different major version should not be compatible
        major_version = f"{int(current_parts[0]) + 1}.0.0"
        assert check_version_compatibility(major_version) is False
        
        # Invalid version should not be compatible
        assert check_version_compatibility("invalid.version") is False
        assert check_version_compatibility("1.0") is False
        assert check_version_compatibility("v1.0.0") is False
    
    def test_repair_cache_missing_fields(self, temp_cache_file):
        """Test repairing a cache file with missing fields."""
        # Create minimal invalid cache
        invalid_data = {
            "version": CURRENT_VERSION,
            "timestamp": datetime.now().isoformat(),
            # Missing many required fields
        }
        
        # Write invalid cache data to file
        with open(temp_cache_file, 'w') as f:
            json.dump(invalid_data, f)
        
        # Repair cache
        success, actions = repair_cache(temp_cache_file)
        
        # Check result
        assert success is True
        assert len(actions) > 0
        
        # Validate the repaired cache
        is_valid, errors = validate_cache(temp_cache_file)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_repair_cache_invalid_optimization_type(self, temp_cache_file, valid_cache_data):
        """Test repairing a cache file with invalid optimization type."""
        # Create invalid cache with wrong optimization type
        invalid_data = valid_cache_data.copy()
        invalid_data["optimization_type"] = "invalid_type"
        
        # Write invalid cache data to file
        with open(temp_cache_file, 'w') as f:
            json.dump(invalid_data, f)
        
        # Repair cache
        success, actions = repair_cache(temp_cache_file)
        
        # Check result
        assert success is True
        assert len(actions) == 1
        assert "Fixed invalid optimization_type" in actions
        
        # Validate the repaired cache
        is_valid, errors = validate_cache(temp_cache_file)
        assert is_valid is True
        assert len(errors) == 0
        
        # Check the repaired data
        with open(temp_cache_file, 'r') as f:
            repaired_data = json.load(f)
        assert repaired_data["optimization_type"] == "simple"
    
    def test_repair_cache_missing_llm_fields(self, temp_cache_file, valid_cache_data):
        """Test repairing an LLM cache file with missing fields."""
        # Create invalid LLM cache without relationships
        invalid_data = valid_cache_data.copy()
        invalid_data["optimization_type"] = "llm"
        # Missing relationships
        
        # Write invalid cache data to file
        with open(temp_cache_file, 'w') as f:
            json.dump(invalid_data, f)
        
        # Repair cache
        success, actions = repair_cache(temp_cache_file)
        
        # Check result
        assert success is True
        assert len(actions) == 1
        assert "Added missing relationships field for LLM optimization" in actions
        
        # Validate the repaired cache
        is_valid, errors = validate_cache(temp_cache_file)
        assert is_valid is True
        assert len(errors) == 0
        
        # Check the repaired data
        with open(temp_cache_file, 'r') as f:
            repaired_data = json.load(f)
        assert "relationships" in repaired_data
