"""
Async/sync bridge for content processing.

Provides utilities to handle the async/sync boundary between
the CacheManager and async content processing components.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Callable, Awaitable, TypeVar, Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Generic type for return values
T = TypeVar('T')


class AsyncBridge:
    """Handles the boundary between synchronous and asynchronous code.
    
    Provides methods to safely call async functions from sync contexts
    and manage event loops correctly across thread boundaries.
    """
    
    # Thread pool for running async code from sync contexts
    _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="async_bridge_")
    
    @staticmethod
    def run_async_in_new_loop(coro: Awaitable[T], timeout: float = 5.0) -> T:
        """Run a coroutine in a new event loop.
        
        This method is used when there is no existing event loop.
        
        Args:
            coro: The coroutine to run
            timeout: Maximum time to wait for completion (seconds)
            
        Returns:
            The result of the coroutine
            
        Raises:
            TimeoutError: If the operation times out
            Exception: Any exception raised by the coroutine
        """
        # In Python 3.12, we need to ensure the coroutine is only awaited once
        # We do this by wrapping it in a function that gets executed by asyncio.run
        async def run_with_timeout():
            return await asyncio.wait_for(coro, timeout)
            
        try:
            return asyncio.run(run_with_timeout())
        except asyncio.TimeoutError as e:
            raise TimeoutError(f"Operation timed out after {timeout}s") from e
    
    @staticmethod
    def run_async_in_existing_loop(coro: Awaitable[T], loop: asyncio.AbstractEventLoop, 
                               timeout: float = 5.0) -> T:
        """Run a coroutine in an existing but not running event loop.
        
        Args:
            coro: The coroutine to run
            loop: The existing event loop
            timeout: Maximum time to wait for completion (seconds)
            
        Returns:
            The result of the coroutine
            
        Raises:
            TimeoutError: If the operation times out
            Exception: Any exception raised by the coroutine
        """
        try:
            # Wrap the coroutine to avoid "cannot reuse already awaited coroutine" errors
            async def wrapper():
                return await asyncio.wait_for(coro, timeout)
                
            return loop.run_until_complete(wrapper())
        except asyncio.TimeoutError as e:
            raise TimeoutError(f"Operation timed out after {timeout}s") from e
    
    @staticmethod
    def run_async_in_thread(coro: Awaitable[T], timeout: float = 5.0) -> T:
        """Run a coroutine in a separate thread.
        
        This is used when we need to run async code from a sync context
        and can't use the current event loop because it's already running.
        
        Args:
            coro: The coroutine to run
            timeout: Maximum time to wait for completion (seconds)
            
        Returns:
            The result of the coroutine
            
        Raises:
            TimeoutError: If the operation times out
            Exception: Any exception raised by the coroutine
        """
        # In Python 3.12, we need to wrap the coroutine in another async function
        # to avoid "cannot reuse already awaited coroutine" errors
        def run_coro():
            async def wrapper():
                return await coro
            return asyncio.run(wrapper())
            
        future = AsyncBridge._executor.submit(run_coro)
        try:
            return future.result(timeout=timeout)
        except Exception as e:
            if isinstance(e, TimeoutError):
                raise TimeoutError(f"Operation timed out after {timeout}s") from e
            raise
    
    @staticmethod
    def run_async_safely(coro: Awaitable[T], timeout: float = 5.0) -> T:
        """Run a coroutine safely from any context.
        
        This method detects the current context and uses the appropriate
        strategy to run the coroutine.
        
        Args:
            coro: The coroutine to run
            timeout: Maximum time to wait for completion (seconds)
            
        Returns:
            The result of the coroutine
            
        Raises:
            TimeoutError: If the operation times out
            Exception: Any exception raised by the coroutine
        """
        try:
            # Detect the current async context
            try:
                # Use get_running_loop to avoid deprecation warnings
                try:
                    loop = asyncio.get_running_loop()
                    # We're in a running event loop - use a separate thread
                    logger.debug("Using thread executor (event loop is running)")
                    return AsyncBridge.run_async_in_thread(coro, timeout)
                except RuntimeError:
                    # No running loop, try to get existing loop
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Loop is running (rare case)
                            logger.debug("Using thread executor (event loop is running)")
                            return AsyncBridge.run_async_in_thread(coro, timeout)
                        else:
                            # We have a loop but it's not running
                            logger.debug("Using existing non-running event loop")
                            return AsyncBridge.run_async_in_existing_loop(coro, loop, timeout)
                    except RuntimeError:
                        # No event loop in this thread
                        logger.debug("No event loop found, creating new one")
                        return AsyncBridge.run_async_in_new_loop(coro, timeout)
            except Exception as e:
                # Catch-all for unexpected issues
                logger.warning(f"Unexpected error detecting event loop: {e}, creating new one")
                return AsyncBridge.run_async_in_new_loop(coro, timeout)
        except Exception as e:
            logger.error(f"Error running async operation: {e}")
            raise
    
    @staticmethod
    def process_content_sync(async_process_func, content: str, existing_cache: Dict[str, str], 
                         bank_type: str, **kwargs) -> Dict[str, Any]:
        """Synchronously process content using an async processor function.
        
        This is a specialized wrapper for content processing functions.
        
        Args:
            async_process_func: The async content processing function
            content: Content to process
            existing_cache: Existing cache content
            bank_type: Type of bank
            **kwargs: Additional keyword arguments
            
        Returns:
            Processed content result
            
        Raises:
            Exception: Any exception raised during processing
        """
        try:
            # Create the coroutine - this is a one-time use object
            coro = async_process_func(content, existing_cache, bank_type, **kwargs)
            
            # Run the coroutine synchronously using our helper
            # The run_async_safely method now properly handles wrapping the coroutine
            result = AsyncBridge.run_async_safely(coro, timeout=10.0)
            
            # Validate the result
            if not isinstance(result, dict) or "target_file" not in result:
                logger.warning(f"Invalid processing result: {result}")
                raise ValueError("Invalid content processing result")
                
            return result
            
        except Exception as e:
            logger.error(f"Content processing failed: {e}")
            raise
