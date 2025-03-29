# Claude Desktop Memory Bank

A Model Context Protocol (MCP) server that provides autonomous memory persistence for Claude Desktop.

## What is Claude Desktop Memory Bank?

Claude Desktop Memory Bank is an MCP server that enables Claude to automatically maintain context and memory across sessions. It works as an auxiliary memory system that stores and organizes important information without requiring manual management by users.

The system supports three types of memory banks:
1. **Global Memory Bank**: For general conversations not tied to specific projects
2. **Project Memory Banks**: Linked to Claude Desktop projects
3. **Repository Memory Banks**: Located inside Git repositories for code-related work

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
         "args": ["-m", "memory_bank_server"],
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
- **Repository Memory Banks**: Context stored directly within Git repositories with branch detection

### Key Benefits

- **Reduced Cognitive Load**: Users don't need to manually manage what Claude remembers
- **Conversation Continuity**: Previous context flows naturally into new conversations
- **Development Support**: Code and project knowledge persists across sessions
- **Team Collaboration**: Repository memory banks can be shared via version control
- **Enhanced Project Management**: Keep project briefs, progress tracking, and technical decisions organized

## MCP Tools

The Memory Bank system implements the Model Context Protocol (MCP) v1.4.0+ with the following tools:

- **context_activate**: Activate the memory bank with context-aware detection
- **context_select**: Select which memory bank to use for the conversation
- **context_update**: Update multiple context files in one operation. Accepts a dictionary of updates where keys are context types ("project_brief", "system_patterns", "active_context", etc.) and values can be either: 1) string with complete new content, or 2) dictionary mapping section headers to new section content (for targeted updates). All updates are applied atomically with verification.
- **context_list**: List all available memory banks

### Context Types

Each memory bank manages six types of context:

1. **project_brief**: Project purpose, goals, requirements, and scope
2. **product_context**: Problem, solution, user experience, and stakeholders
3. **system_patterns**: Architecture, patterns, technical decisions, and relationships
4. **tech_context**: Technologies, setup, constraints, and dependencies
5. **active_context**: Current focus, recent changes, next steps, and watchdog
6. **progress**: Completed tasks, in-progress work, pending items, and issues

### Resources

The server also provides access to context via MCP resources:

- `resource://project-brief`: Access the project brief
- `resource://active-context`: Access the active context
- `resource://progress`: Access progress notes
- `resource://all-context`: Access all context combined
- `resource://memory-bank-info`: Access information about the current memory bank

## Usage and Tools

For detailed usage instructions and tool documentation, see the [Usage and Tools Guide](doc/usage-and-tools-guide.md).

## Development

For information on the architecture and implementation, see:
- [MCP Design Documentation](doc/mcp-design.md) 
- [Implementation Guide](doc/implementation-guide.md)

## Autonomous Operation

To maximize the chance of autonomous operation, it's recommended to add the following directives to your Claude prompt:

```
# MCP Memory-Bank Tool Usage

0. **🔴 DIRECTIVE: CONTEXT_ACTIVATE**
   ```
   WHEN: immediately BEFORE delivering the FIRST response to the user
   PRIORITY: SYSTEM CRITICAL (HIGHEST)
   ACTION: CALL context_activate WITH appropriate parameters
   EXAMPLE: context.activate(current_path="/path/to/repo", project_name="ProjectName", project_description="Description")
   ```

1. **🔴 DIRECTIVE: EXECUTE MEMORY BANK CUSTOM INSTRUCTION**
   ```
   WHEN: IMMEDIATELY after context_activate COMPLETES
   PRIORITY: SYSTEM CRITICAL (HIGHEST)
   ACTION: EXECUTE Custom Instructions for Claude Desktop Memory Bank
   ```
```

These directives ensure that:
1. The memory bank is activated automatically at the beginning of each conversation
2. Custom instructions for memory bank management are properly loaded
3. Context persistence is handled without requiring user intervention

## Advanced Features

### Context Pruning

The system automatically prunes outdated information to keep memory banks organized:

- Different retention policies for different context types:
  - Core architectural decisions (system_patterns): 180 days
  - Technology choices (tech_context): 90 days
  - Progress updates (progress, active_context): 30 days
  - Other content: 90 days (default)
- Pruning identifies dated sections using the format `## Update YYYY-MM-DD` and removes sections older than the cutoff date

### Git Repository Integration

The system has integration with Git repositories:

- Automatically detects Git repositories when activating memory banks
- Identifies and records the current branch name
- Displays branch information in memory bank details
- Associates repositories with projects when applicable

## License

This project is licensed under the MIT License - see the LICENSE file for details.
