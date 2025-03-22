import os
import unittest
import tempfile
import shutil
import asyncio
from pathlib import Path

# Try to import memory_bank modules, skip tests if dependencies are missing
try:
    from memory_bank_server.repository_utils import RepositoryUtils
    from memory_bank_server.storage_manager import StorageManager
    from memory_bank_server.memory_bank_selector import MemoryBankSelector
    from memory_bank_server.context_manager import ContextManager
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Skipping tests due to missing dependency: {e}")
    DEPENDENCIES_AVAILABLE = False

@unittest.skipIf(not DEPENDENCIES_AVAILABLE, "One or more dependencies not available")
class TestMemoryBank(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create storage structure
        self.storage_path = os.path.join(self.temp_dir, "storage")
        os.makedirs(os.path.join(self.storage_path, "global"))
        os.makedirs(os.path.join(self.storage_path, "projects"))
        os.makedirs(os.path.join(self.storage_path, "repositories"))
        os.makedirs(os.path.join(self.storage_path, "templates"))
        
        # Create template files
        template_files = {
            "projectbrief.md": "# Project Brief\n\n## Purpose\n\n## Goals\n\n## Requirements\n\n## Scope\n",
            "productContext.md": "# Product Context\n\n## Problem\n\n## Solution\n\n## User Experience\n\n## Stakeholders\n",
            "systemPatterns.md": "# System Patterns\n\n## Architecture\n\n## Patterns\n\n## Decisions\n\n## Relationships\n",
            "techContext.md": "# Technical Context\n\n## Technologies\n\n## Setup\n\n## Constraints\n\n## Dependencies\n",
            "activeContext.md": "# Active Context\n\n## Current Focus\n\n## Recent Changes\n\n## Next Steps\n\n## Active Decisions\n",
            "progress.md": "# Progress\n\n## Completed\n\n## In Progress\n\n## Pending\n\n## Issues\n"
        }
        
        for filename, content in template_files.items():
            with open(os.path.join(self.storage_path, "templates", filename), 'w') as f:
                f.write(content)
        
        # Initialize components
        self.storage_manager = StorageManager(self.storage_path)
        self.memory_bank_selector = MemoryBankSelector(self.storage_manager)
        self.context_manager = ContextManager(self.storage_manager, self.memory_bank_selector)
        
        # Initialize async components
        asyncio.run(self.async_setup())
    
    async def async_setup(self):
        # Initialize the memory bank
        await self.context_manager.initialize()
    
    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_global_memory_bank(self):
        # Test that global memory bank is initialized by default
        memory_bank = asyncio.run(self.memory_bank_selector.get_current_memory_bank())
        self.assertEqual(memory_bank["type"], "global")
        self.assertEqual(memory_bank["path"], str(Path(self.storage_path) / "global"))
    
    def test_create_project(self):
        # Test creating a project
        project = asyncio.run(self.context_manager.create_project("test-project", "Test project description"))
        
        # Check that project was created
        self.assertEqual(project["name"], "test-project")
        self.assertEqual(project["description"], "Test project description")
        
        # Check that project memory bank is now selected
        memory_bank = asyncio.run(self.memory_bank_selector.get_current_memory_bank())
        self.assertEqual(memory_bank["type"], "project")
        self.assertEqual(memory_bank["project"], "test-project")
        
        # Check that project files were created
        project_path = os.path.join(self.storage_path, "projects", "test-project")
        self.assertTrue(os.path.exists(project_path))
        self.assertTrue(os.path.exists(os.path.join(project_path, "projectbrief.md")))
        self.assertTrue(os.path.exists(os.path.join(project_path, "project.json")))
    
    def test_update_context(self):
        # Create a project first
        asyncio.run(self.context_manager.create_project("test-project", "Test project description"))
        
        # Update context
        new_content = "# Project Brief\n\n## Purpose\nTest purpose\n\n## Goals\nTest goals\n"
        asyncio.run(self.context_manager.update_context("project_brief", new_content))
        
        # Check that context was updated
        context = asyncio.run(self.context_manager.get_context("project_brief"))
        self.assertEqual(context, new_content)
    
    def test_search_context(self):
        # Create a project first
        asyncio.run(self.context_manager.create_project("test-project", "Test project description"))
        
        # Update context with searchable content
        new_content = "# Project Brief\n\n## Purpose\nTest searchable content\n\n## Goals\nMore test content\n"
        asyncio.run(self.context_manager.update_context("project_brief", new_content))
        
        # Search for content
        results = asyncio.run(self.context_manager.search_context("searchable"))
        
        # Check search results
        self.assertIn("project_brief", results)
        self.assertTrue(any("searchable" in line for line in results["project_brief"]))

if __name__ == '__main__':
    unittest.main()
