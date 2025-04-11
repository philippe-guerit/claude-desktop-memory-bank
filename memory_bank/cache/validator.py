"""
Cache validator for ensuring cache files meet expected schema and quality standards.

This module provides functions for validating cache files, including:
- Schema validation (required fields, types, etc.)
- Quality validation (non-empty content, proper formatting, etc.)
- Version compatibility checking
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Current cache schema version (Major.Minor.Patch)
CURRENT_VERSION = "2.0.0"

# Required fields for all cache files
REQUIRED_FIELDS = [
    "version",
    "timestamp",
    "optimization_type",
    "files",
    "summaries",
    "concepts",
    "consolidated",
    "relevance_scores"
]

# Additional fields required for LLM optimization
LLM_REQUIRED_FIELDS = [
    "relationships"
]

# Expected types for each field
FIELD_TYPES = {
    "version": str,
    "timestamp": str,
    "optimization_type": str,
    "optimization_status": str,
    "optimization_method": str,
    "llm_model": str,
    "files": list,
    "summaries": dict,
    "concepts": dict,
    "relationships": dict,
    "consolidated": dict,
    "relevance_scores": dict
}

# Make sure this definition is used in validation
def _check_field_type(field_name: str, value: Any) -> bool:
    """Check if a field has the correct type.
    
    Args:
        field_name: Name of the field
        value: Value to check
        
    Returns:
        True if type is correct, False otherwise
    """
    expected_type = FIELD_TYPES.get(field_name)
    if expected_type is None:
        return True  # No type constraint for this field
    
    return isinstance(value, expected_type)

# Valid optimization types
VALID_OPTIMIZATION_TYPES = ["simple", "llm", "fallback"]

# Valid optimization statuses
VALID_OPTIMIZATION_STATUSES = ["success", "error", "partial"]

# Required sections in consolidated view
REQUIRED_CONSOLIDATED_SECTIONS = [
    "architecture_decisions",
    "technology_choices",
    "current_status",
    "next_steps"
]


def validate_cache(cache_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate a cache file against the expected schema and quality standards.
    
    Args:
        cache_path: Path to the cache file
        
    Returns:
        A tuple containing:
        - Boolean indicating if the cache is valid
        - List of validation error messages (empty if valid)
    """
    errors = []
    
    # Check if file exists
    if not cache_path.exists():
        return False, ["Cache file does not exist"]
    
    # Try to parse the JSON
    try:
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in cache file: {e}"]
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in cache_data:
            errors.append(f"Missing required field: {field}")
    
    # If there are missing fields, return early
    if errors:
        return False, errors
    
    # Check optimization type
    optimization_type = cache_data["optimization_type"]
    if optimization_type not in VALID_OPTIMIZATION_TYPES:
        errors.append(f"Invalid optimization_type: {optimization_type}")
    
    # Check optimization status if present
    if "optimization_status" in cache_data:
        status = cache_data["optimization_status"]
        if status not in VALID_OPTIMIZATION_STATUSES:
            errors.append(f"Invalid optimization_status: {status}")
    
    # Check for LLM-specific fields if optimization_type is 'llm'
    if optimization_type == "llm":
        for field in LLM_REQUIRED_FIELDS:
            if field not in cache_data:
                errors.append(f"Missing required field for LLM optimization: {field}")
        
        # LLM optimizations should include model info
        if "llm_model" not in cache_data and cache_data.get("optimization_status") == "success":
            errors.append("Missing llm_model field for successful LLM optimization")
    
    # Check field types
    for field, expected_type in FIELD_TYPES.items():
        if field in cache_data and not isinstance(cache_data[field], expected_type):
            errors.append(f"Field {field} has wrong type: expected {expected_type.__name__}, "
                         f"got {type(cache_data[field]).__name__}")
    
    # Validate version format
    version = cache_data["version"]
    if not _is_valid_version(version):
        errors.append(f"Invalid version format: {version}")
    
    # Check for empty files list
    if not cache_data["files"] and (cache_data["summaries"] or cache_data["concepts"]):
        errors.append("Files list is empty but summaries or concepts exist")
    
    # Check for consistency between files and summaries
    if set(cache_data["files"]) != set(cache_data["summaries"].keys()):
        errors.append("Files list does not match summary keys")
    
    # Check for consistency between files and relevance scores
    if set(cache_data["files"]) != set(cache_data["relevance_scores"].keys()):
        errors.append("Files list does not match relevance score keys")
    
    # Check consolidated view sections
    for section in REQUIRED_CONSOLIDATED_SECTIONS:
        if section not in cache_data["consolidated"]:
            errors.append(f"Missing required section in consolidated view: {section}")
    
    # Check relevance scores are in range [0, 1]
    for file_path, score in cache_data["relevance_scores"].items():
        if not isinstance(score, (int, float)) or not (0 <= score <= 1):
            errors.append(f"Invalid relevance score for {file_path}: {score}")
    
    return len(errors) == 0, errors


def _is_valid_version(version: str) -> bool:
    """
    Check if a version string is valid (format: X.Y.Z with X, Y, Z being integers).
    
    Args:
        version: Version string to check
        
    Returns:
        True if the version is valid, False otherwise
    """
    if not isinstance(version, str):
        return False
    
    parts = version.split('.')
    if len(parts) != 3:
        return False
    
    return all(part.isdigit() for part in parts)


def check_version_compatibility(cache_version: str) -> bool:
    """
    Check if a cache version is compatible with the current version.
    
    Args:
        cache_version: Version string from cache
        
    Returns:
        True if compatible, False otherwise
    """
    if not _is_valid_version(cache_version) or not _is_valid_version(CURRENT_VERSION):
        return False
    
    # Parse versions
    cache_parts = [int(p) for p in cache_version.split('.')]
    current_parts = [int(p) for p in CURRENT_VERSION.split('.')]
    
    # Major version must match
    if cache_parts[0] != current_parts[0]:
        return False
    
    # If major version matches, it's compatible (until we need stricter rules)
    return True


def repair_cache(cache_path: Path) -> Tuple[bool, List[str]]:
    """
    Attempt to repair common issues with a cache file.
    
    Args:
        cache_path: Path to the cache file
        
    Returns:
        A tuple containing:
        - Boolean indicating if the repair was successful
        - List of repair actions taken
    """
    repair_actions = []
    
    # Check if file exists
    if not cache_path.exists():
        return False, ["Cache file does not exist"]
    
    # Try to parse the JSON
    try:
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
    except json.JSONDecodeError:
        return False, ["Cannot repair invalid JSON"]
    
    # Set missing required fields
    for field in REQUIRED_FIELDS:
        if field not in cache_data:
            if field == "version":
                cache_data[field] = CURRENT_VERSION
            elif field == "timestamp":
                from datetime import datetime
                cache_data[field] = datetime.now().isoformat()
            elif field == "optimization_type":
                cache_data[field] = "simple"
            elif field == "files":
                cache_data[field] = []
            elif field == "concepts":
                cache_data[field] = {}  # Concepts should be a dictionary, not a list
            elif field in ["summaries", "relevance_scores"]:
                cache_data[field] = {}
            elif field == "consolidated":
                cache_data[field] = {
                    section: "" for section in REQUIRED_CONSOLIDATED_SECTIONS
                }
            
            repair_actions.append(f"Added missing field: {field}")
    
    # Ensure optimization_type is valid
    if "optimization_type" in cache_data:
        if cache_data["optimization_type"] not in VALID_OPTIMIZATION_TYPES:
            cache_data["optimization_type"] = "simple"
            repair_actions.append(f"Fixed invalid optimization_type")
    
    # Ensure optimization_status is valid
    if "optimization_status" in cache_data:
        if cache_data["optimization_status"] not in VALID_OPTIMIZATION_STATUSES:
            cache_data["optimization_status"] = "success"
            repair_actions.append(f"Fixed invalid optimization_status")
    else:
        cache_data["optimization_status"] = "success"
        repair_actions.append(f"Added missing optimization_status")
    
    # Ensure optimization_method is present
    if "optimization_method" not in cache_data:
        if cache_data.get("optimization_type") == "llm":
            cache_data["optimization_method"] = "llm_enhanced"
        else:
            cache_data["optimization_method"] = "pattern_matching"
        repair_actions.append(f"Added missing optimization_method")
    
    # Ensure version is valid
    if "version" in cache_data:
        if not _is_valid_version(cache_data["version"]):
            cache_data["version"] = CURRENT_VERSION
            repair_actions.append(f"Fixed invalid version")
    
    # Ensure consolidated has required sections
    if "consolidated" in cache_data:
        for section in REQUIRED_CONSOLIDATED_SECTIONS:
            if section not in cache_data["consolidated"]:
                cache_data["consolidated"][section] = ""
                repair_actions.append(f"Added missing consolidated section: {section}")
    
    # Ensure relationships field exists for LLM optimization
    if cache_data.get("optimization_type") == "llm" and "relationships" not in cache_data:
        cache_data["relationships"] = {}
        repair_actions.append("Added missing relationships field for LLM optimization")
    
    # Make sure files and summaries are consistent
    if "files" in cache_data and "summaries" in cache_data:
        # Add empty summaries for any files without them
        for file_path in cache_data["files"]:
            if file_path not in cache_data["summaries"]:
                cache_data["summaries"][file_path] = ""
                repair_actions.append(f"Added missing summary for {file_path}")
        
        # Remove files that don't exist in files list
        summary_files = list(cache_data["summaries"].keys())
        for file_path in summary_files:
            if file_path not in cache_data["files"]:
                cache_data["files"].append(file_path)
                repair_actions.append(f"Added missing file entry for {file_path}")
    
    # Make sure files and relevance_scores are consistent
    if "files" in cache_data and "relevance_scores" in cache_data:
        # Add default scores for any files without them
        for file_path in cache_data["files"]:
            if file_path not in cache_data["relevance_scores"]:
                cache_data["relevance_scores"][file_path] = 0.5
                repair_actions.append(f"Added default relevance score for {file_path}")
        
        # Add missing files from relevance scores
        score_files = list(cache_data["relevance_scores"].keys())
        for file_path in score_files:
            if file_path not in cache_data["files"]:
                cache_data["files"].append(file_path)
                repair_actions.append(f"Added missing file entry for {file_path}")
    
    # Fix relevance scores out of range
    if "relevance_scores" in cache_data:
        for file_path, score in cache_data["relevance_scores"].items():
            if not isinstance(score, (int, float)) or not (0 <= score <= 1):
                cache_data["relevance_scores"][file_path] = 0.5
                repair_actions.append(f"Fixed invalid relevance score for {file_path}")
    
    # Write repaired cache back to file
    try:
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        # Verify the repair fixed all issues
        is_valid, errors = validate_cache(cache_path)
        if not is_valid:
            logger.warning(f"Repair did not fix all issues: {errors}")
            return False, repair_actions + [f"Failed to fix: {err}" for err in errors]
            
        return True, repair_actions
    except Exception as e:
        return False, [f"Error writing repaired cache: {e}"]
