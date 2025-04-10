"""
Shared fixtures for memory bank tests.
"""

import pytest
import pytest_asyncio
import asyncio
import json
from pathlib import Path
import tempfile
import shutil
import os

from memory_bank.server import MemoryBankServer
from memory_bank.storage.manager import StorageManager


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for memory bank storage."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def storage_manager(temp_storage_dir):
    """Create a storage manager with a temporary storage directory."""
    return StorageManager(temp_storage_dir)


@pytest_asyncio.fixture
async def server(temp_storage_dir):
    """Create and start a memory bank server with a temporary storage directory."""
    server_obj = MemoryBankServer(storage_root=temp_storage_dir)
    await server_obj.start()
    yield server_obj
    await server_obj.stop()


def parse_response(response):
    """Parse MCP response from TextContent to dictionary."""
    if isinstance(response, list) and len(response) > 0:
        text_content = response[0]
        if hasattr(text_content, 'text'):
            return json.loads(text_content.text)
    return response
