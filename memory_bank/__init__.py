"""
Claude Desktop Memory Bank - MCP server for context persistence.

This package implements a Model Context Protocol (MCP) server that provides
autonomous memory persistence for Claude Desktop.
"""

__version__ = "2.0.0"

from .server import MemoryBankServer

__all__ = ["MemoryBankServer"]
