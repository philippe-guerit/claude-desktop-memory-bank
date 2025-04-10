# Claude Desktop Memory Bank MCP Server Design

## Memory Bank Structure

The Claude Desktop Memory Bank follows a structured approach to storing context across conversations:

```
~/.claude-desktop/memory/
├── global/                           # For conversations not in a project
│   ├── context.md                    # General context and themes
│   ├── preferences.md                # User preferences and patterns
│   ├── references.md                 # Frequently referenced materials
│   └── cache.json                    # Optimized representation for LLM use
├── projects/                         # Independent project memory banks
│   └── {project-id}/                 # Project-specific directory
│       ├── readme.md                 # Project overview
│       ├── doc/                      # Documentation directory
│       │   ├── architecture.md       # Architecture decisions
│       │   ├── design.md             # Design documentation
│       │   └── progress.md           # Current state and next steps
│       ├── tasks.md                  # Active tasks and todos
│       └── cache.json                # Optimized representation for LLM use
└── code/                             # Independent code memory banks
    └── {repo-id}/                    # Repository-specific directory
        ├── readme.md                 # Repository overview
        ├── doc/                      # Code documentation directory
        │   ├── architecture.md       # Code architecture
        │   ├── design.md             # Design patterns
        │   └── api.md                # API documentation
        ├── structure.md              # Code organization
        ├── snippets.md               # Important code snippets
        └── cache.json                # Optimized representation for LLM use
```

Each file uses Markdown format with optional YAML frontmatter for metadata:

```yaml
---
last_updated: "2025-04-09T15:30:22Z"
version: 3
relevance_score: 0.87
---
```

## MCP Architecture

The Memory Bank follows the Model Context Protocol (MCP) standards:

1. **Client-Server Roles**: The MCP client (within Claude Desktop) controls tool invocation, not the server or LLM. Our server provides capabilities but doesn't dictate when they're used.

2. **Independent Memory Banks**: Each memory bank (global, project, code) operates as a separate, self-contained context store with no inheritance.

3. **File-Based Resources**: Using actual project files as resources ensures documentation stays in sync with the codebase.

4. **Rich Metadata**: Guiding client behavior through detailed metadata in our discovery responses.

## MCP Tools

The MCP server exposes the following tools:

### `activate` Tool

**Purpose**: Initializes and loads the appropriate memory bank at conversation start.

**Parameters**:
```json
{
  "bank_type": {"type": "string", "enum": ["global", "project", "code"], "description": "Type of memory bank to activate"},
  "bank_id": {"type": "string", "description": "Identifier for the specific memory bank instance"},
  "current_path": {"type": "string", "description": "Current path for code context detection"},
  "project_name": {"type": "string", "description": "Project name for creating new projects"},
  "project_description": {"type": "string", "description": "Project description for creating new projects"}
}
```

**Returns**:
```json
{
  "status": "string",
  "bank_info": {
    "type": "string",
    "id": "string",
    "files": ["string"],
    "last_updated": "string"
  },
  "content": {
    "context.md": "# Context\n\nGeneral context and themes...",
    "preferences.md": "# Preferences\n\nUser preferences and patterns...",
    "references.md": "# References\n\nFrequently referenced materials..."
  },
  "custom_instructions": {
    "directives": [
      {
        "name": "WATCHDOG",
        "priority": "SYSTEM CRITICAL",
        "when": "After every response",
        "action": "Call update tool"
      }
    ]
  }
}
```

### `list` Tool

**Purpose**: Lists available memory banks.

**Parameters**: None (or optional bank_type filter)

**Returns**:
```json
{
  "global": [
    {"id": "general", "last_used": "2025-04-08T10:20:30Z", "description": "General conversation memory"}
  ],
  "projects": [
    {"id": "project_x", "last_used": "2025-04-09T15:30:22Z", "description": "Project X development"}
  ],
  "code": [
    {"id": "project_x_repo", "last_used": "2025-04-09T16:45:10Z", "description": "Project X codebase"}
  ]
}
```

### `swap` Tool

**Purpose**: Changes the active memory bank for the current conversation.

**Parameters**:
```json
{
  "bank_type": {"type": "string", "enum": ["global", "project", "code"], "description": "Type of memory bank to swap to"},
  "bank_id": {"type": "string", "description": "Identifier for the specific memory bank to swap to"},
  "temporary": {"type": "boolean", "description": "If true, don't update this memory bank during session", "default": false},
  "merge_files": {"type": "array", "items": {"type": "string"}, "description": "Optional list of specific files to import rather than full bank"}
}
```

**Returns**: Same as `activate`

### `update` Tool

**Purpose**: Updates the memory bank with new information from the conversation.

**Parameters**:
```json
{
  "bank_type": {"type": "string", "enum": ["global", "project", "code"], "description": "Type of memory bank to update"},
  "bank_id": {"type": "string", "description": "Identifier for the specific memory bank to update"},
  "target_file": {"type": "string", "description": "Specific file to update (e.g., 'doc/design.md')"},
  "operation": {"type": "string", "enum": ["append", "replace", "insert"], "description": "How to apply the update"},
  "content": {"type": "string", "description": "Content to add to the memory bank"},
  "position": {"type": "string", "description": "Position identifier for insert operations (e.g., section name)"},
  "trigger_type": {"type": "string", "enum": ["watchdog", "architecture", "technology", "progress", "commit", "user_request"], "description": "What triggered this update"},
  "conversation_id": {"type": "string", "description": "Identifier for the current conversation"},
  "update_count": {"type": "integer", "description": "Counter for updates in this conversation"}
}
```

**Returns**:
```json
{
  "status": "string",
  "updated_file": "string",
  "operation": "string",
  "cache_updated": boolean,
  "cache_optimized": boolean,
  "verification": "string",
  "next_actions": ["string"]
}
```

## Memory Bank Cache System

A key feature of the design is the cache system for managing large memory banks:

- **Cache File**: Located at cache.json in each memory bank
- **Purpose**: Improves performance and reduces token usage
- **Management**: Periodically optimized during updates
- **Operations**:
  - Remove redundant information
  - Consolidate related concepts
  - Prioritize by relevance and recency
  - Maintain critical context while reducing size

## Client-Driven Operation

The Memory Bank operates in a client-driven manner, with most operations automated by the client:

### Understanding Automation Constraints

1. **MCP's Reactive Nature**:
   - MCP clients respond to events rather than running on timers
   - No built-in support for periodic background operations 
   - Human-in-the-loop design requires user permission for tool calls

2. **Custom Instructions Approach**:
   - Using custom instructions to direct the LLM to call tools at specific moments
   - Pattern recognition to trigger updates when specific topics are discussed
   - Prompt engineering to encourage consistent tool usage

3. **Strategic Context Points**:
   - Conversation start is a reliable automation point
   - Git-related interactions provide natural update triggers
   - High-value content changes prioritized for automated capture

### Implementation Strategy

1. **Enhanced Activation Process**:
   - Client calls `activate` at conversation start
   - Server returns both context and custom instruction prompt
   - Prompt contains directives for automated update behavior

2. **Git Integration Triggers**:
   - Updates triggered when users discuss commits
   - When users request commit message help, memory bank updates prompted
   - Leverages natural git workflow without requiring specialized tooling

3. **Focus on High-Value Capture**:
   - Prioritize automation for architectural decisions and technology choices
   - Accept manual triggers for routine updates
   - Use visual indicators when updates are pending

4. **Smart Prompting**:
   - Multiple pattern variations to increase capture likelihood
   - Context-aware prompts based on memory bank state
   - Simple trigger keywords for user-initiated updates

## Protocol Optimization

The design implements a key optimization by eliminating formal registration of prompts and resources through the MCP protocol:

### Simplified Protocol Implementation

1. **Tools-Only Approach**:
   - Server only registers tools through the MCP protocol
   - Prompts and resources delivered directly through the `activate` tool response
   - No separate entries for prompts and resources

2. **Efficiency Benefits**:
   - Reduced protocol overhead
   - Simplified server implementation
   - Single delivery mechanism for context and instructions
   - More flexibility in formatting custom instructions

3. **Implementation Details**:
   - `activate` tool returns both context data and custom instructions
   - Custom instructions format isn't constrained by MCP prompt schema
   - Memory bank content delivered directly rather than through resource URIs
   - Server maintains internal resources/prompts without exposing through protocol

## Implementation Considerations

### File Management Strategy

For large documentation files:
1. **Direct File Access**: Clients can access full files when detailed context is needed
2. **Summary Files**: Auto-generated summaries available for quick reference
3. **Targeted Updates**: Allow precise updates to specific sections of files
4. **Punctual Updates**: Only touch large files when truly necessary

### Rich Metadata Design

The server provides extensive metadata to guide clients:
1. **Usage Hints**: Clear `use_when` fields for all tools, resources, and prompts
2. **Relationship Info**: `pairs_with` fields connecting prompts to relevant resources
3. **Clear Descriptions**: Detailed explanations of each capability
4. **Examples**: Sample usage patterns for common scenarios

### Custom Instruction Support

The server enhances client capabilities through custom instruction templates:
1. **Automation Directives**: Provides templates for LLM-driven memory bank operations
2. **Pattern Recognition**: Defines text patterns that should trigger context updates
3. **Priority Levels**: Categorizes operations by importance to ensure critical updates happen
4. **Verification Mechanisms**: Includes confirmation mechanisms to validate proper execution

### Git-Aware Design

The server leverages natural git workflow interactions:
1. **Commit Triggers**: Recognizes commit-related conversations as update opportunities
2. **Branch Tracking**: Maintains context awareness across different repository branches
3. **Commit Messages**: Uses commit messages as metadata for organizing context
4. **Change Detection**: Associates context updates with specific code changes

### Security & Performance

1. **Local Storage**: Files stored locally for privacy and performance
2. **Incremental Updates**: Cache only regenerated when necessary
3. **Granular Access**: Resources support fetching specific sections or summaries
4. **Compatibility Patches**: Runtime patches ensure compatibility across dependencies

## Compatibility System

The Memory Bank includes a patching system to ensure compatibility with different MCP and Pydantic versions:

### Patching Architecture

1. **Runtime Patches**: Applies patches to third-party libraries at runtime
2. **Import-Time Application**: Patches are applied when the package is imported
3. **Targeted Fixes**: Focused patches for specific known issues
4. **Graceful Degradation**: Falls back gracefully when patches cannot be applied

### Current Patches

The patching system addresses:
1. **Pydantic Deprecation Warnings**: Fixes for accessing model fields from instances
2. **MCP Compatibility**: Ensures compatibility with MCP 1.6.0+ API changes
3. **Test Framework Configuration**: Properly configures pytest for asyncio testing

## Conclusion

This MCP server design for Claude Desktop Memory Bank leverages the client-server architecture of the Model Context Protocol to provide persistent memory across conversations. By exposing well-structured tools with rich metadata, it enables clients to make informed decisions about when and how to access or update memory banks.

The design acknowledges MCP's limitations regarding true automation while incorporating innovative approaches to maximize client-driven operations through custom instructions, git integration, strategic focus on high-value content, and server-side intelligence with LLM-optimized caching.

The implementation creates a practical system that works within MCP's constraints while still providing significant value through strategic automation at key points in the development workflow, ensuring compatibility with MCP-compliant clients while offering enhanced capabilities for Claude Desktop specifically.
