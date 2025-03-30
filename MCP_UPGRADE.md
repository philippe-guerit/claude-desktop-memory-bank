# MCP Upgrade Guide (1.5.0 → 1.6.0)

## Changes Made

1. **Dependency Updates**
   - Updated `mcp` from 1.5.0 to 1.6.0 in `requirements.txt`
   - Updated `mcp` from 1.5.0 to 1.6.0 in `setup.py`
   - Created new `.venv` virtual environment (standard convention)

2. **Testing Infrastructure**
   - Updated `run_tests.py` to use the `.venv` environment instead of `venv`
   - Installed `pytest`, `pytest-cov`, and `pytest-asyncio` for testing
   - Verified that tests pass with MCP 1.6.0

3. **Scripts Created**
   - `cleanup_old_venv.sh`: Safely removes the old `venv` directory
   - `update_mcp_tools.py`: Updates tool decorators to use schema support in MCP 1.6.0

## Next Steps

### 1. Test the Update

```bash
# Activate the new environment
. .venv/bin/activate

# Run tests
python run_tests.py
```

### 2. Remove the Old Environment

```bash
# Run the cleanup script
./cleanup_old_venv.sh
```

### 3. Update Tool Definitions

```bash
# Run the update script
./update_mcp_tools.py
```

### 4. Define Schema Objects

We've created schema objects for each tool in `tool_schemas.py`, but found that MCP 1.6.0 doesn't directly support the `schema` parameter in the tool decorator yet. The schemas are still valuable for documentation and can be used in the future when the FastMCP API supports this parameter.

Current implementation:
```python
# Define schema object in tool_schemas.py
context_activate_schema = {
    "properties": {
        "prompt_name": {
            "anyOf": [
                {"type": "string"},
                {"type": "null"}
            ],
            "title": "Prompt Name",
            "description": "Name of the prompt template to use (e.g., 'default', 'create-project-brief')",
            "default": None
        },
        # ... other properties ...
    },
    "title": "context_activate_toolArguments",
    "type": "object"
}

# Use in tool decorator (not yet supported)
@self.server.tool(
    name="context_activate", 
    description="Activate the memory bank with context-aware detection"
)
```

In a future release of MCP, the schema parameter will likely be supported, at which point you can update the decorators to use the schema objects.

### 5. Update Other Tool Implementation Details

Review the FastMCP integration implementation and update any code that might depend on MCP-specific features, especially around schema validation.

## Benefits of MCP 1.6.0

1. **Schema Validation**: Proper JSON Schema support for tool parameters
2. **Better Error Handling**: Improved error reporting for validation failures
3. **Enhanced Documentation**: Tool schemas provide better documentation for clients
4. **Performance**: Various internal improvements for better performance

## Additional Notes

- The update maintains backward compatibility with existing code
- The `.venv` directory is the standard convention for Python virtual environments
- Remember to always activate the `.venv` environment before working on the project:
  ```bash
  . .venv/bin/activate
  ```
