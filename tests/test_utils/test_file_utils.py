"""
Tests for file utility functions.
"""

import pytest
import tempfile
import os
import json
import yaml
from pathlib import Path

from memory_bank.utils.file import (
    ensure_directory,
    read_file,
    write_file,
    read_yaml,
    write_yaml,
    read_json,
    write_json,
    extract_frontmatter,
    add_frontmatter
)


@pytest.fixture
def temp_file():
    """Create a temporary file."""
    fd, path = tempfile.mkstemp()
    yield Path(path)
    os.close(fd)
    os.unlink(path)


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    import shutil
    shutil.rmtree(temp_dir)


def test_ensure_directory(temp_dir):
    """Test directory creation."""
    # Test creating a new directory
    new_dir = temp_dir / "test_dir"
    result = ensure_directory(new_dir)
    assert result is True
    assert new_dir.exists()
    assert new_dir.is_dir()
    
    # Test with existing directory
    result = ensure_directory(new_dir)
    assert result is True
    
    # Test with nested directories
    nested_dir = temp_dir / "nested" / "dirs" / "test"
    result = ensure_directory(nested_dir)
    assert result is True
    assert nested_dir.exists()
    assert nested_dir.is_dir()
    
    # Test with string path
    string_dir = str(temp_dir / "string_path")
    result = ensure_directory(string_dir)
    assert result is True
    assert Path(string_dir).exists()
    assert Path(string_dir).is_dir()


def test_read_write_file(temp_dir):
    """Test basic file reading and writing."""
    # Test writing to a new file
    test_file = temp_dir / "test.txt"
    test_content = "This is test content."
    
    result = write_file(test_file, test_content)
    assert result is True
    assert test_file.exists()
    
    # Test reading the file
    content = read_file(test_file)
    assert content == test_content
    
    # Test writing to a file in a non-existent directory
    nested_file = temp_dir / "nested" / "test.txt"
    result = write_file(nested_file, test_content)
    assert result is True
    assert nested_file.exists()
    
    # Test reading a non-existent file with default content
    nonexistent = temp_dir / "nonexistent.txt"
    default = "Default content"
    content = read_file(nonexistent, default)
    assert content == default
    
    # Test with string paths
    string_file = str(temp_dir / "string_file.txt")
    result = write_file(string_file, test_content)
    assert result is True
    
    content = read_file(string_file)
    assert content == test_content


def test_read_write_yaml(temp_dir):
    """Test YAML file reading and writing."""
    # Test data
    test_data = {
        "string": "value",
        "number": 42,
        "list": [1, 2, 3],
        "nested": {
            "key": "value"
        }
    }
    
    # Test writing YAML
    yaml_file = temp_dir / "test.yaml"
    result = write_yaml(yaml_file, test_data)
    assert result is True
    assert yaml_file.exists()
    
    # Test reading YAML
    data = read_yaml(yaml_file)
    assert data == test_data
    
    # Test reading non-existent YAML file
    nonexistent = temp_dir / "nonexistent.yaml"
    data = read_yaml(nonexistent)
    assert data is None
    
    # Test reading malformed YAML
    bad_yaml = temp_dir / "bad.yaml"
    bad_yaml.write_text("key: : value")  # Invalid YAML
    data = read_yaml(bad_yaml)
    assert data is None


def test_read_write_json(temp_dir):
    """Test JSON file reading and writing."""
    # Test data
    test_data = {
        "string": "value",
        "number": 42,
        "list": [1, 2, 3],
        "nested": {
            "key": "value"
        }
    }
    
    # Test writing JSON
    json_file = temp_dir / "test.json"
    result = write_json(json_file, test_data)
    assert result is True
    assert json_file.exists()
    
    # Test reading JSON
    data = read_json(json_file)
    assert data == test_data
    
    # Test reading non-existent JSON file
    nonexistent = temp_dir / "nonexistent.json"
    data = read_json(nonexistent)
    assert data is None
    
    # Test reading malformed JSON
    bad_json = temp_dir / "bad.json"
    bad_json.write_text("{key: value}")  # Invalid JSON
    data = read_json(bad_json)
    assert data is None
    
    # Test writing with different indent
    indent_file = temp_dir / "indent.json"
    result = write_json(indent_file, test_data, indent=4)
    assert result is True
    
    # Verify indentation by reading raw file
    content = read_file(indent_file)
    lines = content.splitlines()
    # Check indentation of nested property
    nested_line = next(line for line in lines if "nested" in line)
    assert nested_line.startswith("    ")


def test_frontmatter(temp_dir):
    """Test frontmatter extraction and addition."""
    # Test frontmatter data
    frontmatter_data = {
        "title": "Test Document",
        "date": "2025-04-09",
        "tags": ["test", "document"],
        "version": 1.0
    }
    
    # Test content
    content = "# Test Document\n\nThis is a test document."
    
    # Test adding frontmatter
    with_frontmatter = add_frontmatter(content, frontmatter_data)
    
    # Ensure frontmatter was added properly
    assert with_frontmatter.startswith("---")
    
    # Test extracting frontmatter
    extracted, remaining = extract_frontmatter(with_frontmatter)
    
    # Verify extracted frontmatter
    assert extracted == frontmatter_data
    assert remaining == content
    
    # Test extracting from content without frontmatter
    extracted, remaining = extract_frontmatter(content)
    assert extracted is None
    assert remaining == content
    
    # Test with invalid frontmatter
    invalid_frontmatter = "---\ntitle: Test: Document\n---\n\n" + content
    extracted, remaining = extract_frontmatter(invalid_frontmatter)
    assert extracted is None
    assert remaining == invalid_frontmatter
    
    # Test adding frontmatter to content that already has frontmatter
    existing_frontmatter = "---\ntitle: Existing Document\n---\n\n" + content
    updated = add_frontmatter(existing_frontmatter, frontmatter_data)
    
    # Extract and verify
    extracted, remaining = extract_frontmatter(updated)
    assert extracted == frontmatter_data
    assert remaining == content
