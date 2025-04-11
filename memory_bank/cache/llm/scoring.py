"""
Relevance scoring utilities for LLM cache optimization.

This module provides functions for calculating relevance scores for memory bank files.
"""

from typing import Dict, Any, List
import json
import re
import logging

logger = logging.getLogger(__name__)


async def calculate_relevance_scores(optimizer, content: Dict[str, str], 
                             concepts: Dict[str, List[str]]) -> Dict[str, float]:
    """Calculate relevance scores for files based on concept presence and LLM analysis.
    
    Args:
        optimizer: LLMCacheOptimizer instance
        content: Dict mapping file paths to their content
        concepts: Dict of extracted concepts
        
    Returns:
        Dict mapping file paths to relevance scores (0.0-1.0)
    """
    try:
        # Flatten concepts for easier matching
        all_concepts = []
        for concept_list in concepts.values():
            all_concepts.extend(concept_list)
            
        relevance_scores = {}
        
        # Create text for LLM to analyze
        files_text = ""
        for file_path, file_content in content.items():
            # Calculate basic score based on concept presence
            concept_matches = sum(1 for concept in all_concepts if concept.lower() in file_content.lower())
            basic_score = min(0.7, (concept_matches / max(len(all_concepts), 1)) * 0.7)
            
            # First few lines and length info for LLM
            preview = file_content[:500] + "..." if len(file_content) > 500 else file_content
            files_text += f"FILE: {file_path}\nLENGTH: {len(file_content)} chars\nPREVIEW: {preview}\n\n"
            
            # Store basic score as fallback
            relevance_scores[file_path] = basic_score
            
        prompt = f"""Analyze these file previews and assign a relevance score from 0.0 to 1.0 to each file.
Higher scores should be given to files that:
- Contain architectural decisions
- Describe key design patterns
- Document important technologies
- Outline project status or roadmap
- Have dense, valuable information vs sparse content

Files:
{files_text}

Return your answer as a JSON object where keys are file paths and values are scores:
{{
  "file_path1": 0.85,
  "file_path2": 0.32,
  ...
}}

JSON:"""

        response = await optimizer.call_llm(prompt)
        parsed_json = json.loads(response.strip())
        
        # Combine LLM scores with basic scores
        for file_path, llm_score in parsed_json.items():
            if file_path in relevance_scores:
                # Give more weight to LLM score but keep basic score component
                combined_score = 0.7 * llm_score + 0.3 * relevance_scores[file_path]
                relevance_scores[file_path] = round(combined_score, 2)
        
        return relevance_scores
        
    except Exception as e:
        logger.error(f"Error calculating relevance scores with LLM: {e}")
        # Fall back to simple relevance scores
        return calculate_simple_scores(content)


def calculate_simple_scores(content: Dict[str, str]) -> Dict[str, float]:
    """Calculate simple relevance scores based on file size and keywords.
    
    Args:
        content: Dict mapping file paths to their content
        
    Returns:
        Dict mapping file paths to relevance scores (0.0-1.0)
    """
    relevance_scores = {}
    
    # Important keywords that indicate relevance
    keywords = [
        "architecture", "design", "pattern", "framework", "component", 
        "technology", "library", "language", "tool", "implementation",
        "progress", "milestone", "completed", "status", "priority",
        "task", "todo", "plan", "next", "future"
    ]
    
    for file_path, file_content in content.items():
        # Check for keywords
        keyword_count = sum(1 for keyword in keywords if keyword in file_content.lower())
        keyword_score = min(0.8, keyword_count / (len(keywords) * 0.4))
        
        # Adjust based on content length (longer files might have more context)
        length_factor = min(0.2, len(file_content) / 10000)
        
        # Check for structured content (headings, lists)
        structure_score = 0.0
        if re.search(r'^#{1,3}\s+.+$', file_content, re.MULTILINE):
            structure_score += 0.1
        if re.search(r'^\s*-\s+.+$', file_content, re.MULTILINE):
            structure_score += 0.1
            
        # Combine factors
        relevance_scores[file_path] = min(1.0, keyword_score + length_factor + structure_score)
        
    return relevance_scores
