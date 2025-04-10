"""
File utility functions.

This module provides file-related utility functions.
"""

from pathlib import Path
from typing import Optional, Union
import logging
import os
import json
import yaml

logger = logging.getLogger(__name__)


def ensure_directory(path: Union[str, Path]) -> bool:
    """Ensure a directory exists.
    
    Args:
        path: Path to the directory
        
    Returns:
        True if the directory exists or was created, False otherwise
    """
    try:
        # Convert to Path if needed
        if isinstance(path, str):
            path = Path(path)
        
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        return True
        
    except Exception as e:
        logger.error(f"Error ensuring directory {path}: {e}")
        return False


def read_file(path: Union[str, Path], default_content: Optional[str] = None) -> Optional[str]:
    """Read the contents of a file.
    
    Args:
        path: Path to the file
        default_content: Default content to return if the file doesn't exist
        
    Returns:
        File contents if successful, default_content if the file doesn't exist, None on error
    """
    try:
        # Convert to Path if needed
        if isinstance(path, str):
            path = Path(path)
        
        # Check if the file exists
        if not path.exists():
            return default_content
        
        # Read the file
        return path.read_text()
        
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        return None


def write_file(path: Union[str, Path], content: str) -> bool:
    """Write content to a file.
    
    Args:
        path: Path to the file
        content: Content to write
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert to Path if needed
        if isinstance(path, str):
            path = Path(path)
        
        # Ensure parent directory exists
        if not ensure_directory(path.parent):
            return False
        
        # Write the file
        path.write_text(content)
        return True
        
    except Exception as e:
        logger.error(f"Error writing file {path}: {e}")
        return False


def read_yaml(path: Union[str, Path]) -> Optional[dict]:
    """Read YAML from a file.
    
    Args:
        path: Path to the file
        
    Returns:
        Dict with YAML content if successful, None otherwise
    """
    try:
        # Read the file
        content = read_file(path)
        if not content:
            return None
        
        # Parse YAML
        return yaml.safe_load(content)
        
    except Exception as e:
        logger.error(f"Error reading YAML from {path}: {e}")
        return None


def write_yaml(path: Union[str, Path], data: dict) -> bool:
    """Write data as YAML to a file.
    
    Args:
        path: Path to the file
        data: Data to write
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert to YAML
        content = yaml.dump(data, default_flow_style=False, sort_keys=False)
        
        # Write the file
        return write_file(path, content)
        
    except Exception as e:
        logger.error(f"Error writing YAML to {path}: {e}")
        return False


def read_json(path: Union[str, Path]) -> Optional[dict]:
    """Read JSON from a file.
    
    Args:
        path: Path to the file
        
    Returns:
        Dict with JSON content if successful, None otherwise
    """
    try:
        # Read the file
        content = read_file(path)
        if not content:
            return None
        
        # Parse JSON
        return json.loads(content)
        
    except Exception as e:
        logger.error(f"Error reading JSON from {path}: {e}")
        return None


def write_json(path: Union[str, Path], data: dict, indent: int = 2) -> bool:
    """Write data as JSON to a file.
    
    Args:
        path: Path to the file
        data: Data to write
        indent: Indentation level
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert to JSON
        content = json.dumps(data, indent=indent)
        
        # Write the file
        return write_file(path, content)
        
    except Exception as e:
        logger.error(f"Error writing JSON to {path}: {e}")
        return False


def extract_frontmatter(content: str) -> tuple[Optional[dict], str]:
    """Extract YAML frontmatter from a string.
    
    Args:
        content: String with potential frontmatter
        
    Returns:
        Tuple of (frontmatter dict or None, content without frontmatter)
    """
    try:
        # Check for frontmatter
        if not content.startswith('---'):
            return None, content
        
        # Find end of frontmatter
        end_index = content.find('---', 3)
        if end_index == -1:
            return None, content
        
        # Extract frontmatter
        frontmatter_str = content[3:end_index].strip()
        
        # Parse YAML
        frontmatter = yaml.safe_load(frontmatter_str)
        
        # Return frontmatter and content
        remaining_content = content[end_index + 3:].strip()
        return frontmatter, remaining_content
        
    except Exception as e:
        logger.error(f"Error extracting frontmatter: {e}")
        return None, content


def add_frontmatter(content: str, frontmatter: dict) -> str:
    """Add YAML frontmatter to a string.
    
    Args:
        content: String to add frontmatter to
        frontmatter: Dict with frontmatter data
        
    Returns:
        String with frontmatter added
    """
    try:
        # Remove existing frontmatter if present
        _, clean_content = extract_frontmatter(content)
        
        # Convert frontmatter to YAML
        frontmatter_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        
        # Add frontmatter
        return f"---\n{frontmatter_str}---\n\n{clean_content}"
        
    except Exception as e:
        logger.error(f"Error adding frontmatter: {e}")
        return content
