# Claude Desktop Memory Bank MCP Server Design

## Original Requirements

- **No Plan and Act Mode**: Unlike Cline Memory Bank, Claude Desktop will not use the plan/act mode paradigm
- **Four Main Tools**: Activate, List, Swap, and Update
- **Memory Bank Types**: Three distinct types:
  - Global: For conversations not in a project
  - Project: For conversations part of a project
  - Code: For conversations in a project that refer/manipulate source code in a repository
- **Client-Driven Operation**: Most memory bank operations should be automated by the client without explicit user requests
- **Memory Management**: System will manage memory bank size and content relevance including a cache for future optimization by an LLM

## MCP Architecture Understanding

Based on Model Context Protocol (MCP) standards, our design recognizes the following:

1. **Client-Server Roles**: The MCP client (within Claude Desktop) controls tool invocation, not the server or LLM. Our server provides capabilities but doesn't dictate when they're used.

2. **Resource Discovery Flow**: When clients connect, they call `mcp.discover` to receive a JSON structure listing our tools, resources, and prompts.

3. **Independent Memory Banks**: Each memory bank (global, project, code) operates as a separate, self-contained context store with no inheritance.

4. **File-Based Resources**: Using actual project files (readme.md, doc/architecture.md) as resources ensures documentation stays in sync with the codebase.

5. **Rich Metadata**: Guiding client behavior through detailed metadata in our `mcp.discover` responses.

## Memory Bank Structure

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

## Client-Driven Operation with Automation Limitations

Our design acknowledges that MCP has inherent limitations regarding automated operations since the protocol works in a primarily reactive manner. The following approach represents our strategy for maximizing client-driven operations within these constraints:

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

## MCP Server Implementation

### Tools Exposed Through MCP

Our MCP server exposes the following tools, designed with clear parameters and purposes:

#### `activate` Tool

**Purpose**: Initializes and loads the appropriate memory bank at conversation start.

**Parameters**:
```json
{
  "bank_type": {"type": "string", "enum": ["global", "project", "code"], "description": "Type of memory bank to activate"},
  "bank_id": {"type": "string", "description": "Identifier for the specific memory bank instance"}
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
}
```

#### `list` Tool

**Purpose**: Lists available memory banks.

**Parameters**: None (or optional filtering parameters)

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

#### `swap` Tool

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

#### `update` Tool

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

## Protocol Optimization

Our design implements a key optimization by eliminating formal registration of prompts and resources through the MCP protocol:

### Simplified Protocol Implementation

1. **Tools-Only Approach**:
   - Server only registers tools through the MCP protocol (activate, list, swap, update)
   - Prompts and resources delivered directly through the `activate` tool response
   - No separate `mcp.discover` entries for prompts and resources

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

This optimization maintains the functionality while reducing complexity, especially appropriate for Claude Desktop which primarily interacts through tool calls rather than dedicated prompt/resource UI elements.

## MCP Server Discovery Response

Our server's `mcp.discover` response provides information about available tools only:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "server": {
      "name": "Claude Desktop Memory Bank",
      "version": "2.0.0",
      "description": "MCP server for managing conversation context across sessions"
    },
    "tools": [
      {
        "id": "activate",
        "description": "Activates and loads a memory bank for the current conversation",
        "use_when": "At the beginning of a conversation to establish context",
        "parameters": {
          "type": "object",
          "properties": {
            "bank_type": {
              "type": "string",
              "enum": ["global", "project", "code"],
              "description": "Type of memory bank to activate"
            },
            "bank_id": {
              "type": "string",
              "description": "Identifier for the specific memory bank instance"
            }
          },
          "required": ["bank_type", "bank_id"]
        }
      },
      {
        "id": "list",
        "description": "Lists all available memory banks by type",
        "use_when": "User wants to see available memory banks or choose which to use",
        "parameters": {
          "type": "object",
          "properties": {}
        }
      },
      {
        "id": "swap",
        "description": "Changes the current conversation to use a different memory bank",
        "use_when": "Conversation shifts focus to a different project or context",
        "parameters": {
          "type": "object",
          "properties": {
            "bank_type": {
              "type": "string",
              "enum": ["global", "project", "code"],
              "description": "Type of memory bank to swap to"
            },
            "bank_id": {
              "type": "string",
              "description": "Identifier for the specific memory bank to swap to"
            },
            "temporary": {
              "type": "boolean",
              "description": "If true, don't update this memory bank during session",
              "default": false
            },
            "merge_files": {
              "type": "array",
              "items": {"type": "string"},
              "description": "Optional list of specific files to import rather than full bank"
            }
          },
          "required": ["bank_type", "bank_id"]
        }
      },
      {
        "id": "update",
        "description": "Updates the memory bank with new information from the conversation",
        "use_when": "Significant new information is discussed that should be persisted",
        "parameters": {
          "type": "object",
          "properties": {
            "bank_type": {
              "type": "string",
              "enum": ["global", "project", "code"],
              "description": "Type of memory bank to update"
            },
            "bank_id": {
              "type": "string",
              "description": "Identifier for the specific memory bank to update"
            },
            "target_file": {
              "type": "string",
              "description": "Specific file to update (e.g., 'doc/design.md')"
            },
            "operation": {
              "type": "string",
              "enum": ["append", "replace", "insert"],
              "description": "How to apply the update"
            },
            "content": {
              "type": "string",
              "description": "Content to add to the memory bank"
            },
            "position": {
              "type": "string",
              "description": "Position identifier for insert operations (e.g., section name)"
            }
          },
          "required": ["bank_type", "bank_id", "target_file", "operation", "content"]
        }
      }
    ]
    // No 'resources' or 'prompts' section - all content delivered through activate tool
  }
}
```

## Memory Bank Cache System with LLM Optimization

A key feature of our design is the cache system that provides server-side intelligence for managing large memory banks:

1. **Inference-Based Updates**:
   - Server analyzes partial updates to infer what needs to be updated elsewhere
   - Reduces number of explicit tool calls needed from the client
   - Makes each client update more efficient and impactful

2. **Smart Content Integration**:
   - When updates affect multiple contexts, server handles relationships
   - Cache maintains connections between related pieces of information
   - LLM helps determine how new information impacts existing context

3. **Cache Management**:
   - `update` tool updates cache.json when changes occur
   - LLM periodically optimizes cache based on accumulated changes
   - Supports both full files and intelligent summaries of large content

## Implementation Considerations

### File Management Strategy

For large documentation files:
1. **Direct File Access**: Clients can access full files when detailed context is needed
2. **Summary Files**: Auto-generated summaries available for quick reference
3. **Targeted Updates**: Allow precise updates to specific sections of files
4. **Punctual Updates**: Only touch large files when truly necessary

### Rich Metadata Design

Our server provides extensive metadata to guide clients:
1. **Usage Hints**: Clear `use_when` fields for all tools, resources, and prompts
2. **Relationship Info**: `pairs_with` fields connecting prompts to relevant resources
3. **Clear Descriptions**: Detailed explanations of each capability
4. **Examples**: Sample usage patterns for common scenarios

### Custom Instruction Support

Our server enhances client capabilities through custom instruction templates:
1. **Automation Directives**: Provides templates for LLM-driven memory bank operations
2. **Pattern Recognition**: Defines text patterns that should trigger context updates
3. **Priority Levels**: Categorizes operations by importance to ensure critical updates happen
4. **Verification Mechanisms**: Includes confirmation mechanisms to validate proper execution

### Git-Aware Design

Our server leverages natural git workflow interactions:
1. **Commit Triggers**: Recognizes commit-related conversations as update opportunities
2. **Branch Tracking**: Maintains context awareness across different repository branches
3. **Commit Messages**: Uses commit messages as metadata for organizing context
4. **Change Detection**: Associates context updates with specific code changes

### Security & Performance

1. **Local Storage**: Files stored locally for privacy and performance
2. **Incremental Updates**: Cache only regenerated when necessary
3. **Granular Access**: Resources support fetching specific sections or summaries

## Differentiation from Cline Memory Bank

Unlike Cline Memory Bank, our MCP server design:
1. **Eliminates Modes**: No plan/act mode switching - client-driven operation
2. **Standardizes Access**: Uses MCP protocol for universal client compatibility
3. **Exposes Real Files**: Uses actual project files rather than special memory files
4. **Provides Guidance**: Rich metadata guides clients on proper usage
5. **Optimizes Large Content**: Cache system manages memory bank size and relevance

## Conclusion

This MCP server design for Claude Desktop Memory Bank leverages the client-server architecture of the Model Context Protocol to provide persistent memory across conversations. By exposing well-structured tools, resources, and prompts with rich metadata, it enables clients to make informed decisions about when and how to access or update memory banks.

While acknowledging MCP's limitations regarding true automation, our design incorporates innovative approaches to maximize client-driven operations:

1. **Custom Instructions**: Using prompt engineering to guide LLM behavior
2. **Git Integration**: Leveraging natural development workflows as update triggers  
3. **Strategic Focus**: Prioritizing high-value content for automated capture
4. **Server Intelligence**: Using LLM-optimized caching to reduce client burden

These strategies create a practical system that works within MCP's constraints while still providing significant value through strategic automation at key points in the development workflow. The design ensures compatibility with MCP-compliant clients while offering enhanced capabilities for Claude Desktop specifically.