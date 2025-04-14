"""
Prompt generation for LLM-based content processing.

This module provides functions for generating prompts used
in the LLM-based content processor.
"""

import json
from typing import Dict, Any, List


def generate_content_analysis_prompt(content: str, existing_cache: Dict[str, str],
                                bank_type: str, file_mapping: Dict) -> str:
    """Generate prompt for content analysis.
    
    Args:
        content: Content to analyze
        existing_cache: Existing memory bank content
        bank_type: Type of bank (global, project, code)
        file_mapping: Mapping of categories to target files
        
    Returns:
        Prompt string for LLM
    """
    # Get available target files based on bank type
    available_files = json.dumps(file_mapping.get(bank_type, {}), indent=2)
    
    # Get list of existing files
    existing_files = list(existing_cache.keys())
    
    prompt = f"""You are an AI assistant helping to organize content for a memory bank system.
Your task is to analyze new content and determine where it should be stored.

### Bank Type
The memory bank type is: {bank_type}

### Available Target Files
The following files are available for this bank type:
{available_files}

### Existing Files
The memory bank currently contains these files:
{', '.join(existing_files) if existing_files else 'No existing files'}

### New Content
{content}

### Instructions
Please analyze the content and provide a JSON object with the following fields:
1. "target_file" - The most appropriate file to store this content
2. "operation" - How to add the content (append, replace, or insert)
3. "position" - For insert operations, specify the position (e.g., section name)
4. "content" - The content, possibly reformatted for clarity
5. "category" - The content category (architecture, design, progress, etc.)

Only respond with a properly formatted JSON object containing these fields. Nothing else.
"""
    return prompt


def generate_concept_extraction_prompt(content: str) -> str:
    """Generate prompt for concept extraction.
    
    Args:
        content: Content to analyze
        
    Returns:
        Prompt string for LLM
    """
    prompt = f"""You are an AI assistant helping organize content for a memory bank system.
Your task is to extract key concepts from the provided content.

### Content
{content}

### Instructions
Please extract key concepts from the content and organize them into these categories:
- architecture_decisions: Major architectural decisions
- technology_choices: Technology selections and their purposes
- implementation_patterns: Design patterns or implementation approaches
- project_constraints: Constraints or requirements
- milestones: Completed items or next steps

Format your response as a JSON object with categories as keys and arrays of concepts as values.
Only include categories where you found relevant concepts.

Only respond with a properly formatted JSON object. Nothing else.
"""
    return prompt


def generate_relationship_prompt(content: str, existing_cache: Dict[str, str]) -> str:
    """Generate prompt for relationship determination.
    
    Args:
        content: New content to analyze
        existing_cache: Existing memory bank content
        
    Returns:
        Prompt string for LLM
    """
    # Limit the context size to prevent overwhelming the LLM
    file_summaries = {}
    for file_path, file_content in existing_cache.items():
        # Get first 200 characters of each file as a summary
        summary = file_content[:200] + "..." if len(file_content) > 200 else file_content
        file_summaries[file_path] = summary
        
    file_context = json.dumps(file_summaries, indent=2)
    
    prompt = f"""You are an AI assistant helping organize content for a memory bank system.
Your task is to identify relationships between new content and existing files.

### Existing Files (Summaries)
{file_context}

### New Content
{content}

### Instructions
Please identify relationships between the new content and existing files, categorized as:
- related_files: Files that are topically related to the new content
- similar_content: Files with highly similar content (potential duplication)
- referenced_files: Files explicitly referenced in the new content

Format your response as a JSON object with categories as keys and arrays of file paths as values.
Only include file paths that actually exist in the provided context.

Only respond with a properly formatted JSON object. Nothing else.
"""
    return prompt


def generate_optimization_prompt(content: Dict[str, str], min_tokens: int, max_tokens: int) -> str:
    """Generate prompt for content optimization.
    
    Args:
        content: Dict of file content to optimize
        min_tokens: Minimum target size in tokens
        max_tokens: Maximum target size in tokens
        
    Returns:
        Prompt string for LLM
    """
    # Convert token counts to approximate character counts for clarity
    min_chars = min_tokens * 4
    max_chars = max_tokens * 4
    
    # Prepare content summary for each file with size info
    file_info = []
    total_chars = 0
    
    for file_path, file_content in content.items():
        chars = len(file_content)
        total_chars += chars
        summary = file_content[:200] + "..." if len(file_content) > 200 else file_content
        file_info.append(f"{file_path} ({chars} chars): {summary}")
    
    files_summary = "\n".join(file_info)
    
    prompt = f"""You are an AI assistant helping to optimize a memory bank system.
Your task is to reduce the size of the content while preserving the most important information.

### Current Content Size
Total size: ~{total_chars} characters (approximately {total_chars//4} tokens)
Target size: Between {min_chars} and {max_chars} characters (approximately {min_tokens}-{max_tokens} tokens)

### Content Files
{files_summary}

### Optimization Guidelines
Please optimize the content following these priorities:
1. Preserve critical architecture decisions and design patterns
2. Maintain current project scope definition and ongoing work
3. Keep technical decision history with explicit rationales
4. Retain information about current implementation patterns
5. Preserve critical dependencies and system constraints
6. Keep recent development activities and progress markers
7. Prune or summarize historical discussions and outdated information
8. Combine redundant information

### Instructions
For each file, provide optimized content that preserves the most valuable information
while reducing the overall size to fit within the target range.

Format your response as a JSON object where keys are file paths and values are the optimized content.
Only respond with a properly formatted JSON object. Nothing else.
"""
    return prompt
