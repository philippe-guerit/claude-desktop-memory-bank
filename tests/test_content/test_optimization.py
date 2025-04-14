"""
Tests for content optimization functionality.

Verifies the content optimization features work correctly
with both LLM-based and rule-based approaches.
"""

import pytest
from unittest.mock import patch, MagicMock
import asyncio
from typing import Dict, Any

from memory_bank.content.async_bridge import AsyncBridge


class TestContentOptimization:
    """Tests for content optimization."""
    
    @pytest.fixture
    def sample_content(self):
        """Fixture to create sample content for testing."""
        return {
            "doc/architecture.md": """# Architecture
            
            This document describes the architecture of our system.
            
            ## Microservices
            
            We've decided to use a microservice architecture for this project.
            This will allow us to scale each component independently.
            
            ## Database
            
            We're using PostgreSQL as our primary database.
            
            ## Historical Decisions
            
            Previously, we considered a monolithic approach but rejected it.
            """,
            
            "doc/design.md": """# Design
            
            ## UI Design
            
            We're using Material UI for consistency across the application.
            
            ## API Design
            
            RESTful APIs will be implemented for all services.
            """,
            
            "tasks.md": """# Tasks
            
            - [ ] Implement authentication service
            - [ ] Set up CI/CD pipeline
            - [ ] Create database schema
            """
        }
    
    @pytest.mark.asyncio
    async def test_async_bridge_with_mocked_optimization(self, sample_content):
        """Test AsyncBridge with mocked content optimization."""
        # Create a mock async function that simulates content optimization
        async def mock_optimize(content, min_tokens, max_tokens):
            # Simulate processing delay
            await asyncio.sleep(0.1)
            
            # Return optimized content and metadata
            optimized = {
                "doc/architecture.md": "# Architecture (Optimized)\n\nUsing microservices with PostgreSQL."
            }
            
            metadata = {
                "optimized": True,
                "method": "test",
                "initial_size": 500,
                "final_size": 100
            }
            
            return optimized, metadata
        
        # Use AsyncBridge to call our mock function
        result = AsyncBridge.run_async_safely(mock_optimize(sample_content, 1000, 2000))
        
        # Verify we get the expected result
        assert isinstance(result, tuple)
        assert len(result) == 2
        optimized, metadata = result
        
        assert "doc/architecture.md" in optimized
        assert "Optimized" in optimized["doc/architecture.md"]
        assert metadata["optimized"] is True
        assert metadata["method"] == "test"
    
    @pytest.mark.asyncio
    async def test_llm_optimization_with_mock(self, sample_content):
        """Test LLM optimization with mocked LLM responses."""
        # Import here to avoid importing during module load
        from memory_bank.content.processors.llm.processor import LLMProcessor
        
        # Create a mock LLM optimizer
        mock_optimizer = MagicMock()
        mock_response = asyncio.Future()
        mock_response.set_result('{"doc/architecture.md": "# LLM-Optimized\\n\\nUsing microservices with PostgreSQL."}')
        mock_optimizer.call_llm = MagicMock(return_value=mock_response)
        
        # Patch LLM configuration checks
        with patch('memory_bank.utils.service_config.is_llm_configured') as mock_config:
            mock_config.return_value = True
            with patch('memory_bank.utils.service_config.llm_config') as mock_llm_config:
                mock_llm_config.get_status.return_value = "CONFIGURED"
                
                # Create the LLM processor with the mock optimizer
                processor = LLMProcessor()
                processor.llm_optimizer = mock_optimizer
                
                # Call the optimize_content method
                optimized, metadata = await processor.optimize_content(sample_content, 1000, 2000)
                
                # Check the result
                assert optimized is not None
                assert "doc/architecture.md" in optimized
                assert "LLM-Optimized" in optimized["doc/architecture.md"]
                assert metadata["optimization_method"] == "llm"
                
                # Verify the correct prompt was used
                mock_optimizer.call_llm.assert_called_once()
                prompt = mock_optimizer.call_llm.call_args[0][0]
                assert "optimize" in prompt.lower()
                assert "content" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_optimization_error_handling(self):
        """Test error handling in optimization."""
        # Import here to avoid importing during module load
        from memory_bank.content.processors.llm.processor import LLMProcessor
        
        # Create a processor that will fail
        processor = LLMProcessor()
        
        # Make call_llm raise an exception
        processor.llm_optimizer.call_llm = MagicMock(side_effect=Exception("Test error"))
        
        # Patch LLM configuration checks
        with patch('memory_bank.utils.service_config.is_llm_configured') as mock_config:
            mock_config.return_value = True
            with patch('memory_bank.utils.service_config.llm_config') as mock_llm_config:
                mock_llm_config.get_status.return_value = "CONFIGURED"
                
                # Call optimize_content and expect an exception
                with pytest.raises(ValueError) as excinfo:
                    await processor.optimize_content({"test.md": "content"}, 1000, 2000)
                
                # Check the error message
                assert "LLM optimization failed" in str(excinfo.value)
