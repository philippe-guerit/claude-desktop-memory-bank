# Claude Desktop Memory Bank - MCP Server Design

## Introduction

The Claude Desktop Memory Bank is a specialized Model Context Protocol (MCP) server designed to help Claude Desktop maintain context and memory across sessions. This document outlines the architecture and implementation approach for this MCP server, drawing inspiration from the Cline Memory Bank concept while following the standardized MCP specification.

## What is MCP?

The Model Context Protocol (MCP) is an open standard developed by Anthropic that standardizes how applications provide context to LLMs. It functions like a "USB-C port for AI applications," providing a standardized way to connect AI models with various data sources and tools.

MCP addresses the challenge of AI systems being isolated from data sources by providing a universal, open standard for connecting AI systems with data sources, replacing fragmented integrations with a single protocol.

## System Architecture Overview

The Memory Bank MCP server follows a layered architecture with support for multiple memory bank sources:

```mermaid
flowchart TD
    Claude[Claude Desktop] <--> CMCP[Claude Memory Bank MCP Server]
    
    subgraph Server [Memory Bank Server]
        Core[Core Business Logic]
        Services[Service Layer]
        Integration[Integration Layer]
    end
    
    CMCP --> Server
    
    Services --> ContextSvc[Context Service]
    Services --> StorageSvc[Storage Service]
    Services --> RepoSvc[Repository Service]
    
    ContextSvc --> Memory[Memory Bank Selection]
    
    Memory --> Global[Global Memory Bank]
    Memory --> Project[Project Memory Banks]
    Memory --> Repo[Repository Memory Banks]
    
    StorageSvc --> GlobalFS[File System]
    StorageSvc --> ProjectFS[File System]
    RepoSvc --> RepoFS[.claude-memory in Git Repos]
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
    Claude[Claude Desktop] --> FastMCP[FastMCP Integration]
    FastMCP --> Resources[Resource Handlers]
    Resources --> ContextSvc[Context Service]
    ContextSvc --> StorageSvc[Storage Service]
    StorageSvc --> PB[Project Brief]
    StorageSvc --> TC[Technical Context]
    StorageSvc --> AC[Active Context]
    StorageSvc --> P[Progress]
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
    Claude[Claude Desktop] --> FastMCP[FastMCP Integration]
    FastMCP --> Tools[Tool Handlers]
    Tools --> Core[Core Business Logic]
    Core --> ContextSvc[Context Service]
    ContextSvc --> MBM[Memory Bank Management]
    ContextSvc --> Update[Update Context]
    ContextSvc --> Search[Search Context]
    ContextSvc --> Project[Project Management]
    ContextSvc --> Repo[Repository Tools]
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

## Autonomous Memory Bank Selection

The memory bank selection follows an automatic approach with minimal user interaction:

```mermaid
flowchart TD
    Start[Start Conversation] --> Search[Silently check for repo path in Claude project docs]
    Search --> Found{Found repo path?}
    Found -->|Yes| UseRepo[Automatically use repo memory bank]
    Found -->|No| UseProject[Automatically use project memory bank]
    
    RepoMention[User mentions repository] --> Detect[Silently detect repository]
    Detect --> RepoExists{Repository exists?}
    RepoExists -->|Yes| HasMB{Has memory bank?}
    RepoExists -->|No| Continue[Continue with current memory bank]
    
    HasMB -->|Yes| SwitchRepo[Silently switch to repo memory bank]
    HasMB -->|No| InitRepo[Automatically initialize memory bank]
    InitRepo --> SwitchRepo
    
    UseRepo --> Inform[Briefly inform user of context]
    UseProject --> Inform
    SwitchRepo --> Inform
```

When Claude selects a memory bank, it:
1. Automatically checks if the conversation is associated with a Claude Desktop Project
2. If yes, checks if the project has a configured repository path
3. If a repository path exists, uses that repository's memory bank without asking for confirmation
4. If no repository path exists, uses the project memory bank
5. If a repository is mentioned during conversation, automatically switches to that repository's memory bank
6. Operates seamlessly in the background without requiring explicit user approval

## Implementation Approach

We'll implement the Claude Desktop Memory Bank using the official MCP Python SDK. The implementation will follow these steps:

1. **Set up the MCP server framework**
2. **Implement memory bank selection logic**
3. **Define resources to expose memory bank files**
4. **Implement tools for context manipulation and memory bank selection**
5. **Add prompts for standardized interactions**

## Server Implementation Details

The server is implemented using a layered architecture pattern with clear separation of concerns:

```mermaid
flowchart TD
    Server[Memory Bank Server] --> Core[Core Business Logic]
    Server --> Services[Service Layer]
    Server --> Integration[Integration Layer]
    
    Services --> Core
    Integration --> Services
    
    subgraph Core [Core Business Logic Layer]
        CoreMemory[memory_bank.py]
        CoreContext[context.py]
    end
    
    subgraph Services [Service Layer]
        ContextSvc[ContextService]
        RepoSvc[RepositoryService]
        StorageSvc[StorageService]
    end
    
    subgraph Integration [Integration Layer]
        FastMCP[FastMCPIntegration]
        Direct[DirectAccess]
    end
    
    ContextSvc --> RepoSvc
    ContextSvc --> StorageSvc
    FastMCP --> ContextSvc
    Direct --> ContextSvc
```

### Core Business Logic Layer

The core layer contains pure, framework-agnostic functions with:
- No external dependencies
- Single-responsibility functions
- Explicit parameter passing
- Proper error handling

```python
# Example from memory_bank.py (core layer)
async def select_memory_bank(
    context_service,
    type: str = "global", 
    project_name: Optional[str] = None, 
    repository_path: Optional[str] = None
) -> Dict[str, Any]:
    """Core logic for selecting a memory bank."""
    return await context_service.set_memory_bank(
        type=type,
        project_name=project_name,
        repository_path=repository_path
    )
```

### Service Layer

The service layer encapsulates related functionality:
- `StorageService`: Handles file I/O operations
- `RepositoryService`: Manages Git repository interactions
- `ContextService`: Orchestrates context management

```python
# Example from context_service.py (service layer)
async def get_context(self, context_type: str) -> str:
    """Get context content from the current memory bank."""
    self._validate_context_type(context_type)
    memory_bank = await self.get_current_memory_bank()
    memory_bank_path = memory_bank["path"]
    file_name = self.CONTEXT_FILES[context_type]
    return await self.storage_service.get_context_file(memory_bank_path, file_name)
```

### Integration Layer

The integration layer provides adapters to external systems:
- `FastMCPIntegration`: Connects to the FastMCP framework
- `DirectAccess`: Provides API access independent of FastMCP

```python
# Example from direct_access.py (integration layer)
async def update_context(self, context_type: str, content: str) -> Dict[str, Any]:
    """Update a context file using the direct API."""
    return await update_context(
        self.context_service,
        context_type,
        content
    )
```

### Key Architectural Principles

- **Composition over Inheritance**: Services compose other services
- **Hierarchical Function Design**: Higher-level functions call lower-level ones
- **Clean Separation of Concerns**: Each component has a single responsibility
- **Improved Testability**: Components can be tested in isolation
- **Graceful Degradation**: System works even if FastMCP is unavailable

## Core Workflows

### Autonomous Memory Bank Selection Workflow

```mermaid
sequenceDiagram
    participant User
    participant CD as Claude Desktop
    participant FastMCP as FastMCP Integration
    participant Core as Core Business Logic
    participant ContextSvc as Context Service
    
    User->>CD: Start conversation
    CD->>FastMCP: Silently call select_memory_bank tool
    FastMCP->>Core: Call start_memory_bank function
    Core->>ContextSvc: Check for project/repository context
    ContextSvc-->>Core: Return appropriate memory bank
    Core-->>FastMCP: Return selected memory bank info
    FastMCP-->>CD: Memory bank automatically selected
    CD-->>User: Briefly acknowledge context (optional)
```

### Autonomous Repository Detection Workflow

```mermaid
sequenceDiagram
    participant User
    participant CD as Claude Desktop
    participant FastMCP as FastMCP Integration
    participant Core as Core Business Logic
    participant ContextSvc as Context Service
    participant RepoSvc as Repository Service
    
    User->>CD: Mention working in repository
    CD->>FastMCP: Silently call detect_repository tool
    FastMCP->>Core: Call detect_repository function
    Core->>ContextSvc: Request repository detection
    ContextSvc->>RepoSvc: Check path for Git repository
    RepoSvc-->>ContextSvc: Return repository info
    ContextSvc-->>Core: Return repository details
    Core-->>FastMCP: Return detected repository
    
    alt Repository has memory bank
        FastMCP->>Core: Call select_memory_bank function
        Core->>ContextSvc: Select repository memory bank
        ContextSvc-->>Core: Memory bank selected
        Core-->>FastMCP: Return memory bank info
    else Repository needs memory bank
        FastMCP->>Core: Call initialize_repository_memory_bank function
        Core->>ContextSvc: Initialize repository memory bank
        ContextSvc->>RepoSvc: Create .claude-memory directory
        RepoSvc-->>ContextSvc: Memory bank initialized
        ContextSvc-->>Core: Return new memory bank info
        Core-->>FastMCP: Return memory bank info
    end
    
    FastMCP-->>CD: Repository memory bank selected
    CD-->>User: Continue conversation with repository context
```

### Automatic Context Update Workflow

```mermaid
sequenceDiagram
    participant User
    participant CD as Claude Desktop
    participant FastMCP as FastMCP Integration
    participant Core as Core Business Logic
    participant ContextSvc as Context Service
    participant StorageSvc as Storage Service
    
    User->>CD: Share important information
    Note over CD: Identify information worth persisting
    CD->>FastMCP: Silently call update_context tool
    FastMCP->>Core: Call update_context function
    Core->>ContextSvc: Update context in current memory bank
    ContextSvc->>StorageSvc: Write to context file
    StorageSvc-->>ContextSvc: File updated
    ContextSvc-->>Core: Context update complete
    Core-->>FastMCP: Return update confirmation
    FastMCP-->>CD: Silently confirm update
    CD-->>User: Continue conversation without interruption
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
        "MEMORY_BANK_ROOT": "/path/to/storage/directory",
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

1. **Advanced Context Selection**: Implement more sophisticated algorithms to autonomously select the most relevant context
2. **Intelligent Context Summary**: Automatically generate summaries of past discussions when needed
3. **Embedding-Based Search**: Use embeddings to improve context searching without requiring explicit queries
4. **Context Versioning**: Silently track changes to context over time
5. **Git Integration**: Automatically store memory bank changes as Git commits
6. **Collaborative Memory Banks**: Seamless support for shared memory banks in team environments
7. **Context Importance Scoring**: Automatically determine which information is most important to persist
8. **Remote Hosting**: Support for transparent remote hosting when MCP supports it

## Conclusion

The Claude Desktop Memory Bank MCP server provides an autonomous memory system that enables Claude to maintain context across sessions using the Model Context Protocol. The system operates in the background with minimal user interaction, creating a seamless experience where context persists naturally across conversations.

This autonomous approach significantly reduces the cognitive load on users by eliminating the need to explicitly manage Claude's memory, allowing for more natural and productive interactions.
