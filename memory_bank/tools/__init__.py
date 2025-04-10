"""
Tools module for Claude Desktop Memory Bank.

This module provides the MCP tools for the memory bank.
"""

from .activate import register_activate_tool
from .list import register_list_tool
from .swap import register_swap_tool
from .update import register_update_tool

__all__ = [
    "register_activate_tool",
    "register_list_tool",
    "register_swap_tool",
    "register_update_tool",
]
