"""
Response parsing for LLM-based content processing.

This module provides functions for parsing and validating
responses from the LLM service.
"""

import re
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def parse_llm_response(response: str, bank_type: str, file_mapping: Dict) -> Dict[str, Any]:
    """Parse and validate the LLM response.
    
    Args:
        response: LLM response text
        bank_type: Type of bank (global, project, code)
        file_mapping: Mapping of categories to target files
        
    Returns:
        Parsed response as a dictionary
        
    Raises:
        ValueError: If response cannot be parsed or is invalid
    """
    try:
        # Extract JSON from response (handle cases where there might be extra text)
        json_match = re.search(r'(\{.*\})', response.strip(), re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in response")
            
        json_str = json_match.group(1)
        result = json.loads(json_str)
        
        # Ensure required fields are present
        required_fields = ["target_file", "operation", "content", "category"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
                
        # Ensure the target file is valid for this bank type
        valid_files = set()
        for file_list in file_mapping.get(bank_type, {}).values():
            valid_files.add(file_list)
            
        if result["target_file"] not in valid_files and not result["target_file"].startswith(("doc/", "notes/")):
            # Use default file as fallback
            result["target_file"] = file_mapping.get(bank_type, {}).get("default", "context.md")
            
        # Ensure operation is valid
        valid_operations = ["append", "replace", "insert"]
        if result["operation"] not in valid_operations:
            result["operation"] = "append"  # Default to append
            
        # If operation is insert, ensure position is specified
        if result["operation"] == "insert" and "position" not in result:
            result["operation"] = "append"  # Fall back to append
            
        return result
        
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing LLM response: {e}")
        raise ValueError(f"Failed to parse LLM response: {e}")


def parse_concept_response(response: str) -> Dict[str, List[str]]:
    """Parse the concept extraction response.
    
    Args:
        response: LLM response text
        
    Returns:
        Dict mapping concept categories to lists of concepts
        
    Raises:
        ValueError: If response cannot be parsed
    """
    try:
        # Extract JSON from response
        json_match = re.search(r'(\{.*\})', response.strip(), re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in response")
            
        json_str = json_match.group(1)
        concepts = json.loads(json_str)
        
        # Validate structure - each value should be a list of strings
        for category, items in list(concepts.items()):
            if not isinstance(items, list):
                logger.warning(f"Removing invalid concept category: {category}")
                concepts.pop(category)
                continue
                
            # Ensure all items are strings
            concepts[category] = [str(item) for item in items]
            
        return concepts
        
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing concept response: {e}")
        return {}  # Return empty dict on error


def parse_relationship_response(response: str) -> Dict[str, List[str]]:
    """Parse the relationship determination response.
    
    Args:
        response: LLM response text
        
    Returns:
        Dict mapping relationship types to lists of file paths
        
    Raises:
        ValueError: If response cannot be parsed
    """
    try:
        # Extract JSON from response
        json_match = re.search(r'(\{.*\})', response.strip(), re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in response")
            
        json_str = json_match.group(1)
        relationships = json.loads(json_str)
        
        # Validate structure - each value should be a list of strings
        for rel_type, files in list(relationships.items()):
            if not isinstance(files, list):
                logger.warning(f"Removing invalid relationship type: {rel_type}")
                relationships.pop(rel_type)
                continue
                
            # Ensure all items are strings
            relationships[rel_type] = [str(file) for file in files]
            
        return relationships
        
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing relationship response: {e}")
        return {
            "related_files": [],
            "similar_content": [],
            "referenced_files": []
        }  # Return empty structure on error


def parse_optimization_response(response: str, original_content: Dict[str, str]) -> Dict[str, str]:
    """Parse the content optimization response.
    
    Args:
        response: LLM response text
        original_content: Original content dict for fallback
        
    Returns:
        Dict mapping file paths to optimized content
        
    Raises:
        ValueError: If response cannot be parsed or is invalid
    """
    try:
        # Extract JSON from response
        json_match = re.search(r'(\{.*\})', response.strip(), re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in response")
            
        json_str = json_match.group(1)
        optimized = json.loads(json_str)
        
        # Validate structure - should be a dict of file paths to content
        if not isinstance(optimized, dict):
            raise ValueError("Response is not a dictionary of file paths to content")
            
        # Validate each file and content
        for file_path, content in list(optimized.items()):
            # Ensure content is a string
            if not isinstance(content, str):
                logger.warning(f"Removing invalid content for file {file_path}")
                optimized.pop(file_path)
                continue
                
            # Ensure file path exists in original content or has valid format
            if file_path not in original_content and not file_path.startswith(("doc/", "notes/")):
                logger.warning(f"Removing invalid file path: {file_path}")
                optimized.pop(file_path)
                
        # If optimization removed all files, return original content
        if not optimized:
            logger.warning("Optimization produced no valid content, returning original")
            return original_content
            
        # Add a marker to indicate content was optimized by LLM
        for file_path, content in optimized.items():
            if not content.startswith("# LLM-Optimized Content") and not content.startswith("#"):
                optimized[file_path] = f"# LLM-Optimized Content\n\n{content}"
            elif not content.startswith("# LLM-Optimized Content"):
                original_header = content.split('\n')[0]
                new_content = content.replace(original_header, f"# LLM-Optimized: {original_header[2:]}")
                optimized[file_path] = new_content
                
        return optimized
        
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing optimization response: {e}")
        # Return original content on error
        return original_content


def validate_results(result: Dict[str, Any], bank_type: str, file_mapping: Dict) -> bool:
    """Validate the parsed results for consistency and safety.
    
    Args:
        result: Parsed LLM response
        bank_type: Type of bank (global, project, code)
        file_mapping: Mapping of categories to target files
        
    Returns:
        True if results are valid, False otherwise
    """
    try:
        # Verify target_file exists in the mapping or has a valid path pattern
        valid_file = False
        
        # Check if target_file is in the file mapping for this bank type
        for category, file_path in file_mapping.get(bank_type, {}).items():
            if result["target_file"] == file_path:
                valid_file = True
                break
                
        # Also accept paths with standard subdirectories
        if not valid_file:
            valid_dirs = ["doc/", "notes/"]
            valid_file = any(result["target_file"].startswith(prefix) for prefix in valid_dirs)
            
        if not valid_file:
            logger.warning(f"Invalid target file: {result['target_file']}")
            return False
            
        # Verify operation is valid
        valid_operations = ["append", "replace", "insert"]
        if result["operation"] not in valid_operations:
            logger.warning(f"Invalid operation: {result['operation']}")
            return False
            
        # For insert operations, verify position is specified
        if result["operation"] == "insert" and "position" not in result:
            logger.warning("Missing position for insert operation")
            return False
            
        # Ensure content is not empty
        if not result.get("content"):
            logger.warning("Empty content in result")
            return False
            
        # Ensure category is specified
        if not result.get("category"):
            logger.warning("Missing category in result")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error validating results: {e}")
        return False
