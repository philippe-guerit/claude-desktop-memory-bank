"""
Utilities module for Claude Desktop Memory Bank.

This module provides utility functions for the memory bank.
"""

from .git import detect_git_repo
from .file import ensure_directory, read_file, write_file

__all__ = [
    "detect_git_repo",
    "ensure_directory",
    "read_file",
    "write_file",
]
