"""
Patches for third-party libraries.

This module applies patches to third-party libraries to fix issues or
add functionality needed by the memory bank.
"""

import logging

logger = logging.getLogger(__name__)


def apply_patches():
    """Apply all patches to third-party libraries."""
    logger.info("Applying patches to third-party libraries...")
    
    # Apply patches
    patch_mcp_pydantic()
    
    logger.info("All patches applied successfully.")


def patch_mcp_pydantic():
    """
    Patch the MCP library to fix Pydantic deprecation warnings.
    
    This fixes the "Accessing the 'model_fields' attribute on the instance is deprecated"
    warning by updating the ArgModelBase.model_dump_one_level method to access model_fields
    from the class instead of the instance.
    """
    try:
        # Import the module to patch
        from mcp.server.fastmcp.utilities.func_metadata import ArgModelBase
        
        # Save the original method
        original_model_dump_one_level = ArgModelBase.model_dump_one_level
        
        # Define the patched method
        def patched_model_dump_one_level(self):
            """Return a dict of the model's fields, one level deep.
            
            That is, sub-models etc are not dumped - they are kept as pydantic models.
            
            This is a patched version that accesses model_fields from the class instead
            of the instance to avoid Pydantic deprecation warnings.
            """
            kwargs = {}
            # Access model_fields from the class instead of the instance
            for field_name in self.__class__.model_fields.keys():
                kwargs[field_name] = getattr(self, field_name)
            return kwargs
        
        # Apply the patch
        ArgModelBase.model_dump_one_level = patched_model_dump_one_level
        
        logger.info("Successfully patched MCP Pydantic deprecation")
    except (ImportError, AttributeError) as e:
        logger.warning(f"Failed to apply MCP Pydantic patch: {e}")
