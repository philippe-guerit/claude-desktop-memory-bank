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

# Import service configuration
from memory_bank.utils.service_config import llm_config, is_llm_configured, ApiStatus


class LLMCacheOptimizer:
    """LLM-powered cache optimization system."""
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None, 
                 model: Optional[str] = None):
        """Initialize the cache optimizer.
        
        Args:
            api_key: API key for LLM service (default: from service_config)
            api_url: URL for LLM API (default: from service_config)
            model: LLM model to use (default: from service_config)
        """
        self.api_key = api_key or llm_config.get_api_key()
        self.api_url = api_url or llm_config.get_api_url()
        self.model = model or llm_config.get_model()
        self.http_client = httpx.AsyncClient(timeout=60.0)
        
        # Threshold for when to use LLM optimization vs. simple optimization
        self.full_optimization_threshold = 8192  # characters
        
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

    def _handle_llm_error(self, exception):
        """Handle an LLM API error by reporting it to the service config.
        
        Args:
            exception: The exception that occurred
        """
        error_msg = str(exception)
        logger.error(f"Error in LLM API call: {error_msg}")
        
        # Report the error to the service config for tracking
        is_auth_error = any(term in error_msg.lower() for term in 
                           ["unauthorized", "authentication", "api key", "auth"])
        is_rate_limit = any(term in error_msg.lower() for term in 
                           ["rate limit", "too many requests", "429"])
        
        if is_auth_error:
            llm_config.report_error(error_msg, is_permanent=True)
        elif is_rate_limit:
            llm_config.report_error(error_msg)
        else:
            llm_config.report_error(error_msg)
        
    async def optimize_cache(self, bank_path: Path, content: Dict[str, str], 
                      bank_type: str, optimization_preference: str = "auto") -> bool:
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
            optimization_preference: Optimization mode preference: "auto", "llm", or "simple"
            
        Returns:
            True if optimization was successful, False otherwise
        """
        try:
            # Ensure the directory exists
            bank_path.mkdir(parents=True, exist_ok=True)
            
            cache_path = bank_path / "cache.json"
            
            # Get current LLM API status
            current_status = llm_config.get_status()
            
            # Check if LLM is available
            if not is_llm_configured() or current_status != ApiStatus.CONFIGURED:
                # Log detailed information about why LLM is not being used
                status_message = f"Using simple optimization. LLM API status: {current_status.value}"
                
                if current_status == ApiStatus.UNCONFIGURED:
                    status_message += " - Missing required configuration"
                elif current_status == ApiStatus.RATE_LIMITED:
                    status_message += " - Rate limited, try again later"
                elif current_status == ApiStatus.ERROR:
                    status_message += " - Experiencing API errors"
                
                logger.warning(status_message)
                
                # Use simple optimization
                simple_result = self._optimize_simple(bank_path, content, cache_path)
                
                # Verify the cache file has the correct type (this is a safety check)
                try:
                    if cache_path.exists():
                        with open(cache_path, "r") as f:
                            cache_data = json.load(f)
                        if cache_data.get("optimization_type") != "simple":
                            logger.warning("Found invalid optimization_type in cache, fixing...")
                            cache_data["optimization_type"] = "simple"
                            with open(cache_path, "w") as f:
                                json.dump(cache_data, f, indent=2)
                except Exception as e:
                    logger.error(f"Error verifying cache file: {e}")
                
                return simple_result
            
            # Determine optimization method based on preference and configuration
            should_use_llm = False
            
            if optimization_preference == "llm":
                # User explicitly requested LLM optimization
                logger.info("LLM optimization explicitly requested")
                should_use_llm = True
            elif optimization_preference == "simple":
                # User explicitly requested simple optimization
                logger.info("Simple optimization explicitly requested")
                should_use_llm = False
            else:  # "auto" mode - make a smart decision
                # Check content size for auto mode
                total_content_size = sum(len(text) for text in content.values())
                logger.info(f"Content size: {total_content_size} chars, threshold: {self.full_optimization_threshold}")
                
                # Use LLM optimization for larger content in auto mode
                should_use_llm = total_content_size > self.full_optimization_threshold
            
            # Execute the appropriate optimization method
            if should_use_llm:
                logger.info(f"Using LLM-based optimization for {bank_path}")
                return await self._optimize_with_llm(bank_path, content, bank_type, cache_path)
            else:
                logger.info(f"Using simple optimization for {bank_path}")
                return self._optimize_simple(bank_path, content, cache_path)
                
        except Exception as e:
            logger.error(f"Error optimizing cache for {bank_path}: {e}")
            # Create a fallback cache for severe failures
            try:
                self._create_fallback_cache(bank_path, content, cache_path)
                logger.info("Created fallback cache after error")
                return True
            except Exception as fallback_error:
                logger.error(f"Failed to create fallback cache: {fallback_error}")
                return False
            
    def _create_fallback_cache(self, bank_path: Path, content: Dict[str, str], cache_path: Path) -> None:
        """Create a minimal fallback cache when optimization fails.
        
        This ensures we always have a valid cache file, even in error conditions.
        
        Args:
            bank_path: Path to the memory bank
            content: Dict mapping file paths to their content
            cache_path: Path to write the cache file
        """
        from datetime import datetime
        
        # Create minimal cache data
        cache = {
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "optimization_type": "fallback",  # Special type for fallback caches
            "optimization_status": "error",  # Indicate there was an error
            "optimization_method": "fallback",  # Method used
            "files": list(content.keys()),
            "summaries": {k: v[:100] + "..." if len(v) > 100 else v for k, v in content.items()},
            "concepts": {},
            "consolidated": {
                "architecture_decisions": "",
                "technology_choices": "",
                "current_status": "",
                "next_steps": ""
            },
            "relevance_scores": {k: 0.5 for k in content.keys()}
        }
        
        # Write cache file
        with open(cache_path, "w") as f:
            json.dump(cache, f, indent=2)
            
        logger.info(f"Created fallback cache for {bank_path} with optimization_type='fallback'")
            
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
                "optimization_status": "success",  # Indicate successful optimization
                "optimization_method": "pattern_matching",  # Describe the method used
                "files": list(content.keys()),
                "summaries": summaries,
                "concepts": concepts,
                "consolidated": generate_simple_view(content),
                "relevance_scores": calculate_simple_scores(content)
            }
            
            # Write cache to file - use nice formatting for readability
            try:
                cache_path.write_text(json.dumps(cache, indent=2))
            except Exception as e:
                logger.error(f"Error writing cache file: {e}")
                # Last ditch effort - try writing directly
                with open(cache_path, "w") as f:
                    json.dump(cache, f)
            
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
            # CRITICAL SECURITY CHECK - DOUBLE CHECK API KEY
            # This is our second line of defense against accessing LLM API without a key
            if not self.api_key:
                logger.warning("SECURITY: No LLM API key in _optimize_with_llm(). Using simple optimization.")
                return self._optimize_simple(bank_path, content, cache_path)
                
            # All LLM calls need to happen after the API key check
            try:
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
                    "optimization_status": "success",
                    "optimization_method": "llm_enhanced",
                    "llm_model": self.model,
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
                # Call our error handler
                self._handle_llm_error(e)
                
                logger.info("Falling back to simple optimization due to LLM API error")
                return self._optimize_simple(bank_path, content, cache_path)
                
        except Exception as e:
            logger.error(f"Error in LLM optimization for {bank_path}: {e}")
            # Fall back to simple optimization on any failure
            logger.info("Falling back to simple optimization")
            return self._optimize_simple(bank_path, content, cache_path)
    
    async def call_llm(self, prompt: str) -> str:
        """Call the LLM API with the given prompt.
        
        Args:
            prompt: Prompt to send to LLM
            
        Returns:
            LLM response text
            
        Raises:
            ValueError: If LLM is not properly configured or available
        """
        # Check LLM configuration status through service config
        if not is_llm_configured() or llm_config.get_status() != ApiStatus.CONFIGURED:
            error_msg = f"LLM API not properly configured or available. Current status: {llm_config.get_status().value}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        if not self.api_key:
            error_msg = "No API key provided"
            llm_config.report_error(error_msg, is_permanent=True)
            raise ValueError(error_msg)
        
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
                error_msg = f"Unexpected response format: {response_data}"
                logger.error(error_msg)
                llm_config.report_error(error_msg)
                raise ValueError(error_msg)
                
        except httpx.HTTPStatusError as e:
            error_msg = f"LLM API HTTP error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            
            # Report specific error types
            if e.response.status_code == 401 or e.response.status_code == 403:
                llm_config.report_error(error_msg, is_permanent=True)
            elif e.response.status_code == 429:
                llm_config.report_error(error_msg)  # Rate limit
            else:
                llm_config.report_error(error_msg)
                
            raise
        except Exception as e:
            error_msg = f"Error calling LLM API: {e}"
            logger.error(error_msg)
            llm_config.report_error(error_msg)
            raise