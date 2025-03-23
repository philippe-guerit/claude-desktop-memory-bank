# Memory Bank MCP Tools

This document describes the MCP tools available in the Claude Desktop Memory Bank.

## memory-bank-start

Initializes the memory bank and loads a custom prompt.

### Description

This tool orchestrates the initialization process for memory banks. It detects repositories, initializes memory banks when needed, selects the appropriate memory bank based on the detection, and loads a specified prompt or the default custom instructions.

### Parameters

- **prompt_name** (optional): Name of the prompt to load. If not provided, the default custom instruction will be used.
- **auto_detect** (optional): Whether to automatically detect repositories. Default: `true`
- **current_path** (optional): Path to check for repository. Default: Current working directory
- **force_type** (optional): Force a specific memory bank type (`global`, `project`, or `repository`) overriding auto-detection.

### Returns

A confirmation message about the initialization with details about the memory bank that was selected. Includes special `<claude_display>` tags for Claude to recognize and display a confirmation message.

### Example

```json
{
  "type": "tools/call",
  "tool": "memory-bank-start",
  "params": {
    "prompt_name": "expert-developer",
    "auto_detect": true,
    "current_path": "/home/user/projects/my-repo"
  }
}
```

## select-memory-bank

[Documentation for other tools would continue here]
