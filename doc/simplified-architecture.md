# Memory Bank Simplified Architecture

This document explains the design decisions and architecture behind the Memory Bank Tool Simplification project.

## Design Goals

1. **Reduce Cognitive Load**: Simplify the API to make it easier to understand and use
2. **Maintain Functionality**: Preserve all existing capabilities
3. **Improve Reliability**: Reduce potential for race conditions and errors
4. **Enhance Autonomy**: Enable more autonomous operation with fewer explicit commands
5. **Future-Proof**: Create a cleaner foundation for future enhancements

## Core Architecture

The simplified architecture consists of exactly 4 tools:

1. **memory-bank-start**: The unified tool for initialization, detection, creation, and setup
2. **select-memory-bank**: For explicit memory bank selection
3. **bulk-update-context**: For updating multiple context files in a single operation
4. **list-memory-banks**: For diagnostics and visualization

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                       Claude Desktop                    │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Memory Bank Server                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐  ┌───────────────┐  ┌───────────┐  │
│  │ memory-bank-start│  │select-memory-bank│  │list-memory-banks│  │
│  └────────┬────────┘  └───────┬───────┘  └─────┬─────┘  │
│           │                   │                 │        │
│           ▼                   ▼                 ▼        │
│  ┌────────────────────────────────────────────────────┐ │
│  │               Memory Bank Core Services            │ │
│  │                                                    │ │
│  │  ┌──────────────┐  ┌───────────────┐  ┌─────────┐ │ │
│  │  │Context Service│  │Repository Service│  │Storage Service│ │ │
│  │  └──────────────┘  └───────────────┘  └─────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
│                            │                             │
│                            ▼                             │
│  ┌────────────────────────────────────────────────────┐ │
│  │              bulk-update-context                   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Memory Banks Storage                 │
│                                                         │
│  ┌─────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │Global Memory Bank│  │Project Memory Banks│  │Repository Memory Banks│  │
│  └─────────────┘  └────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### Unified Initialization with memory-bank-start

The `memory-bank-start` tool now handles multiple responsibilities that were previously distributed across several tools:

1. **Repository Detection**: Automatically identifies Git repositories
2. **Project Creation**: Creates new projects when requested
3. **Repository Initialization**: Sets up repository memory banks as needed
4. **Project-Repository Association**: Links projects to repositories
5. **Memory Bank Selection**: Selects the appropriate memory bank
6. **Context Loading**: Retrieves and returns the complete memory bank content
7. **Automatic Pruning**: Removes outdated content based on content type

This unified approach eliminates race conditions that could occur when these operations were performed by separate tools in sequence. It also simplifies the mental model by having a single entry point for all initialization operations.

### Consolidation of Context Updates

All context updates now go through the `bulk-update-context` tool, which can update multiple context files in a single operation. This replaces the previous approach of having separate tools for different update scenarios.

Benefits of this approach:
- Fewer API calls for common operations
- Consistent pattern for all context updates
- Reduced likelihood of conflicting updates

### Autonomy Through Custom Instructions

Rather than relying on explicit tool calls for operations like auto-summarization and pruning, the system now leverages Claude's custom instructions to perform these operations autonomously:

- **Auto-summarization**: Claude intelligently extracts and updates context based on conversation
- **Pro