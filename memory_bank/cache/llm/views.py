"""
Consolidated view generation utilities for LLM cache optimization.

This module provides functions for generating consolidated views across memory bank files.
"""

from typing import Dict, Any, List
import json
import re
import logging

logger = logging.getLogger(__name__)


async def generate_consolidated_view(optimizer, content: Dict[str, str], bank_type: str) -> Dict[str, str]:
    """Generate consolidated views across files using LLM.
    
    Args:
        optimizer: LLMCacheOptimizer instance
        content: Dict mapping file paths to their content
        bank_type: Type of memory bank (global, project, code)
        
    Returns:
        Dict containing consolidated views
    """
    # Combine all content with file markers for context
    combined_content = ""
    for file_path, file_content in content.items():
        # Include just the first part of each file to avoid too much content
        preview_content = file_content[:1500] + "..." if len(file_content) > 1500 else file_content
        combined_content += f"\n\n=== {file_path} ===\n{preview_content}"
        
    view_types = {
        "global": [
            "key_preferences", "recurring_themes", "important_references"
        ],
        "project": [
            "architecture_decisions", "technology_choices", "current_status", "next_steps"
        ],
        "code": [
            "architecture_overview", "design_patterns", "key_components", "technical_debt"
        ]
    }
    
    selected_views = view_types.get(bank_type, view_types["project"])
    
    prompt = f"""Based on these documents, generate concise consolidated views for a {bank_type} memory bank.
Each view should synthesize information across multiple files into a coherent summary.

DOCUMENTS:
{combined_content}

Return your answer in this JSON format:
{{
"""
    
    for view in selected_views:
        view_display = view.replace("_", " ").title()
        prompt += f'  "{view}": "A concise summary of {view_display}",\n'
        
    prompt += """}

JSON:"""

    try:
        response = await optimizer.call_llm(prompt)
        parsed_json = json.loads(response.strip())
        
        # Validate and return
        return parsed_json
        
    except Exception as e:
        logger.error(f"Error generating consolidated view with LLM: {e}")
        # Fall back to simple consolidated view
        return generate_simple_view(content)


def generate_simple_view(content: Dict[str, str]) -> Dict[str, str]:
    """Generate simple consolidated views without LLM.
    
    Args:
        content: Dict mapping file paths to their content
        
    Returns:
        Dict containing consolidated views
    """
    # Extract headings from all files
    all_headings = []
    for file_content in content.values():
        headings = re.findall(r'^#{1,3}\s+(.+)$', file_content, re.MULTILINE)
        all_headings.extend(headings)
        
    # Count heading frequencies
    heading_counts = {}
    for heading in all_headings:
        clean_heading = heading.lower().strip()
        heading_counts[clean_heading] = heading_counts.get(clean_heading, 0) + 1
        
    # Find most common topics
    top_headings = sorted(heading_counts.items(), key=lambda x: x[1], reverse=True)[:4]
    
    # Create simple consolidated views
    consolidated = {}
    
    if "architecture" in " ".join(h[0] for h in top_headings):
        consolidated["architecture_decisions"] = "Key architectural decisions from documentation."
        
    if "technology" in " ".join(h[0] for h in top_headings):
        consolidated["technology_choices"] = "Key technology choices from documentation."
    
    if "progress" in " ".join(h[0] for h in top_headings) or "status" in " ".join(h[0] for h in top_headings):
        consolidated["current_status"] = "Current project status from documentation."
        
    if "next" in " ".join(h[0] for h in top_headings) or "todo" in " ".join(h[0] for h in top_headings):
        consolidated["next_steps"] = "Next steps from documentation."
    
    # Always include these if not already present
    if "architecture_decisions" not in consolidated:
        consolidated["architecture_decisions"] = "Architecture decisions not explicitly found."
        
    if "technology_choices" not in consolidated:
        consolidated["technology_choices"] = "Technology choices not explicitly found."
        
    if "current_status" not in consolidated:
        consolidated["current_status"] = "Current status not explicitly found."
        
    if "next_steps" not in consolidated:
        consolidated["next_steps"] = "Next steps not explicitly found."
        
    return consolidated
