"""
Git utility functions.

This module provides Git-related utility functions.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


def detect_git_repo(path: Path) -> Optional[Dict[str, Any]]:
    """Detect if a path is inside a Git repository.
    
    Args:
        path: Path to check
        
    Returns:
        Dict with repo info if found, None otherwise
    """
    try:
        # Only import if needed
        import git
        
        # Try to find the Git repo
        try:
            repo = git.Repo(path, search_parent_directories=True)
            repo_path = Path(repo.working_dir)
            
            # Get basic Git info
            result = {
                "is_git_repo": True,
                "repo_path": str(repo_path),
                "repo_name": os.path.basename(repo_path),
                "current_branch": repo.active_branch.name if not repo.head.is_detached else "DETACHED_HEAD",
            }
            
            # Get remote URL if available
            try:
                if repo.remotes:
                    result["remote_url"] = next(repo.remotes.origin.urls)
            except (AttributeError, StopIteration):
                # No remotes or no origin
                result["remote_url"] = None
            
            # Get last commit info
            try:
                result["last_commit"] = {
                    "id": repo.head.commit.hexsha,
                    "message": repo.head.commit.message.strip(),
                    "author": f"{repo.head.commit.author.name} <{repo.head.commit.author.email}>",
                    "date": repo.head.commit.committed_datetime.isoformat()
                }
            except (AttributeError, ValueError):
                # No commits or other error
                result["last_commit"] = None
            
            return result
            
        except git.exc.InvalidGitRepositoryError:
            return None
            
    except ImportError:
        logger.warning("GitPython not installed, Git detection disabled")
        return None
    except Exception as e:
        logger.error(f"Error detecting Git repository at {path}: {e}")
        return None


def get_branch_list(repo_path: Path) -> Optional[Dict[str, Any]]:
    """Get a list of branches for a Git repository.
    
    Args:
        repo_path: Path to the Git repository
        
    Returns:
        Dict with branch info if successful, None otherwise
    """
    try:
        # Only import if needed
        import git
        
        # Open the repo
        repo = git.Repo(repo_path)
        
        # Get list of local branches
        local_branches = []
        for branch in repo.branches:
            local_branches.append({
                "name": branch.name,
                "is_active": branch.name == repo.active_branch.name,
                "last_commit": branch.commit.hexsha,
                "last_commit_date": branch.commit.committed_datetime.isoformat()
            })
        
        # Get list of remote branches
        remote_branches = []
        for remote in repo.remotes:
            try:
                # Fetch remote info
                remote.fetch()
                
                for ref in remote.refs:
                    if ref.name.startswith(f"{remote.name}/HEAD"):
                        continue  # Skip HEAD refs
                        
                    branch_name = ref.name.replace(f"{remote.name}/", "")
                    remote_branches.append({
                        "name": branch_name,
                        "remote": remote.name,
                        "last_commit": ref.commit.hexsha,
                        "last_commit_date": ref.commit.committed_datetime.isoformat()
                    })
            except Exception as e:
                logger.warning(f"Error fetching remote {remote.name}: {e}")
        
        return {
            "current_branch": repo.active_branch.name if not repo.head.is_detached else "DETACHED_HEAD",
            "local_branches": local_branches,
            "remote_branches": remote_branches
        }
        
    except ImportError:
        logger.warning("GitPython not installed, Git branch listing disabled")
        return None
    except Exception as e:
        logger.error(f"Error getting branch list for Git repository at {repo_path}: {e}")
        return None


def get_git_file_history(repo_path: Path, file_path: str) -> Optional[Dict[str, Any]]:
    """Get the history of a file in a Git repository.
    
    Args:
        repo_path: Path to the Git repository
        file_path: Path to the file, relative to the repo root
        
    Returns:
        Dict with file history if successful, None otherwise
    """
    try:
        # Only import if needed
        import git
        
        # Open the repo
        repo = git.Repo(repo_path)
        
        # Get full file path
        full_path = repo_path / file_path
        if not full_path.exists():
            return None
        
        # Get relative path from repo root
        rel_path = os.path.relpath(full_path, repo_path)
        
        # Get file history
        history = []
        for commit in repo.iter_commits(paths=rel_path, max_count=10):
            history.append({
                "commit_id": commit.hexsha,
                "author": f"{commit.author.name} <{commit.author.email}>",
                "date": commit.committed_datetime.isoformat(),
                "message": commit.message.strip()
            })
        
        return {
            "file_path": file_path,
            "history": history
        }
        
    except ImportError:
        logger.warning("GitPython not installed, Git file history disabled")
        return None
    except Exception as e:
        logger.error(f"Error getting file history for {file_path} in Git repository at {repo_path}: {e}")
        return None
