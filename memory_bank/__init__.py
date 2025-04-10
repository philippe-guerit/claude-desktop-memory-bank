"""
Claude Desktop Memory Bank - MCP server for context persistence.

This package implements a Model Context Protocol (MCP) server that provides
autonomous memory persistence for Claude Desktop.
"""

__version__ = "2.0.0"

# Apply patches to fix third-party library issues
from .patches import apply_patches
apply_patches()

from .server import MemoryBankServer

__all__ = ["MemoryBankServer"]
