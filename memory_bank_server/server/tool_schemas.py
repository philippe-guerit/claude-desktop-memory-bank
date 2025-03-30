"""
JSON Schema definitions for Memory Bank MCP tools.

This module contains the schema definitions for the Memory Bank MCP tools.
These schemas are used for validation and documentation.
"""

# Schema for context_activate tool
context_activate_schema = {
    "properties": {
        "prompt_name": {
            "anyOf": [
                {"type": "string"},
                {"type": "null"}
            ],
            "title": "Prompt Name",
            "description": "Name of the prompt template to use (e.g., 'default', 'create-project-brief')",
            "default": None
        },
        "auto_detect": {
            "type": "boolean",
            "title": "Auto Detect",
            "description": "Whether to automatically detect the repository",
            "default": True
        },
        "current_path": {
            "anyOf": [
                {"type": "string"},
                {"type": "null"}
            ],
            "title": "Current Path",
            "description": "Current path to detect repository from",
            "default": None
        },
        "force_type": {
            "anyOf": [
                {"type": "string"},
                {"type": "null"}
            ],
            "title": "Force Type",
            "description": "Force a specific memory bank type (global, project:name, repository:path)",
            "default": None
        },
        "project_name": {
            "anyOf": [
                {"type": "string"},
                {"type": "null"}
            ],
            "title": "Project Name",
            "description": "Name of the project to create or use",
            "default": None
        },
        "project_description": {
            "anyOf": [
                {"type": "string"},
                {"type": "null"}
            ],
            "title": "Project Description",
            "description": "Description of the project to create",
            "default": None
        }
    },
    "title": "context_activate_toolArguments",
    "type": "object"
}

# Schema for context_select tool
context_select_schema = {
    "properties": {
        "type": {
            "type": "string",
            "title": "Type",
            "description": "Type of memory bank to select (global, project, repository)",
            "default": "global",
            "enum": ["global", "project", "repository"]
        },
        "project": {
            "anyOf": [
                {"type": "string"},
                {"type": "null"}
            ],
            "title": "Project",
            "description": "Name of the project when selecting a project memory bank",
            "default": None
        },
        "repository_path": {
            "anyOf": [
                {"type": "string"},
                {"type": "null"}
            ],
            "title": "Repository Path",
            "description": "Path to the repository when selecting a repository memory bank",
            "default": None
        }
    },
    "title": "context_select_toolArguments",
    "type": "object",
    "required": ["type"],
    "allOf": [
        {
            "if": {
                "properties": {"type": {"enum": ["project"]}}
            },
            "then": {
                "required": ["project"]
            }
        },
        {
            "if": {
                "properties": {"type": {"enum": ["repository"]}}
            },
            "then": {
                "required": ["repository_path"]
            }
        }
    ]
}

# Schema for context_list tool
context_list_schema = {
    "properties": {},
    "title": "context_list_toolArguments",
    "type": "object"
}

# Schema for context_update tool
context_update_schema = {
    "properties": {
        "updates": {
            "additionalProperties": {
                "anyOf": [
                    {"type": "string"},
                    {
                        "additionalProperties": {"type": "string"},
                        "type": "object"
                    }
                ]
            },
            "title": "Updates",
            "description": "Dictionary of updates where keys are context types and values are either strings with complete new content or dictionaries mapping section headers to new section content",
            "type": "object"
        }
    },
    "required": ["updates"],
    "title": "context_update_toolArguments",
    "type": "object"
}
