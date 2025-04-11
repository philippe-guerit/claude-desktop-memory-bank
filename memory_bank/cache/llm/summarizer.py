"""
File summarization utilities for LLM cache optimization.

This module provides functions for generating intelligent summaries of memory bank files.
"""

from typing import Dict, Any, List
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def generate_summaries(optimizer, content: Dict[str, str]) -> Dict[str, str]:
    """Generate intelligent summaries for each file using LLM.
    
    Args:
        optimizer: LLMCacheOptimizer instance
        content: Dict mapping file paths to their content
        
    Returns:
        Dict mapping file paths to their summaries
    """
    summaries = {}
    tasks = []
    
    for file_path, file_content in content.items():
        if len(file_content) < 200:  # Don't summarize very small files
            summaries[file_path] = file_content
            continue
            
        task = summarize_file(optimizer, file_path, file_content)
        tasks.append(task)
        
    # Process in batches to avoid overwhelming the API
    batch_size = 3
    for i in range(0, len(tasks), batch_size):
        batch_results = await asyncio.gather(*tasks[i:i+batch_size], return_exceptions=True)
        
        for j, result in enumerate(batch_results):
            file_idx = i + j
            if file_idx >= len(tasks):
                break
                
            file_path = list(content.keys())[file_idx]
            if isinstance(result, Exception):
                logger.error(f"Error summarizing {file_path}: {result}")
                # Fall back to simple summary
                from .utils import extract_first_paragraph
                summaries[file_path] = extract_first_paragraph(content[file_path])
            else:
                summaries[file_path] = result
    
    # Handle any files that didn't get processed
    for file_path in content:
        if file_path not in summaries:
            from .utils import extract_first_paragraph
            summaries[file_path] = extract_first_paragraph(content[file_path])
            
    return summaries
    
    
async def summarize_file(optimizer, file_path: str, content: str) -> str:
    """Summarize a single file using LLM.
    
    Args:
        optimizer: LLMCacheOptimizer instance
        file_path: Path to the file
        content: Content of the file
        
    Returns:
        Summary of the file
    """
    # Truncate very large files
    max_content_length = 12000
    if len(content) > max_content_length:
        content = content[:max_content_length] + "...[content truncated]"
        
    file_type = Path(file_path).stem
    prompt = f"""Summarize the following {file_type} document in a concise paragraph.
Focus on the key information that would be relevant for context in future conversations.
Maintain any critical technical details, architectural decisions, or design patterns.

DOCUMENT ({file_path}):
{content}

SUMMARY:"""

    response = await optimizer.call_llm(prompt)
    return response.strip()
