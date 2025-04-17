# Claude Desktop Memory Bank API Reference

This document provides a detailed reference for the Model Context Protocol (MCP) tools exposed by the Claude Desktop Memory Bank.

## MCP Tools

The Memory Bank implements three main tools:

1. [activate](#activate): Activate a memory bank at conversation start
2. [list](#list): List available memory banks
3. [update](#update): Update memory bank content

## Tool Reference

### `activate`

Activates and loads a memory bank for the current conversation.

#### Parameters

| Name | Type | Required | Description |
| ---- | ---- | -------- | ----------- |
| `bank_type` | string | Yes | Type of memory bank to activate (`"global"`, `"project"`, or `"code"`) |
| `bank_id` | string | Yes | Identifier for the specific memory bank instance (use `"auto"` for automatic detection) |
| `current_path` | string | No | Current path for code context detection |
| `project_name` | string | No | Project name for creating new projects |
| `project_description` | string | No | Project description for creating new projects |

#### Returns

```json
{
  "status": "success",
  "bank_info": {
    "type": "code",
    "id": "my-repo",
    "files": [
      "readme.md",
      "doc/architecture.md",
      "doc/design.md",
      "doc/api.md",
      "structure.md",
      "snippets.md"
    ],
    "last_updated": "2025-04-09T15:30:22Z"
  },
  "content": {
    "readme.md": "# My Repository\n\n## Repository Overview\nA brief description of the codebase.\n\n...",
    "doc/architecture.md": "# Code Architecture\n\n## Architecture Overview\nOverview of the code architecture.\n\n...",
    "doc/design.md": "# Design\n\n## Design Principles\nCore design principles for the codebase.\n\n...",
    "doc/api.md": "# API Documentation\n\n## Public API\nDocumentation for the public API.\n\n...",
    "structure.md": "# Code Structure\n\n## Directory Structure\nOverview of the directory structure.\n\n...",
    "snippets.md": "# Code Snippets\n\n## Important Snippets\nCode snippets that are important to remember.\n\n..."
  },
  "custom_instructions": {
    "directives": [
      {
        "name": "WATCHDOG",
        "priority": "SYSTEM CRITICAL",
        "when": "After every response",
        "action": "Call update tool"
      },
      {
        "name": "CODE_ARCHITECTURE_UPDATE",
        "priority": "HIGH",
        "when": "User discusses code architecture or design decisions",
        "action": "CALL update with target_file='doc/architecture.md'"
      },
      {
        "name": "API_UPDATE",
        "priority": "HIGH",
        "when": "User discusses API design or usage",
        "action": "CALL update with target_file='doc/api.md'"
      },
      {
        "name": "SNIPPET_CAPTURE",
        "priority": "MEDIUM",
        "when": "User shares important code patterns or examples",
        "action": "CALL update with target_file='snippets.md'"
      }
    ],
    "prompts": [
      {
        "id": "code_default",
        "text": "You're a coding assistant with access to the code memory bank for \"my-repo\".\nUse this context to discuss code architecture, design patterns, API usage, and implementation details.\n\nThis repository is currently on branch: main\n\nPay special attention to architecture decisions, design patterns, and API usage.\nUpdate the memory bank when you observe important context that should persist\nacross conversations about this codebase."
      }
    ],
    "examples": {
      "trigger_patterns": [
        "We decided to use [technology]",
        "We're implementing [pattern]",
        "The architecture will be [description]",
        "I've completed [task]",
        "Next, we need to [task]"
      ],
      "verification": "// Update #[N] for conversation [id]"
    }
  }
}
```

#### Usage Examples

Basic activation:
```javascript
activate(bank_type="global", bank_id="default")
```

Activating code bank with automatic repository detection:
```javascript
activate(bank_type="code", bank_id="auto", current_path="/path/to/repo")
```

Creating a new project:
```javascript
activate(bank_type="project", bank_id="my-project", project_name="My Project", project_description="A project to develop a new feature.")
```

### `list`

Lists all available memory banks.

#### Parameters

| Name | Type | Required | Description |
| ---- | ---- | -------- | ----------- |
| `bank_type` | string | No | Optional type filter (`"global"`, `"project"`, or `"code"`) |

#### Returns

```json
{
  "global": [
    {
      "id": "default",
      "last_used": "2025-04-08T10:20:30Z",
      "description": "Global conversation memory"
    }
  ],
  "projects": [
    {
      "id": "project_x",
      "last_used": "2025-04-09T15:30:22Z",
      "description": "Project X development"
    },
    {
      "id": "project_y",
      "last_used": "2025-04-07T11:45:15Z",
      "description": "Project Y planning"
    }
  ],
  "code": [
    {
      "id": "project_x_repo",
      "last_used": "2025-04-09T16:45:10Z",
      "description": "Project X codebase"
    },
    {
      "id": "utils_lib",
      "last_used": "2025-04-05T09:30:00Z",
      "description": "Utilities library"
    }
  ]
}
```

#### Usage Examples

List all memory banks:
```javascript
list()
```

List only project memory banks:
```javascript
list(bank_type="project")
```



### `update`

Updates the memory bank with new information from the conversation.

#### Parameters

| Name | Type | Required | Description |
| ---- | ---- | -------- | ----------- |
| `bank_type` | string | Yes | Type of memory bank to update (`"global"`, `"project"`, or `"code"`) |
| `bank_id` | string | Yes | Identifier for the specific memory bank to update |
| `target_file` | string | Yes | Specific file to update (e.g., `"doc/design.md"`) |
| `operation` | string | Yes | How to apply the update (`"append"`, `"replace"`, or `"insert"`) |
| `content` | string | Yes | Content to add to the memory bank |
| `position` | string | No | Position identifier for insert operations (e.g., section name) |
| `trigger_type` | string | No | What triggered this update (`"watchdog"`, `"architecture"`, `"technology"`, `"progress"`, `"commit"`, or `"user_request"`) |
| `conversation_id` | string | No | Identifier for the current conversation |
| `update_count` | integer | No | Counter for updates in this conversation |

#### Returns

```json
{
  "status": "success",
  "updated_file": "doc/architecture.md",
  "operation": "append",
  "cache_updated": true,
  "cache_optimized": false,
  "verification": "// Update #3 for conversation conv-123",
  "next_actions": [],
  "previous_errors": []
}
```

With error history (when applicable):

```json
{
  "status": "success",
  "updated_file": "doc/architecture.md",
  "operation": "append",
  "cache_updated": true,
  "cache_optimized": false,
  "verification": "// Update #3 for conversation conv-123",
  "next_actions": [],
  "previous_errors": [
    {
      "timestamp": "2025-04-10T14:32:10Z",
      "description": "Failed to process content for doc/design.md", 
      "severity": "warning"
    },
    {
      "timestamp": "2025-04-10T14:30:05Z",
      "description": "Disk synchronization delayed due to large content size", 
      "severity": "info"
    }
  ]
}
```

In case of error:

```json
{
  "status": "error",
  "error": "Failed to update content: Invalid operation type",
  "previous_errors": [
    {
      "timestamp": "2025-04-10T14:35:22Z",
      "description": "LLM processing failed, using fallback rule-based processing", 
      "severity": "warning"
    }
  ]
}
```

#### Usage Examples

Append new content to a file:
```javascript
update(
  bank_type="project",
  bank_id="project_x",
  target_file="doc/architecture.md",
  operation="append",
  content="## New Component\n\nThis component will handle authentication using OAuth2.",
  trigger_type="architecture",
  conversation_id="conv-123",
  update_count=3
)
```

Replace content in a file:
```javascript
update(
  bank_type="code",
  bank_id="project_x_repo",
  target_file="doc/api.md",
  operation="replace",
  content="# API Documentation\n\n## Authentication API\n\nThe authentication API uses JWT tokens.",
  trigger_type="user_request"
)
```

Insert content at a specific position in a file:
```javascript
update(
  bank_type="global",
  bank_id="default",
  target_file="preferences.md",
  operation="insert",
  content="The user prefers detailed explanations with code examples.",
  position="Communication Style",
  trigger_type="watchdog"
)
```

## Custom Instructions

The Memory Bank provides custom instructions through the `activate` tool. These instructions help guide the assistant in using the memory bank effectively.

### Directive Structure

```json
{
  "name": "DIRECTIVE_NAME",
  "priority": "PRIORITY_LEVEL",
  "when": "TRIGGER_CONDITION",
  "action": "ACTION_TO_PERFORM",
  "patterns": ["PATTERN1", "PATTERN2"]
}
```

### Custom Instructions Object

The custom instructions object returned by the tools has the following structure:

```json
"custom_instructions": {
  "directives": [
    {
      "name": "WATCHDOG",
      "priority": "SYSTEM CRITICAL",
      "when": "After every response",
      "action": "Call update tool"
    },
    {
      "name": "ARCHITECTURE_TRACKING",
      "priority": "HIGH",
      "when": "When architecture decisions detected",
      "patterns": ["decided to use", "implement pattern", "architecture will be"]
    }
  ],
  "prompts": [
    {
      "id": "code_default",
      "text": "You're a coding assistant with access to the code memory bank. Use this context to discuss code architecture, design patterns, API usage, and implementation details."
    },
    {
      "id": "memory_bank_automation",
      "text": "# Custom Instructions for Claude Desktop Memory Bank\n\n## 🔴 SYSTEM CRITICAL COMMAND DIRECTIVES\n\n0. **🔴 WATCHDOG DIRECTIVE: UPDATE AFTER EACH RESPONSE**\n   ```\n   WHEN: IMMEDIATELY after EVERY response delivery \n   PRIORITY: SYSTEM CRITICAL (HIGHEST)\n   ACTION: CALL update WITH appropriate parameters\n   ```"
    }
  ],
  "examples": {
    "trigger_patterns": ["We decided to use [technology]", "We're implementing [pattern]"],
    "verification": "// Update #[N] for conversation [id]"
  }
}
```

### Priority Levels

- `"SYSTEM CRITICAL"`: Highest priority, must be executed
- `"HIGH"`: Important directive that should be executed when detected
- `"MEDIUM"`: Moderate priority, execute when appropriate
- `"LOW"`: Lowest priority, execute when convenient

### Common Directives

1. **WATCHDOG**: Monitors for updates after each response
2. **DECISION_TRACKING**: Tracks important decisions and technical choices
3. **PROGRESS_TRACKING**: Tracks completed work and next steps
4. **MEETING_NOTES**: Captures meeting outcomes and action items
5. **IDEA_CAPTURE**: Records new ideas and brainstorming results
6. **RESEARCH_FINDINGS**: Documents research results and findings
7. **GIT_COMMIT**: Captures information during commit preparation

## File Structure

Each memory bank type has a specific structure:

### Global Memory Bank

- `context.md`: General context and themes
- `preferences.md`: User preferences and patterns
- `references.md`: Frequently referenced materials
- `cache_memory_dump.json`: Diagnostic memory dump (only in debug mode)

### Project Memory Bank

- `readme.md`: Project overview
- `doc/objectives.md`: Goals and objectives
- `doc/decisions.md`: Key decisions (generic)
- `doc/progress.md`: Status updates
- `doc/references.md`: Important references
- `notes/meeting_notes.md`: Meeting summaries
- `notes/ideas.md`: Brainstorming and ideas
- `notes/research.md`: Research findings
- `cache_memory_dump.json`: Diagnostic memory dump (only in debug mode)

### Code Memory Bank

- `readme.md`: Repository overview
- `doc/architecture.md`: Code architecture
- `doc/design.md`: Design patterns
- `doc/api.md`: API documentation
- `structure.md`: Code organization
- `snippets.md`: Important code snippets
- `cache_memory_dump.json`: Diagnostic memory dump (only in debug mode)

## Error Handling

The server returns standard MCP error responses:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Error message",
    "data": {
      "code": "error_code",
      "details": "Additional error details"
    }
  },
  "id": "request_id"
}
```

### Common Error Codes

- `"invalid_bank_type"`: Invalid bank type
- `"bank_not_found"`: Memory bank not found
- `"activation_failed"`: Failed to activate memory bank
- `"list_failed"`: Failed to list memory banks
- `"update_failed"`: Failed to update memory bank
- `"invalid_operation"`: Invalid update operation
- `"content_processing_failed"`: Failed to process content
- `"disk_sync_failed"`: Failed to synchronize with disk
- `"cache_load_failed"`: Failed to load bank into cache

## Cache Architecture

The Memory Bank server implements an in-memory cache architecture for improved performance:

### Cache Manager

The server uses a centralized Cache Manager with the following features:

- **In-Memory Storage**: Memory banks are stored in a shared in-memory dictionary
- **Unique Identification**: Memory banks are keyed by `{bank_type}:{bank_id}`
- **Lazy Loading**: Banks are loaded from disk only when first accessed
- **Background Synchronization**: Content is synchronized to disk asynchronously
- **Configurable Timing**: Default synchronization interval is 60 seconds
- **Immediate Sync Option**: Large updates trigger immediate synchronization
- **Error Tracking**: Maintains history of recent errors for client reporting

### Content Processing

The server uses a dual-path approach for content processing:

- **Primary Path (LLM-based)**: Uses LLM for content categorization and placement
- **Fallback Path (Rule-based)**: Falls back to deterministic rules when LLM is unavailable
- **Standard Interface**: Both paths use the same output schema for consistency
- **Validation Layer**: Validates outputs against constraints before applying changes

### Diagnostic Features

For development and troubleshooting:

- **Debug Memory Dumps**: When enabled, writes complete memory bank state to `cache_memory_dump.json`
- **Error History**: Tracks and returns recent processing errors
- **Token Count Metrics**: Logs approximate token count of memory banks
- **Processing Path Tracking**: Records which path (LLM or rule-based) was used for each operation

## Protocol Optimization

The Memory Bank server implements a key optimization in the MCP protocol:

### Tools-Only Approach

The server only registers tools through the MCP protocol:
- Only tools (activate, list, update) are formally registered
- Prompts and resources are delivered directly through the `activate` tool response
- No separate `mcp.discover` entries for prompts and resources

### Benefits

This optimization provides several advantages:
- Reduced protocol overhead
- Simplified server implementation
- Single delivery mechanism for context and instructions
- More flexibility in formatting custom instructions

### Implementation Details

- `activate` tool returns both context data and custom instructions
- Custom instructions format isn't constrained by MCP prompt schema
- Memory bank content delivered directly rather than through resource URIs
- Server maintains internal resources/prompts without exposing through protocol

## Response Format

### MCP 1.6.0+ Response Format

In MCP 1.6.0 and later, tool responses are returned as `TextContent` objects with the following structure:

```python
[
    TextContent(
        type='text',
        text='{"status": "success", "bank_info": {...}}',
        annotations=None
    )
]
```

To handle these responses correctly, the Memory Bank includes a `parse_response` utility function:

```python
def parse_response(response):
    """Parse MCP response from TextContent to dictionary."""
    if isinstance(response, list) and len(response) > 0:
        text_content = response[0]
        if hasattr(text_content, 'text'):
            return json.loads(text_content.text)
    return response
```

This function is used to convert the TextContent objects to Python dictionaries:

```python
# Call the tool
result = await server.server.call_tool("activate", {...})

# Parse the response
response = parse_response(result[0])

# Access the response data
if response["status"] == "success":
    bank_info = response["bank_info"]
```

The Memory Bank handles this conversion internally, so clients interact with Python dictionaries rather than raw TextContent objects.
