"""
Mock transport implementation for testing MCP servers.

This module provides a drop-in replacement for the stdio_server context manager
used by the MCP SDK, allowing tests to mock stdin/stdout communication.
"""

import asyncio
import anyio
import json
import logging
import sys
from typing import Dict, Any, Tuple, Optional, AsyncIterator, TypeVar, Generic
from contextlib import asynccontextmanager
from io import TextIOWrapper

from mcp.types import JSONRPCMessage

logger = logging.getLogger(__name__)

T = TypeVar("T")


class QueueStream:
    """A stream that reads from and writes to a queue."""
    
    def __init__(self):
        """Initialize the queue stream."""
        self.queue = asyncio.Queue()
        self.closed = False
    
    async def write(self, data: str) -> None:
        """
        Write data to the queue.
        
        Args:
            data: The data to write.
        """
        if self.closed:
            raise anyio.ClosedResourceError()
        
        logger.debug(f"QueueStream write: {data.strip()}")
        await self.queue.put(data)
    
    async def read(self) -> str:
        """
        Read data from the queue.
        
        Returns:
            The data read from the queue.
        """
        if self.closed:
            raise anyio.ClosedResourceError()
        
        data = await self.queue.get()
        logger.debug(f"QueueStream read: {data.strip()}")
        return data
    
    async def flush(self) -> None:
        """Flush the stream (no-op for queues)."""
        pass
    
    async def close(self) -> None:
        """Close the stream."""
        self.closed = True
    
    async def __aiter__(self) -> AsyncIterator[str]:
        """Make this an async iterator."""
        while not self.closed:
            try:
                data = await self.read()
                yield data
            except anyio.ClosedResourceError:
                break
            except asyncio.CancelledError:
                break


class MockMemoryObjectStream(Generic[T]):
    """A mock memory object stream."""
    
    def __init__(self):
        """Initialize the memory object stream."""
        self.queue = asyncio.Queue()
        self.closed = False
    
    async def send(self, item: T) -> None:
        """
        Send an item to the stream.
        
        Args:
            item: The item to send.
        """
        if self.closed:
            raise anyio.ClosedResourceError()
        
        await self.queue.put(item)
    
    async def receive(self) -> T:
        """
        Receive an item from the stream.
        
        Returns:
            The item received.
        """
        if self.closed:
            raise anyio.ClosedResourceError()
        
        return await self.queue.get()
    
    async def __aiter__(self) -> AsyncIterator[T]:
        """Make this an async iterator."""
        while not self.closed:
            try:
                item = await self.receive()
                yield item
            except anyio.ClosedResourceError:
                break
            except asyncio.CancelledError:
                break
    
    async def aclose(self) -> None:
        """Close the stream."""
        self.closed = True


class MockTransport:
    """
    Mock transport for testing MCP servers.
    
    This class provides a way to send requests and receive responses
    when testing the MCP server.
    """
    
    def __init__(self):
        """Initialize the mock transport."""
        self.stdin_stream = QueueStream()
        self.stdout_stream = QueueStream()
        self.request_id = 1
        logger.debug("MockTransport initialized")
    
    async def put_request(self, method: str, params: Dict[str, Any]) -> None:
        """
        Add a request to the stdin stream.
        
        Args:
            method: The JSON-RPC method to call.
            params: The parameters for the method.
        """
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id
        }
        self.request_id += 1
        
        logger.debug(f"Adding request to queue: {request}")
        json_data = json.dumps(request) + "\n"
        await self.stdin_stream.write(json_data)
    
    async def get_response(self) -> Dict[str, Any]:
        """
        Get a response from the stdout stream.
        
        Returns:
            The JSON-RPC response.
        """
        json_data = await self.stdout_stream.read()
        response = json.loads(json_data)
        logger.debug(f"Got response from queue: {response}")
        return response


@asynccontextmanager
async def mock_stdio_server():
    """
    A mock version of mcp.server.stdio.stdio_server for testing.
    
    This AsyncContextManager is a simplified version that can be used as a
    drop-in replacement for the real stdio_server during testing.
    """
    # Create a transport instance for test control
    transport = MockTransport()
    
    try:
        # Yield stdin and stdout streams to mimic the real stdio_server
        yield transport.stdin_stream, transport.stdout_stream
    finally:
        # Cleanup
        await transport.stdin_stream.close()
        await transport.stdout_stream.close()
