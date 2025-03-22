# Claude Desktop Memory Bank - MCP Server Design

## Introduction

The Claude Desktop Memory Bank is a specialized Model Context Protocol (MCP) server designed to help Claude Desktop maintain context and memory across sessions. This document outlines the architecture and implementation approach for this MCP server, drawing inspiration from the Cline Memory Bank concept while following the standardized MCP specification.

## What is MCP?

The Model Context Protocol (MCP) is an open standard developed by Anthropic that standardizes how applications provide context to LLMs. It functions like a "USB-C port for AI applications," providing a standardized way to connect AI models with various data sources and tools.

MCP addresses the challenge of AI systems being isolated from data sources by providing a universal, open standard for connecting AI systems with data sources, replacing fragmented integrations with a single protocol.

## System Architecture Overview

The Memory Bank MCP server follows the standard MCP architecture pattern, with support for multiple memory bank sources:

```mermaid
flowchart TD
    Claude[Claude Desktop] <--> CMCP[Claude Memory Bank MCP Server]
    CMCP <--> MemSelector[Memory Bank Selector]
    
    MemSelector --> Global[Global Memory Bank]
    MemSelector --> Project[Project Memory Banks]
    MemSelector --> Repo[Repository Memory Banks]
    
    Global <--> GlobalFS[File System]
    Project <--> ProjectFS[File System]
    Repo <--> RepoFS[.claude-memory in Git Repos]
```

## Memory Bank Types

The system supports three types of memory banks:

1. **Global Memory Bank**: Used for general conversations not associated with any specific project
2. **Project Memory Banks**: Linked to Claude Desktop projects for project-specific conversations
3. **Repository Memory Banks**: Located within Git repositories for code-related conversations

## Core Components

The Claude Desktop Memory Bank MCP server implements these core MCP capabilities:

### 1. Resources

Resources in MCP are file-like data that can be read by clients. Our Memory Bank server exposes:

- **Project Brief Resource**: Provides high-level information about the current project
- **Technical Context Resource**: Offers technical context about the project
- **Active Context Resource**: Delivers the current working context
- **Progress Resource**: Shows what's been done and what's still to be completed

```mermaid
flowchart LR
    Claude[Claude Desktop] --> RH[Resource Handler]
    RH --> MBS[Memory Bank Selector]
    MBS --> PB[Project Brief]
    MBS --> TC[Technical Context]
    MBS --> AC[Active Context]
    MBS --> P[Progress]
```

### 2. Tools

MCP Tools are functions that can be called by the LLM (with user approval). Our server provides:

- **Memory Bank Management Tools**: Select, initialize, and list available memory banks
- **Update Context Tool**: Allows Claude to update the memory bank with new information
- **Search Context Tool**: Enables searching through past context
- **Project Management Tools**: Create and manage project-specific memory banks
- **Repository Detection Tool**: Detect and initialize repository memory banks

```mermaid
flowchart LR
    Claude[Claude Desktop] --> TH[Tool Handler]
    TH --> MBM[Memory Bank Management]
    TH --> Update[Update Context]
    TH --> Search[Search Context]
    TH --> Project[Project Management]
    TH --> Repo[Repository Tools]
```

### 3. Prompts

MCP Prompts are pre-written templates that help users interact with the server:

- **Project Brief Template**: Guide for creating an initial project brief
- **Context Summary Template**: Format for summarizing current context
- **Progress Update Template**: Structure for updating progress

## Data Structure

The memory bank data is organized in a structured way using markdown files. This structure is replicated across all memory bank types:

```mermaid
flowchart TD
    PB[projectbrief.md] --> PC[productContext.md]
    PB --> SP[systemPatterns.md]
    PB --> TC[techContext.md]
    
    PC --> AC[activeContext.md]
    SP --> AC
    TC --> AC
    
    AC --> P[progress.md]
```

## Storage Structure

The file system structure accommodates multiple memory bank types:

```
memory-bank/
├── global/                 # Global memory bank
│   ├── projectbrief.md
│   ├── productContext.md
│   └── ...
├── projects/               # Project-specific memory banks
│   ├── project1/
│   │   ├── projectbrief.md
│   │   └── ...
│   └── project2/
│       ├── projectbrief.md
│       └── ...
└── repositories/           # Symlinks or records of git repositories
    ├── repo1 -> /path/to/repo1/.claude-memory
    └── repo2 -> /path/to/repo2/.claude-memory
```

For repositories, the actual memory bank files are stored within the repository itself:

```
repository/
├── .claude-memory/         # Repository memory bank
│   ├── projectbrief.md
│   ├── productContext.md
│   └── ...
├── src/
└── ...
```

## Memory Bank Selection

The memory bank selection follows a systematic approach:

```mermaid
flowchart TD
    Start[Start Conversation] --> Search[Search for repo path in Claude project docs]
    Search --> Found{Found repo path?}
    Found -->|Yes| UseRepo[Use repo memory bank]
    Found -->|No| Suggest[Claude suggests global memory bank]
    Suggest --> Ask{User approves?}
    Ask -->|Yes| UseGlobal[Use global memory bank]
    Ask -->|No| Instruct[Claude instructs to add repo path to project doc]
    Instruct --> Restart[User restarts memory bank]
```

When Claude needs to select a memory bank, it:
1. Checks if the conversation is associated with a Claude Desktop Project
2. If yes, checks if the project has a configured repository path
3. If a repository path exists, uses that repository's memory bank
4. If no repository path exists, asks the user whether to use the global memory bank
5. Provides instructions on how to associate a repository if desired

## Implementation Approach

We'll implement the Claude Desktop Memory Bank using the official MCP Python SDK. The implementation will follow these steps:

1. **Set up the MCP server framework**
2. **Implement memory bank selection logic**
3. **Define resources to expose memory bank files**
4. **Implement tools for context manipulation and memory bank selection**
5. **Add prompts for standardized interactions**

## Server Implementation Details

The server will be implemented using Python and the official MCP Python SDK:

```mermaid
classDiagram
    class MemoryBankServer {
        +initialize_server()
        +configure_resources()
        +configure_tools()
        +configure_prompts()
        +run()
    }
    
    class MemoryBankSelector {
        +get_memory_bank(context)
        +detect_repository(path)
        +get_project_repository(project_name)
        +initialize_memory_bank(path)
    }
    
    class ContextManager {
        +get_context(memory_bank, context_type)
        +update_context(memory_bank, context_type, content)
        +search_context(memory_bank, query)
    }
    
    class StorageManager {
        +read_file(file_path)
        +write_file(file_path, content)
        +list_files()
        +create_memory_bank(path)
    }
    
    MemoryBankServer --> MemoryBankSelector
    MemoryBankServer --> ContextManager
    MemoryBankSelector --> StorageManager
    ContextManager --> StorageManager
```

## Core Workflows

### Memory Bank Selection Workflow

```mermaid
sequenceDiagram
    participant User
    participant CD as Claude Desktop
    participant MCP as Memory Bank MCP Server
    participant MBS as Memory Bank Selector
    
    User->>CD: Start conversation
    CD->>MCP: Call select_memory_bank tool
    MCP->>MBS: Check for repository in Claude project
    MBS-->>MCP: Return memory bank selection
    MCP-->>CD: Request user approval
    CD-->>User: Explain memory bank selection
    User->>CD: Approve selection
    CD->>MCP: Confirm memory bank selection
    MCP-->>CD: Memory bank selected
```

### Repository Detection Workflow

```mermaid
sequenceDiagram
    participant User
    participant CD as Claude Desktop
    participant MCP as Memory Bank MCP Server
    participant MBS as Memory Bank Selector
    participant Git as Git Repository
    
    User->>CD: Mention working in repository
    CD->>MCP: Call detect_repository tool
    MCP->>MBS: Check path for Git repository
    MBS->>Git: Check for .git directory
    Git-->>MBS: Confirm repository exists
    MBS-->>MCP: Repository detected
    MCP-->>CD: Repository information
    CD-->>User: Ask to use repository memory bank
    User->>CD: Approve
    CD->>MCP: Call initialize_memory_bank tool
    MCP->>Git: Create .claude-memory directory
    Git-->>MCP: Memory bank initialized
    MCP-->>CD: Confirmation
    CD-->>User: Memory bank ready
```

### Context Update Workflow

```mermaid
sequenceDiagram
    participant User
    participant CD as Claude Desktop
    participant MCP as Memory Bank MCP Server
    participant MB as Memory Bank
    
    User->>CD: Update project context
    CD->>MCP: Call update_context tool
    MCP->>MB: Process update
    MB-->>MCP: Confirm update
    MCP-->>CD: Report successful update
    CD-->>User: Confirm context is updated
```

## Integration with Claude Desktop

To integrate with Claude Desktop, the configuration will include options for global and repository memory banks:

```json
{
  "mcpServers": {
    "memory-bank": {
      "command": "python",
      "args": ["-m", "memory_bank_server"],
      "env": {
        "GLOBAL_MEMORY_PATH": "/path/to/global/memory",
        "ENABLE_REPO_DETECTION": "true"
      }
    }
  }
}
```

## Repository Integration

For repository integration, we'll use Git to detect repositories and place memory banks directly within them:

1. **Repository Detection**: Check for `.git` directories to identify repositories
2. **Memory Bank Location**: Store memory banks in `.claude-memory` at the repository root
3. **Path Resolution**: Support both absolute and relative paths to repositories
4. **Project Association**: Allow linking Claude Desktop Projects to specific repositories

## Future Enhancements

After the initial implementation, we could consider these enhancements:

1. **Advanced Context Selection**: Implement more sophisticated algorithms to select the most relevant context
2. **Embedding-Based Search**: Use embeddings to improve context searching
3. **Context Versioning**: Track changes to context over time
4. **Git Integration**: Store memory bank changes as Git commits
5. **Collaborative Memory Banks**: Support for shared memory banks in team environments
6. **Remote Hosting**: Support for remote hosting when MCP supports it

## Conclusion

The Claude Desktop Memory Bank MCP server provides a standardized way for Claude to maintain context across sessions using the Model Context Protocol. The multi-memory bank approach (global, project, and repository) offers flexibility and better context management for different conversation scenarios.
