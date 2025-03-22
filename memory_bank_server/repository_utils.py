import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

class RepositoryUtils:
    @staticmethod
    def is_git_repository(path: str) -> bool:
        """Check if the given path is a git repository."""
        git_dir = os.path.join(path, '.git')
        return os.path.exists(git_dir) and os.path.isdir(git_dir)
    
    @staticmethod
    def find_repository_root(path: str) -> Optional[str]:
        """Find the nearest git repository root from a path."""
        current = os.path.abspath(path)
        while current != os.path.dirname(current):  # Stop at filesystem root
            if RepositoryUtils.is_git_repository(current):
                return current
            current = os.path.dirname(current)
        return None
    
    @staticmethod
    def get_repository_name(repo_path: str) -> str:
        """Get the name of a repository from its path."""
        return os.path.basename(repo_path)
    
    @staticmethod
    def initialize_memory_bank(repo_path: str, templates_dir: str) -> bool:
        """Initialize a .claude-memory directory in the repository."""
        memory_dir = os.path.join(repo_path, '.claude-memory')
        
        # Create directory if it doesn't exist
        if not os.path.exists(memory_dir):
            os.makedirs(memory_dir)
        
        # Copy template files
        template_files = [f for f in os.listdir(templates_dir) if f.endswith('.md')]
        for template_file in template_files:
            source = os.path.join(templates_dir, template_file)
            destination = os.path.join(memory_dir, template_file)
            
            # Only copy if destination doesn't exist
            if not os.path.exists(destination):
                with open(source, 'r', encoding='utf-8') as src_file:
                    with open(destination, 'w', encoding='utf-8') as dest_file:
                        dest_file.write(src_file.read())
        
        return True
    
    @staticmethod
    def get_repository_info(repo_path: str) -> Dict[str, Any]:
        """Get information about a Git repository."""
        try:
            # Get repository name
            name = RepositoryUtils.get_repository_name(repo_path)
            
            # Get remote URL if available
            remote_url = ""
            try:
                result = subprocess.run(
                    ["git", "config", "--get", "remote.origin.url"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    remote_url = result.stdout.strip()
            except Exception:
                pass
            
            # Get current branch
            branch = ""
            try:
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    branch = result.stdout.strip()
            except Exception:
                pass
            
            return {
                "name": name,
                "path": repo_path,
                "remote_url": remote_url,
                "branch": branch,
                "memory_bank_path": os.path.join(repo_path, '.claude-memory')
            }
        except Exception as e:
            return {
                "name": os.path.basename(repo_path),
                "path": repo_path,
                "error": str(e)
            }
