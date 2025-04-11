"""
LLM-powered cache optimization implementation.

This module provides the main LLMCacheOptimizer class for optimizing memory bank caches
using LLM-based summarization and content analysis.
"""

from typing import Dict, Any, List, Optional, Tuple
import json
import asyncio
import logging
from pathlib import Path
import httpx
from datetime import datetime
import os

from .summarizer import generate_summaries
from .concepts import extract_concepts, extract_concepts_patterns
from .views import generate_consolidated_view, generate_simple_view
from .scoring import calculate_relevance_scores, calculate_simple_scores

logger = logging.getLogger(__name__)

# Load .env file
from dotenv import load_dotenv
from pathlib import Path

# Try to load from memory_bank/.env
env_path = Path(__file__).parents[2] / '.env'
load_dotenv(dotenv_path=env_path)

# LLM API configuration (must be explicitly set)
LLM_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
LLM_API_URL = os.environ.get("LLM_API_URL", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "")


class LLMCacheOptimizer:
    """LLM-powered cache optimization system."""
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None, 
                 model: Optional[str] = None):
        """Initialize the cache optimizer.
        
        Args:
            api_key: API key for LLM service (default: from ANTHROPIC_API_KEY env var)
            api_url: URL for LLM API (default: Anthropic API)
            model: LLM model to use (default: claude-3-sonnet-20240229)
        """
        self.api_key = api_key or LLM_API_KEY
        self.api_url = api_url or LLM_API_URL
        self.model = model or LLM_MODEL
        self.http_client = httpx.AsyncClient(timeout=60.0)
        
        # Threshold for when to use LLM optimization vs. simple optimization
        self.full_optimization_threshold = 8192  # characters
        
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
        
    async def optimize_cache(self, bank_path: Path, content: Dict[str, str], 
                      bank_type: str, force_full: bool = False) -> bool:
        """Optimize the cache for a memory bank.
        
        This function creates an optimized cache.json file that contains:
        - Intelligent summaries of each file
        - Metadata about the memory bank
        - Connections between related concepts
        - Consolidated views across files
        
        Args:
            bank_path: Path to the memory bank root
            content: Dict mapping file paths to their content
            bank_type: Type of memory bank (global, project, code)
            force_full: Force full LLM-based optimization even for small content
            
        Returns:
            True if optimization was successful, False otherwise
        """
        try:
            cache_path = bank_path / "cache.json"
            
            # Determine content size to decide optimization approach
            total_content_size = sum(len(text) for text in content.values())
            
            if total_content_size > self.full_optimization_threshold or force_full:
                # Use advanced LLM-based optimization for larger content
                return await self._optimize_with_llm(bank_path, content, bank_type, cache_path)
            else:
                # Use simple optimization for smaller content
                return self._optimize_simple(bank_path, content, cache_path)
                
        except Exception as e:
            logger.error(f"Error optimizing cache for {bank_path}: {e}")
            return False
            
    def _optimize_simple(self, bank_path: Path, content: Dict[str, str], 
                         cache_path: Path) -> bool:
        """Perform simple optimization without using LLM.
        
        Args:
            bank_path: Path to the memory bank root
            content: Dict mapping file paths to their content
            cache_path: Path where cache file should be written
            
        Returns:
            True if optimization was successful, False otherwise
        """
        try:
            # Generate summaries without LLM
            summaries = {}
            for file_path, file_content in content.items():
                from .utils import extract_first_paragraph
                summaries[file_path] = extract_first_paragraph(file_content)
            
            # Extract key concepts using pattern matching
            concepts = extract_concepts_patterns(content)
            
            # Create optimization structure
            cache = {
                "version": "2.0.0",
                "timestamp": datetime.now().isoformat(),
                "optimization_type": "simple",
                "files": list(content.keys()),
                "summaries": summaries,
                "concepts": concepts,
                "consolidated": generate_simple_view(content),
                "relevance_scores": calculate_simple_scores(content)
            }
            
            # Write cache to file
            cache_path.write_text(json.dumps(cache, indent=2))
            
            logger.info(f"Cache optimized (simple) for {bank_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error in simple optimization for {bank_path}: {e}")
            return False
            
    async def _optimize_with_llm(self, bank_path: Path, content: Dict[str, str], 
                          bank_type: str, cache_path: Path) -> bool:
        """Perform advanced optimization using LLM.
        
        Args:
            bank_path: Path to the memory bank root
            content: Dict mapping file paths to their content
            bank_type: Type of memory bank (global, project, code)
            cache_path: Path where cache file should be written
            
        Returns:
            True if optimization was successful, False otherwise
        """
        try:
            if not self.api_key:
                logger.warning("No LLM API key provided. Falling back to simple optimization.")
                return self._optimize_simple(bank_path, content, cache_path)
                
            # Generate file summaries using LLM
            summaries = await generate_summaries(self, content)
            
            # Extract key concepts and relationships using LLM
            concepts, relationships = await extract_concepts(self, content, bank_type)
            
            # Generate consolidated view using LLM
            consolidated = await generate_consolidated_view(self, content, bank_type)
            
            # Calculate relevance scores using patterns and keywords
            relevance_scores = await calculate_relevance_scores(self, content, concepts)
            
            # Create optimization structure with LLM-enhanced data
            cache = {
                "version": "2.0.0",
                "timestamp": datetime.now().isoformat(),
                "optimization_type": "llm",
                "files": list(content.keys()),
                "summaries": summaries,
                "concepts": concepts,
                "relationships": relationships,
                "consolidated": consolidated,
                "relevance_scores": relevance_scores
            }
            
            # Write cache to file
            cache_path.write_text(json.dumps(cache, indent=2))
            
            logger.info(f"Cache optimized (LLM) for {bank_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error in LLM optimization for {bank_path}: {e}")
            # Fall back to simple optimization on LLM failure
            logger.info("Falling back to simple optimization")
            return self._optimize_simple(bank_path, content, cache_path)
    
    async def call_llm(self, prompt: str) -> str:
        """Call the LLM API with the given prompt.
        
        Args:
            prompt: Prompt to send to LLM
            
        Returns:
            LLM response text
        """
        if not self.api_key:
            raise ValueError("No API key provided")
        
        # OpenRouter configuration
        if "openrouter.ai" in self.api_url:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://memory-bank.claude-desktop.local",
                "X-Title": "Claude Desktop Memory Bank"
            }
        # Anthropic configuration
        elif "anthropic.com" in self.api_url:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
        # Generic configuration
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000
        }
        
        try:
            logger.info(f"Calling LLM API: {self.api_url} with model {self.model}")
            response = await self.http_client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            # Extract the response content based on API format
            if "choices" in response_data:  # OpenAI/OpenRouter format
                return response_data["choices"][0]["message"]["content"]
            elif "content" in response_data:  # Anthropic API format
                return response_data["content"][0]["text"]
            elif "completion" in response_data:  # Legacy format
                return response_data["completion"]
            else:
                logger.error(f"Unexpected response format: {response_data}")
                raise ValueError("Unexpected response format from LLM API")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error calling LLM API: {e}")
            raise
