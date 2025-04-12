# Compatibility Notes

This document provides information about compatibility considerations for the Claude Desktop Memory Bank.

## MCP Version Compatibility

Claude Desktop Memory Bank v2.0.0 is compatible with MCP 1.6.0 and later versions. The implementation follows the Model Context Protocol specifications and makes use of the Python SDK (`mcp[cli]>=1.6.0`).

## Python Compatibility

The Memory Bank is compatible with Python 3.8 and later versions. The implementation has been tested with:
- Python 3.8
- Python 3.9
- Python 3.10 
- Python 3.11
- Python 3.12

## Dependencies

The Memory Bank has the following key dependencies:
- `mcp[cli]>=1.6.0`: The Model Context Protocol SDK
- `httpx>=0.23.0`: HTTP client for async requests
- `python-dotenv>=1.0.0`: Environment variable management
- `pyyaml>=6.0`: YAML parsing and generation
- `gitpython>=3.1.30`: Git repository interaction (optional)

For development, the following additional dependencies are used:
- `pytest>=7.0.0`: Testing framework
- `pytest-asyncio>=0.20.0`: Async support for pytest
- `pytest-cov>=4.0.0`: Coverage reporting for pytest
- `flake8>=6.0.0`: Linting
- `black>=24.0.0`: Code formatting
- `isort>=5.12.0`: Import sorting

## Third-Party Library Patches

To ensure compatibility with all supported Python and dependency versions, the Memory Bank includes a patching mechanism.

### Patches System

The Memory Bank includes a patching system located in `memory_bank/patches/__init__.py`. This system applies runtime patches to third-party libraries to:
1. Fix deprecation warnings
2. Ensure compatibility across different versions
3. Apply workarounds for known issues

The patches are applied automatically when the Memory Bank package is imported.

### Current Patches

#### MCP Pydantic Integration

The Memory Bank applies a patch to fix a Pydantic deprecation warning in the MCP library:

```python
# Fix for "Accessing the 'model_fields' attribute on the instance is deprecated"
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
```

This patch addresses a Pydantic 2.11+ deprecation warning about accessing `model_fields` on the instance instead of the class.

## Testing Compatibility

The test suite includes configuration to ensure compatibility across supported environments:

1. **pytest.ini**: Configures pytest to work correctly with asyncio and suppresses known warnings
2. **GitHub Actions**: Tests the code on multiple Python versions (3.8-3.12)
3. **Response Parsing**: Handles compatibility with different MCP response formats
4. **Mock Transport**: New test transport system provides consistent testing environment
5. **Test Mode**: Server supports a dedicated test mode that bypasses stdio requirements

### Mock Transport System

The new mock transport system provides several compatibility advantages:

- **Platform Independence**: Tests work consistently across operating systems
- **Environment Isolation**: Transport mocking eliminates environmental dependencies
- **Direct Tool Access**: The `call_tool_test` method provides consistent interface for tool testing
- **Improved Reliability**: Removes dependencies on actual stdio streams that can vary between systems

## Handling Breaking Changes

When handling breaking changes in dependencies:

1. **Versioned Requirements**: Dependencies are specified with minimum versions to ensure compatibility
2. **Conditional Imports**: Code uses conditional imports for optional dependencies
3. **Feature Detection**: Implementation detects available features rather than relying on version checks
4. **Runtime Patches**: The patches system applies fixes as needed

## Future Compatibility Considerations

As MCP and its dependencies evolve, future versions of the Memory Bank will:

1. Track and adapt to changes in the MCP protocol
2. Update compatibility patches as needed
3. Maintain backward compatibility where possible
4. Clearly document breaking changes when they occur

## Reporting Compatibility Issues

If you encounter compatibility issues with specific Python versions or dependency combinations, please:

1. Check if the issue is already addressed in the patches system
2. Report the issue with detailed environment information
3. Include the specific error messages and stack traces
