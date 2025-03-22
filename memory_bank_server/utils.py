import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("memory_bank")

def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat()

def sanitize_path(path: str) -> str:
    """Sanitize and normalize a file path."""
    return os.path.normpath(os.path.abspath(path))

def format_memory_bank_info(memory_bank_info: Dict[str, Any]) -> str:
    """Format memory bank information for display."""
    result = f"Memory Bank Type: {memory_bank_info.get('type', 'unknown')}\n"
    
    if memory_bank_info.get('type') == 'repository':
        repo_info = memory_bank_info.get('repo_info', {})
        result += f"Repository: {repo_info.get('name', '')}\n"
        result += f"Path: {repo_info.get('path', '')}\n"
        if repo_info.get('branch'):
            result += f"Branch: {repo_info.get('branch', '')}\n"
        if memory_bank_info.get('project'):
            result += f"Associated Project: {memory_bank_info.get('project')}\n"
    
    elif memory_bank_info.get('type') == 'project':
        result += f"Project: {memory_bank_info.get('project', '')}\n"
    
    result += f"Storage Path: {memory_bank_info.get('path', '')}\n"
    
    return result

def validate_context_type(context_type: str) -> bool:
    """Validate that a context type is supported."""
    valid_types = [
        "project_brief", "product_context", "system_patterns", 
        "tech_context", "active_context", "progress"
    ]
    return context_type in valid_types
