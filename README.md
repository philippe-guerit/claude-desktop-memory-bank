# Claude Desktop Memory Bank

A Model Context Protocol (MCP) server that provides autonomous memory persistence for Claude Desktop.

## What is Claude Desktop Memory Bank?

Claude Desktop Memory Bank is an MCP server that enables Claude to automatically maintain context and memory across sessions. It works as an auxiliary memory system that stores and organizes important information without requiring manual management by users.

The system supports three types of memory banks:
1. **Global Memory Bank**: For general conversations not tied to specific projects
2. **Project Memory Banks**: Linked to Claude Desktop projects
3. **Code Memory Banks**: Located inside Git repositories for code-related work

## Installation

### Prerequisites

- Claude Desktop app installed
- Python 3.8 or newer
- Git (for repository memory banks)

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/claude-desktop-memory-bank.git
   cd claude-desktop-memory-bank
   ```

2. **Install the memory bank server**:
   ```bash
   pip install -e .
   ```

3. **Configure Claude Desktop**:
   
   Locate the Claude Desktop configuration file and add the memory bank server configuration:
   ```json
   {
     "mcpServers": {
       "memory-bank": {
         "command": "python",
         "args": ["-m", "memory_bank"],
         "env": {
           "MEMORY_BANK_ROOT": "/path/to/your/storage/directory",
           "ENABLE_REPO_DETECTION": "true"
         }
       }
     }
   }
   ```

4. **Restart Claude Desktop**

## Features

### Autonomous Memory Management

- **Background Operation**: Claude manages memory banks without user interaction
- **Intelligent Context Persistence**: Automatically identifies and persists important information
- **Seamless Context Retrieval**: Leverages stored context in conversations without explicit commands
- **Automatic Context Pruning**: Keeps memory banks organized by removing outdated information
- **Section-based Updates**: Supports targeted updates to specific sections within context files

### Memory Bank Types

- **Global Memory Bank**: For general context across all conversations
- **Project Memory Banks**: Context linked to specific Claude Desktop projects
- **Code Memory Banks**: Context stored directly within Git repositories with branch detection

### Key Benefits

- **Reduced Cognitive Load**: Users don't need to manually manage what Claude remembers
- **Conversation Continuity**: Previous context flows naturally into new conversations
- **Development Support**: Code and project knowledge persists across sessions
- **Team Collaboration**: Repository memory banks can be shared via version control
- **Enhanced Project Management**: Keep project briefs, progress tracking, and technical decisions organized

## MCP Tools

The Memory Bank system implements the Model Context Protocol (MCP) v1.6.0+ with the following tools:

- **activate**: Activate the memory bank with context-aware detection
- **list**: List all available memory banks
- **swap**: Change the active memory bank for the current conversation
- **update**: Update memory bank content with new information

### Memory Bank Structure

Each memory bank type has a specific structure:

#### Global Memory Bank
```
~/.claude-desktop/memory/global/{bank_id}/
├── context.md                    # General context and themes
├── preferences.md                # User preferences and patterns
├── references.md                 # Frequently referenced materials
└── cache.json                    # Optimized representation for LLM use
```

#### Project Memory Bank
```
~/.claude-desktop/memory/projects/{bank_id}/
├── readme.md                     # Project overview
├── doc/                          # Documentation directory
│   ├── architecture.md           # Architecture decisions
│   ├── design.md                 # Design documentation
│   └── progress.md               # Current state and next steps
├── tasks.md                      # Active tasks and todos
└── cache.json                    # Optimized representation for LLM use
```

#### Code Memory Bank
```
~/.claude-desktop/memory/code/{bank_id}/
├── readme.md                     # Repository overview
├── doc/                          # Code documentation directory
│   ├── architecture.md           # Code architecture
│   ├── design.md                 # Design patterns
│   └── api.md                    # API documentation
├── structure.md                  # Code organization
├── snippets.md                   # Important code snippets
└── cache.json                    # Optimized representation for LLM use
```

## Autonomous Operation

To maximize the chance of autonomous operation, it's recommended to add the following directives to your Claude prompt:

```
# MCP Memory-Bank Tool Usage

0. **🔴 DIRECTIVE: CONTEXT_ACTIVATE**
   ```
   WHEN: immediately BEFORE delivering the FIRST response to the user
   PRIORITY: SYSTEM CRITICAL (HIGHEST)
   ACTION: CALL activate WITH appropriate parameters
   EXAMPLE: activate(bank_type="code", bank_id="project_x_repo", current_path="/path/to/repo")
   ```

1. **🔴 DIRECTIVE: EXECUTE MEMORY BANK CUSTOM INSTRUCTION**
   ```
   WHEN: IMMEDIATELY after activate COMPLETES
   PRIORITY: SYSTEM CRITICAL (HIGHEST)
   ACTION: EXECUTE Custom Instructions for Claude Desktop Memory Bank
   ```
```

These directives ensure that:
1. The memory bank is activated automatically at the beginning of each conversation
2. Custom instructions for memory bank management are properly loaded
3. Context persistence is handled without requiring user intervention

## Advanced Features

### Cache Optimization

The system automatically optimizes the memory bank cache for efficiency:

- Cache files contain summaries and metadata for each content file
- Intelligent processing reduces token usage when accessing full context
- Automatic optimization happens periodically during updates
- Maintains relationships between related pieces of information

### Git Repository Integration

The system integrates with Git repositories:

- Automatically detects Git repositories when activating memory banks
- Identifies and records the current branch name
- Associates context with specific branches
- Tracks relevant commit information

## Development

For information on the architecture and implementation, see:
- [Design Document](docs/design.md)
- [API Reference](docs/api-reference.md)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
