"""
LLM-based content processor for memory bank.

Implements the main LLMProcessor class for intelligent content processing.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from memory_bank.content.processors.base_processor import ContentProcessor
from memory_bank.content.processors.rule_processor import RuleBasedProcessor
from memory_bank.cache.llm.optimizer import LLMCacheOptimizer
from memory_bank.utils.service_config import llm_config, is_llm_configured, ApiStatus

from .prompts import (
    generate_content_analysis_prompt,
    generate_concept_extraction_prompt,
    generate_relationship_prompt
)
from .parsers import (
    parse_llm_response,
    parse_concept_response,
    parse_relationship_response,
    validate_results
)

logger = logging.getLogger(__name__)


class LLMProcessor(ContentProcessor):
    """LLM-powered content processor implementation.
    
    Uses LLM capabilities to analyze content for optimal categorization,
    identify relationships, and determine appropriate file targets.
    """
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None, 
                 model: Optional[str] = None):
        """Initialize the LLM processor.
        
        Args:
            api_key: API key for LLM service (default: from service_config)
            api_url: URL for LLM API (default: from service_config)
            model: LLM model to use (default: from service_config)
        """
        # Initialize the LLM optimizer for API calls
        self.llm_optimizer = LLMCacheOptimizer(api_key, api_url, model)
        
        # Initialize the fallback processor
        self.fallback_processor = RuleBasedProcessor()
        
        # Target file mappings (same as ContentAnalyzer for consistency)
        # Import here to avoid circular imports
        from memory_bank.content.content_analyzer import ContentAnalyzer
        self.file_mapping = ContentAnalyzer.FILE_MAPPING
        
    async def close(self):
        """Close the LLM processor and release resources."""
        await self.llm_optimizer.close()
        
    async def process_content(self, content: str, existing_cache: Dict[str, str],
                         bank_type: str) -> Dict[str, Any]:
        """Process content using LLM-based analysis.
        
        Args:
            content: New conversation content to process
            existing_cache: Existing memory bank content
            bank_type: Type of bank (global, project, code)
            
        Returns:
            Dict with processing results
        """
        # First, check if LLM is available
        llm_status = llm_config.get_status()
        if not is_llm_configured() or (hasattr(llm_status, 'value') and llm_status.value != 'CONFIGURED') and llm_status != 'CONFIGURED' and llm_status != ApiStatus.CONFIGURED:
            logger.warning("LLM not properly configured or unavailable. Using fallback processor.")
            return await self.fallback_processor.process_content(content, existing_cache, bank_type)
        
        try:
            # Generate the prompt
            prompt = generate_content_analysis_prompt(content, existing_cache, bank_type, self.file_mapping)
            
            # Call LLM for content analysis
            llm_response = await self.llm_optimizer.call_llm(prompt)
            
            # Parse and validate the LLM response
            result = parse_llm_response(llm_response, bank_type, self.file_mapping)
            
            # Validate the results with safety checks
            if not validate_results(result, bank_type, self.file_mapping):
                logger.warning("Invalid LLM response. Using fallback processor.")
                return await self.fallback_processor.process_content(content, existing_cache, bank_type)
                
            # Extract key concepts using LLM
            concept_prompt = generate_concept_extraction_prompt(content)
            concept_response = await self.llm_optimizer.call_llm(concept_prompt)
            concepts = parse_concept_response(concept_response)
            
            # Determine relationships (this requires existing content)
            relationship_prompt = generate_relationship_prompt(content, existing_cache)
            relationship_response = await self.llm_optimizer.call_llm(relationship_prompt)
            relationships = parse_relationship_response(relationship_response)
            
            # Add metadata to the results
            from datetime import datetime
            result["metadata"] = {
                "timestamp": datetime.now().isoformat(),
                "processing_method": "llm",
                "concepts": concepts,
                "relationships": relationships
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in LLM content processing: {e}")
            logger.info("Falling back to rule-based processing")
            return await self.fallback_processor.process_content(content, existing_cache, bank_type)
    
    async def optimize_content(self, content: Dict[str, str], 
                          min_tokens: int, max_tokens: int) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Optimize content using LLM analysis to reduce size while preserving key information.
        
        Args:
            content: Dict of file content to optimize
            min_tokens: Minimum target token count
            max_tokens: Maximum target token count
            
        Returns:
            Tuple of (optimized_content, optimization_metadata)
        """
        # Check if LLM is available
        llm_status = llm_config.get_status()
        if not is_llm_configured() or (hasattr(llm_status, 'value') and llm_status.value != 'CONFIGURED') and llm_status != 'CONFIGURED' and llm_status != ApiStatus.CONFIGURED:
            logger.warning("LLM not properly configured or unavailable for optimization.")
            raise ValueError("LLM optimization not available")
        
        try:
            # Generate the optimization prompt
            from .prompts import generate_optimization_prompt
            prompt = generate_optimization_prompt(content, min_tokens, max_tokens)
            
            # Call LLM for optimization
            llm_response = await self.llm_optimizer.call_llm(prompt)
            
            # Parse the response
            from .parsers import parse_optimization_response
            optimized_content = parse_optimization_response(llm_response, content)
            
            # Calculate token estimates for original and optimized content
            from datetime import datetime
            
            # A simple approximation of token count (4 chars per token)
            orig_chars = sum(len(c) for c in content.values())
            opt_chars = sum(len(c) for c in optimized_content.values())
            
            orig_tokens = orig_chars // 4
            opt_tokens = opt_chars // 4
            
            # Create metadata
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "optimization_type": "llm",
                "original_token_estimate": orig_tokens,
                "optimized_token_estimate": opt_tokens,
                "reduction_percent": round((orig_tokens - opt_tokens) / orig_tokens * 100, 1) if orig_tokens > 0 else 0,
                "token_target_range": [min_tokens, max_tokens]
            }
            
            return optimized_content, metadata
            
        except Exception as e:
            logger.error(f"Error in LLM content optimization: {e}")
            raise
            
    def extract_key_concepts(self, content: str) -> Dict[str, List[str]]:
        """Synchronous wrapper for concept extraction.
        
        This is primarily used when LLM processing isn't available.
        For LLM-based extraction, the process_content method handles this asynchronously.
        
        Args:
            content: Content to analyze
            
        Returns:
            Dict mapping concept categories to lists of key concepts
        """
        # Use the fallback processor for synchronous operation
        return self.fallback_processor.extract_key_concepts(content)
        
    def determine_content_relationships(self, content: str, 
                                   existing_cache: Dict[str, str]) -> Dict[str, List[str]]:
        """Synchronous wrapper for relationship determination.
        
        This is primarily used when LLM processing isn't available.
        For LLM-based extraction, the process_content method handles this asynchronously.
        
        Args:
            content: New content to analyze
            existing_cache: Existing memory bank content
            
        Returns:
            Dict mapping relationship types to lists of related files
        """
        # Use the fallback processor for synchronous operation
        return self.fallback_processor.determine_content_relationships(content, existing_cache)
        
    async def optimize_content(self, content: Dict[str, str], 
                          min_tokens: int, max_tokens: int) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Optimize content using LLM-based analysis.
        
        Args:
            content: Dict of file content to optimize
            min_tokens: Minimum target size in tokens
            max_tokens: Maximum target size in tokens
            
        Returns:
            Tuple of (optimized_content, optimization_metadata)
            
        Raises:
            ValueError: If optimization fails
        """
        # First, check if LLM is available
        llm_status = llm_config.get_status()
        if not is_llm_configured() or (hasattr(llm_status, 'value') and llm_status.value != 'CONFIGURED') and llm_status != 'CONFIGURED' and llm_status != ApiStatus.CONFIGURED:
            logger.warning("LLM not properly configured or unavailable for optimization")
            raise ValueError("LLM not properly configured for optimization")
        
        try:
            # Import here to avoid circular imports
            from memory_bank.content.processors.llm.prompts import generate_optimization_prompt
            from memory_bank.content.processors.llm.parsers import parse_optimization_response
            
            # Generate the optimization prompt
            prompt = generate_optimization_prompt(content, min_tokens, max_tokens)
            
            # Call the LLM for optimization
            llm_response = await self.llm_optimizer.call_llm(prompt)
            
            # Parse the response
            optimized_content = parse_optimization_response(llm_response, content)
            
            # Check if we got a valid result
            if not optimized_content:
                raise ValueError("LLM optimization produced no valid content")
                
            # Return the optimized content and metadata
            metadata = {
                "optimization_timestamp": datetime.now().isoformat(),
                "optimization_method": "llm",
                "initial_files": list(content.keys()),
                "optimized_files": list(optimized_content.keys())
            }
            
            return optimized_content, metadata
            
        except Exception as e:
            logger.error(f"Error in LLM content optimization: {e}")
            raise ValueError(f"LLM optimization failed: {e}")