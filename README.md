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

### Memory Bank Types

- **Global Memory Bank**: For general context across all conversations
- **Project Memory Banks**: Context linked to specific Claude Desktop projects
- **Repository Memory Banks**: Context stored directly within Git repositories

### Key Benefits

- **Reduced Cognitive Load**: Users don't need to manage what Claude remembers
- **Conversation Continuity**: Previous context flows naturally into new conversations
- **Development Support**: Code and project knowledge persists across sessions
- **Team Collaboration**: Repository memory banks can be shared via version control

## Usage and Tools

For detailed usage instructions and tool documentation, see the [Usage and Tools Guide](doc/usage-and-tools-guide.md).

## Development

For information on the architecture and implementation, see:
- [MCP Design Documentation](doc/mcp-design.md) 
- [Implementation Guide](doc/implementation-guide.md)

## MCP API

This server implements the Model Context Protocol (MCP) to provide a standardized way for Claude to access and maintain context across sessions. The MCP specification defines a standard for resources, tools, and prompts that can be used by any MCP-compatible client.

### Key MCP Tools

- **memory-bank-start**: Initialize memory banks and load custom prompts with a single tool call
- **select-memory-bank**: Choose which memory bank to use for the conversation
- **update-context**: Update context files in the current memory bank
- **search-context**: Find relevant information in context files

For complete documentation on all available tools, see the [Usage and Tools Guide](doc/usage-and-tools-guide.md).

## License

This project is licensed under the MIT License - see the LICENSE file for details.
