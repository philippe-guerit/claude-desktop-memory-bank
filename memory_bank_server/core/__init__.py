"""
Core business logic for Memory Bank.

This package contains pure, framework-agnostic functions that implement
the actual business logic of the Memory Bank system, independent of
any specific integration framework like FastMCP.
"""

# Export functions from memory_bank module
from .memory_bank import (
    start_memory_bank,
    select_memory_bank,
    list_memory_banks,
    detect_repository,
    initialize_repository_memory_bank,
    create_project
)

# Export functions from context module
from .context import (
    get_context,
    update_context,
    bulk_update_context,
    prune_context,
    get_all_context,
    get_memory_bank_info
)
