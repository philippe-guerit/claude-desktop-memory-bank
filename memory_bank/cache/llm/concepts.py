"""
Concept extraction utilities for LLM cache optimization.

This module provides functions for extracting key concepts and relationships from memory bank files.
"""

from typing import Dict, Any, List, Tuple
import json
import re
import logging

logger = logging.getLogger(__name__)


async def extract_concepts(optimizer, content: Dict[str, str], 
                           bank_type: str) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Extract key concepts and their relationships using LLM.
    
    Args:
        optimizer: LLMCacheOptimizer instance
        content: Dict mapping file paths to their content
        bank_type: Type of memory bank (global, project, code)
        
    Returns:
        Tuple containing concepts dict and relationships dict
    """
    # Combine all content with file markers
    combined_content = ""
    for file_path, file_content in content.items():
        # Include just the first part of each file to avoid too much content
        preview_content = file_content[:2000] + "..." if len(file_content) > 2000 else file_content
        combined_content += f"\n\n=== {file_path} ===\n{preview_content}"
        
    bank_type_prompts = {
        "global": "Focus on preferences, patterns, and general concepts",
        "project": "Focus on project architecture, features, and milestones",
        "code": "Focus on code architecture, patterns, libraries, and implementation details"
    }
    
    focus_instruction = bank_type_prompts.get(bank_type, "")
    
    prompt = f"""Extract key concepts and their relationships from these documents.
{focus_instruction}

DOCUMENTS:
{combined_content}

Return your answer in this JSON format:
{{
  "concepts": {{
    "architecture": ["concept1", "concept2"],
    "technology": ["tech1", "tech2"],
    "progress": ["milestone1", "milestone2"],
    "tasks": ["task1", "task2"]
  }},
  "relationships": {{
    "concept1": ["related_concept_a", "related_concept_b"],
    "tech1": ["related_tech_a", "related_tech_b"]
  }}
}}

JSON:"""

    try:
        response = await optimizer.call_llm(prompt)
        parsed_json = json.loads(response.strip())
        
        # Ensure expected structure
        if "concepts" not in parsed_json or "relationships" not in parsed_json:
            raise ValueError("LLM response missing expected fields")
            
        return parsed_json["concepts"], parsed_json["relationships"]
        
    except Exception as e:
        logger.error(f"Error extracting concepts with LLM: {e}")
        # Fall back to pattern-based extraction
        return extract_concepts_patterns(content), {}


def extract_concepts_patterns(content: Dict[str, str]) -> Dict[str, List[str]]:
    """Extract key concepts using pattern matching.
    
    Args:
        content: Dict mapping file paths to their content
        
    Returns:
        Dict of concept categories and their identified instances
    """
    # Define patterns to look for
    patterns = {
        "architecture": [
            r"architecture(?:.*?)(?:is|will be|based on|using)(?:.*?)(\w+(?:\s+\w+){0,5})",
            r"(?:designed|implemented)(?:.*?)(?:using|with)(?:.*?)(\w+(?:\s+\w+){0,5})",
            r"design pattern(?:.*?)(\w+(?:\s+\w+){0,2})"
        ],
        "technology": [
            r"(?:using|with|based on)(?:.*?)(?:technology|framework|library|language)(?:.*?)(\w+(?:\s+\w+){0,2})",
            r"(?:will use|using|implements|based on)(?:.*?)(\w+(?:\.\w+)?)"
        ],
        "progress": [
            r"(?:completed|finished|done)(?:.*?)(\w+(?:\s+\w+){0,5})",
            r"(?:in progress|working on)(?:.*?)(\w+(?:\s+\w+){0,5})",
            r"(?:planned|next step|will)(?:.*?)(\w+(?:\s+\w+){0,5})"
        ],
        "tasks": [
            r"(?:TODO|FIXME|task)(?:.*?)(\w+(?:\s+\w+){0,5})",
            r"(?:\[ \]|\[x\])(?:.*?)(\w+(?:\s+\w+){0,5})"
        ]
    }
    
    # Extract concepts
    concepts = {category: [] for category in patterns}
    for file_content in content.values():
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, file_content, re.IGNORECASE)
                for match in matches:
                    # Clean up match
                    clean_match = match.strip().strip(".,:;()[]{}").strip()
                    if clean_match and len(clean_match) > 3 and clean_match not in concepts[category]:
                        concepts[category].append(clean_match)
    
    return concepts
