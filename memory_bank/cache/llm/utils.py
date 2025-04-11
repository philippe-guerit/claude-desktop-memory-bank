"""
Utility functions for LLM cache optimization.

This module provides common utility functions used by other modules in the LLM cache system.
"""

import re
from typing import Dict, Any, List


def extract_first_paragraph(content: str) -> str:
    """Extract the first paragraph or heading + first paragraph from content.
    
    Args:
        content: Markdown content
        
    Returns:
        First paragraph or heading + first paragraph
    """
    # Look for first heading
    heading_match = re.search(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)
    
    # Look for first paragraph
    paragraph_matches = re.findall(r'(?:^|\n\n)([^\n#].+?)(?:\n\n|$)', content, re.DOTALL)
    first_paragraph = paragraph_matches[0].strip() if paragraph_matches else ""
    
    if heading_match and first_paragraph:
        return f"{heading_match.group(0)}\n\n{first_paragraph}"
    elif heading_match:
        return heading_match.group(0)
    elif first_paragraph:
        return first_paragraph
    else:
        return content[:100] + "..." if len(content) > 100 else content


def merge_dictionaries(dict1: Dict, dict2: Dict) -> Dict:
    """Merge two dictionaries, with dict2 values taking precedence.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (values override dict1)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dictionaries(result[key], value)
        else:
            result[key] = value
    return result


def extract_yaml_frontmatter(content: str) -> Dict:
    """Extract YAML frontmatter from markdown content.
    
    Args:
        content: Markdown content with optional YAML frontmatter
        
    Returns:
        Dictionary of YAML frontmatter values, or empty dict if none found
    """
    import yaml
    
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if frontmatter_match:
        try:
            return yaml.safe_load(frontmatter_match.group(1))
        except yaml.YAMLError:
            return {}
    return {}


def find_headings(content: str) -> Dict[str, int]:
    """Find all headings in markdown content with their positions.
    
    Args:
        content: Markdown content
        
    Returns:
        Dict mapping heading text to position in content
    """
    headings = {}
    for match in re.finditer(r'^(#{1,6})\s+(.+?)$', content, re.MULTILINE):
        level = len(match.group(1))
        text = match.group(2).strip()
        headings[text] = match.start()
    return headings


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity between two strings.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0.0-1.0)
    """
    # Convert to lowercase and split into words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    return intersection / union
