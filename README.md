# Claude Desktop Memory Bank

A Model Context Protocol (MCP) server that provides autonomous memory persistence for Claude Desktop.

**Version 2.0.0** - Updated April 2025

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

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # On Linux/macOS
   source .venv/bin/activate
   # On Windows
   .venv\Scripts\activate
   ```

3. **Install the memory bank server**:
   ```bash
   pip install -e .
   ```

4. **Configure Claude Desktop**:
   
   Locate the Claude Desktop configuration file and add the memory bank server configuration. You can use either the module directly or the wrapper script:

   **Option 1: Using the module directly**:
   ```json
   {
     "mcpServers": {
       "memory-bank": {
         "command": "python3",
         "args": ["-m", "memory_bank"],
         "cwd": "/path/to/claude-desktop-memory-bank"
       }
     }
   }
   ```

   **Option 2: Using the wrapper script**:
   ```json
   {
     "mcpServers": {
       "memory-bank": {
         "command": "python3",
         "args": ["run_server.py"],
         "cwd": "/path/to/claude-desktop-memory-bank"
       }
     }
   }
   ```

   **Option 3: Using a custom storage location**:
   ```json
   {
     "mcpServers": {
       "memory-bank": {
         "command": "python3",
         "args": ["-m", "memory_bank"],
         "cwd": "/path/to/claude-desktop-memory-bank",
         "env": {
           "MEMORY_BANK_ROOT": "/custom/path/to/memory/storage"
         }
       }
     }
   }
   ```

   **Environment Variables**:
   - `MEMORY_BANK_ROOT` (Optional): Path to custom storage directory. If not specified, defaults to `~/.claude-desktop/memory/`

   Make sure to adjust the `cwd` path according to your setup.

5. **(Optional) Customize the wrapper script**:
   The repository already includes a `run_server.py` wrapper script that's ready to use. If you need to customize it, you can modify it to suit your needs. The existing wrapper looks like this:
   
   ```python
   #!/usr/bin/env python3
   """
   Wrapper script for the Claude Desktop Memory Bank MCP server.
   This exposes the server for use with the MCP Inspector tool.
   """

   import asyncio
   import logging
   import sys
   from pathlib import Path
   from memory_bank.server import MemoryBankServer

   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
       handlers=[logging.StreamHandler(sys.stdout)]
   )

   logger = logging.getLogger(__name__)

   async def main():
       logger.info("Starting run_server.py wrapper...")
       
       # Create and configure the server
       storage_root = Path.home() / ".claude-desktop" / "memory"
       
       # Override storage root from environment variable if set
       import os
       storage_root_env = os.environ.get("MEMORY_BANK_ROOT")
       if storage_root_env:
           storage_root = Path(storage_root_env)
       
       logger.info(f"Using storage root: {storage_root}")
       
       # Create server
       mcp_server = MemoryBankServer(storage_root=storage_root)
       
       # Start the server
       logger.info("Starting server...")
       await mcp_server.start()

   if __name__ == "__main__":
       asyncio.run(main())
   ```

6. **Make the wrapper executable** (if using the wrapper script):
   ```bash
   chmod +x run_server.py
   ```

7. **Restart Claude Desktop**

## Using the MCP Inspector

For development and testing, you can use the MCP Inspector to interact with the server:

```bash
# Install the MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Run the server with the inspector using the wrapper script
npx @modelcontextprotocol/inspector python3 run_server.py

# Or run using the module directly
npx @modelcontextprotocol/inspector python3 -m memory_bank
```

This will launch a web interface at http://127.0.0.1:6274 where you can test the MCP tools.

## Running the Server Directly

You can also run the server directly without the MCP Inspector:

```bash
# Using the wrapper script
python3 run_server.py

# Or using the module directly
python3 -m memory_bank
```

Both methods work identically and provide the same functionality.

## Features

### Autonomous Memory Management

- **Background Operation**: Claude manages memory banks without user interaction
- **Intelligent Context Persistence**: Automatically identifies and persists important information
- **Seamless Context Retrieval**: Leverages stored context in conversations without explicit commands
- **Automatic Context Pruning**: Keeps memory banks organized by removing outdated information
- **Section-based Updates**: Supports targeted updates to specific sections within context files

### Memory Bank Types

- **Global Memory Bank**: For general context across all conversations
- **Project Memory Banks**: Context linked to specific Claude Desktop projects, using a standardized template
- **Code Memory Banks**: Context stored directly within Git repositories with branch detection

### Standardized Project Template

All project memory banks use a standardized template optimized for various project types, consisting of:

- **Project Overview**: Basic project information in readme.md
- **Documentation Directory**: 
  - Goals and objectives tracking
  - Key decisions documentation
  - Progress updates
  - Important references
- **Notes Directory**:
  - Meeting summaries
  - Ideas and brainstorming results
  - Research findings

This standardized structure simplifies client integration and makes it easier to maintain project context across conversations.

### Key Benefits

- **Reduced Cognitive Load**: Users don't need to manually manage what Claude remembers
- **Conversation Continuity**: Previous context flows naturally into new conversations
- **Development Support**: Code and project knowledge persists across sessions
- **Team Collaboration**: Repository memory banks can be shared via version control
- **Enhanced Project Management**: Keep project briefs, progress tracking, and technical decisions organized

## MCP Tools

The Memory Bank system implements the Model Context Protocol (MCP) v1.6.0+ with the following tools:

- **activate**: Initializes and loads the appropriate memory bank at conversation start, with context-aware detection. Returns both context data and custom instructions.
- **list**: Lists all available memory banks of each type (global, project, code).
- **update**: Updates memory bank content with new information, supporting targeted file updates and different operation types.

### Memory Bank Structure

By default, all memory banks are stored in `~/.claude-desktop/memory/` (where `~` is your home directory). This location can be customized using the `MEMORY_BANK_ROOT` environment variable.

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
│   ├── objectives.md             # Goals and objectives
│   ├── decisions.md              # Key decisions (generic)
│   ├── progress.md               # Status updates
│   └── references.md             # Important references
├── notes/                        # Project-specific notes
│   ├── meeting_notes.md          # Meeting summaries
│   ├── ideas.md                  # Brainstorming and ideas
│   └── research.md               # Research findings
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
   EXAMPLE: activate(conversation_type="project", project_name="ProjectName", current_path="/path/to/repo")
   ```

1. **🔴 DIRECTIVE: EXECUTE MEMORY BANK CUSTOM INSTRUCTION**
   ```
   WHEN: IMMEDIATELY after activate COMPLETES
   PRIORITY: SYSTEM CRITICAL (HIGHEST)
   ACTION: EXECUTE Custom Instructions for Claude Desktop Memory Bank
   ```

2. **🔴 WATCHDOG DIRECTIVE: UPDATE AFTER EACH RESPONSE**
   ```
   WHEN: IMMEDIATELY after EVERY response delivery 
   PRIORITY: SYSTEM CRITICAL (HIGHEST)
   ACTION: CALL update WITH appropriate parameters when relevant changes detected
   ```
```

These directives ensure that:
1. The memory bank is activated automatically at the beginning of each conversation
2. Custom instructions for memory bank management are properly loaded
3. Context persistence is handled without requiring user intervention

## Advanced Features

### Protocol Optimization

The Memory Bank server implements a key optimization in the MCP protocol:

- **Tools-Only Approach**: Server only registers tools through the MCP protocol (activate, list, swap, update)
- **Prompt and Resource Delivery**: Prompts and resources delivered directly through the `activate` tool response
- **Simplified Implementation**: Reduced protocol overhead and flexible formatting of custom instructions
- **Single Delivery Mechanism**: Context data and custom instructions provided in a single response

### Cache Optimization

The system automatically optimizes the memory bank cache for efficiency:

- **Intelligent Cache Storage**: Cache files contain compressed/optimized version of the entire memory bank
- **Token Optimization**: Intelligent processing reduces token usage when accessing full context
- **Automatic Optimization**: Cache is periodically optimized during updates using LLM processing
- **Relationship Tracking**: Maintains connections between related pieces of information
- **Inference-Based Updates**: Server analyzes partial updates to infer what needs to be updated elsewhere
- **Smart Content Integration**: Server handles updates affecting multiple contexts automatically
- **Optimized Memory Management**: LLM helps determine how new information impacts existing context

### Git Repository Integration

The system automatically integrates with Git repositories:

- Automatically detects Git repositories when activating memory banks
- Identifies and records the current branch name
- Associates context with specific branches
- Tracks relevant commit information
- Creates code-specific memory banks customized for the repository

This feature provides context-aware assistance with codebases by automatically creating optimized memory banks for your repositories.

## Development

For information on the architecture and implementation, see:
- [Design Document](docs/design.md)
- [API Reference](docs/api-reference.md)
- [Project Status](docs/status.md)

### Testing

The project has a comprehensive test suite organized by component:

```
tests/
├── conftest.py               # Shared fixtures and test utilities
├── test_cache/               # Tests for cache optimization
├── test_storage/             # Tests for storage components
├── test_tools/               # Tests for MCP tool implementations
├── test_utils/               # Tests for utility functions
└── test_integration/         # Integration tests
```

#### Test Infrastructure

The Memory Bank server has a robust testing framework with these key features:

- **Mock Transport System**: A testing-specific transport layer that replaces stdin/stdout communication
- **Test Mode**: `MemoryBankServer` includes a test mode that bypasses stdio requirements
- **Direct Tool Access**: The `call_tool_test` method enables direct tool invocation in tests
- **Improved Isolation**: Tests no longer rely on actual stdio streams
- **Enhanced Error Handling**: Better error detection and reporting in the test environment

To run the tests:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=memory_bank

# Run specific test categories
pytest tests/test_storage/
pytest tests/test_tools/
```

The project uses GitHub Actions for continuous integration:
- Automated tests on multiple Python versions (3.8-3.12)
- Code coverage reporting
- Linting with flake8, black, and isort

## License

This project is licensed under the MIT License - see the LICENSE file for details.

~/code/claude-desktop-memory-bank$ npx @modelcontextprotocol/inspector python3 -m run_server

