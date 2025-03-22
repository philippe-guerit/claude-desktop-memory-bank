# Claude Desktop Memory Bank

A Model Context Protocol (MCP) server for Claude Desktop that maintains context across sessions.

## What is Claude Desktop Memory Bank?

Claude Desktop Memory Bank is an MCP server that helps Claude Desktop maintain context and memory across sessions. It works by storing and organizing context in a structured format that Claude can access when needed.

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

### Memory Bank Types

- **Global Memory Bank**: For general context across all conversations
- **Project Memory Banks**: Context linked to specific Claude Desktop projects
- **Repository Memory Banks**: Context stored directly within Git repositories

### MCP Resources

- Project brief and context files
- Technical documentation
- Progress tracking
- Active context updates

### MCP Tools

- Memory bank selection and management
- Context search and updates
- Repository detection and integration
- Project creation and management

## Usage

For detailed usage instructions, see the [Usage Guide](doc/usage-guide.md).

## Development

For information on the architecture and implementation, see:
- [MCP Design Documentation](doc/mcp-design.md)
- [Implementation Guide](doc/implementation-guide.md)

## MCP API

This server implements the Model Context Protocol (MCP) to provide a standardized way for Claude to access and maintain context across sessions. The MCP specification defines a standard for resources, tools, and prompts that can be used by any MCP-compatible client.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
