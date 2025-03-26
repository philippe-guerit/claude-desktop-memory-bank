"""
Core business logic for Memory Bank.

This package contains pure, framework-agnostic functions that implement
the actual business logic of the Memory Bank system, independent of
any specific integration framework like FastMCP.
"""

# Export fluent API-style functions
from .memory_bank import (
    activate,
    select,
    list
)

from .context import (
    update
)

# Export functions from context module
from .context import (
    get_context,
    get_all_context,
    get_memory_bank_info,
    _prune_context_internal
)

# Internal helper functions (not exported as public API)
# For internal use only by context.activate
from .memory_bank import (
    _detect_repository_internal,
    _initialize_repository_memory_bank_internal,
    _create_project_internal
)
