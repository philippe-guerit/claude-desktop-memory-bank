import os
import unittest
import tempfile
import shutil
import asyncio
from datetime import datetime, timedelta
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
class TestContextManagerExtensions(unittest.TestCase):
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
        
        # Create a test project for use in tests
        await self.context_manager.create_project("test-project", "Test project for context manager extensions")
    
    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_bulk_update_context(self):
        """Test the bulk_update_context method."""
        # Prepare test data
        updates = {
            "project_brief": "# Project Brief\n\n## Purpose\nTest bulk update purpose\n\n## Goals\nTest bulk update goals\n",
            "tech_context": "# Technical Context\n\n## Technologies\nTest bulk update technologies\n\n## Dependencies\nTest bulk update dependencies\n",
            "active_context": "# Active Context\n\n## Current Focus\nTest bulk update focus\n"
        }
        
        # Execute bulk update
        memory_bank_info = asyncio.run(self.context_manager.bulk_update_context(updates))
        
        # Verify bulk update succeeded
        self.assertEqual(memory_bank_info["type"], "project")
        self.assertEqual(memory_bank_info["project"], "test-project")
        
        # Verify each context file was updated correctly
        for context_type, content in updates.items():
            updated_content = asyncio.run(self.context_manager.get_context(context_type))
            self.assertEqual(updated_content, content)
        
        # Verify non-updated files remain unchanged
        original_progress = asyncio.run(self.context_manager.get_context("progress"))
        self.assertTrue("# Progress" in original_progress)
        self.assertFalse("Test bulk update" in original_progress)
    
    def test_bulk_update_context_invalid_type(self):
        """Test bulk_update_context with an invalid context type."""
        # Prepare test data with an invalid context type
        updates = {
            "invalid_context": "Invalid content",
            "project_brief": "Valid content"
        }
        
        # Attempt to execute bulk update with invalid type should raise ValueError
        with self.assertRaises(ValueError):
            asyncio.run(self.context_manager.bulk_update_context(updates))
        
        # Verify no updates were applied
        brief_content = asyncio.run(self.context_manager.get_context("project_brief"))
        self.assertNotEqual(brief_content, "Valid content")
    
    def test_auto_summarize_context(self):
        """Test the auto_summarize_context method."""
        # Prepare test conversation with content relevant to different context types
        conversation = """
Let's discuss the project requirements and goals.
We need to build a system that can automatically categorize user feedback.
This is a requirement from the stakeholders.

For the technical setup, we'll use Python with FastAPI for the backend.
We should also consider using PostgreSQL as our database technology.

In terms of architecture, we'll follow a microservices pattern.
This design pattern will help with scalability.

The current focus should be on setting up the development environment.
We've recently changed our approach to use Docker for containerization.

We've completed the initial API design documents.
The authentication system is currently in progress.
We're still pending the database schema finalization.
"""
        
        # Execute auto summarization
        suggested_updates = asyncio.run(self.context_manager.auto_summarize_context(conversation))
        
        # Verify that relevant contexts were identified
        self.assertIn("project_brief", suggested_updates)
        self.assertIn("tech_context", suggested_updates)
        self.assertIn("system_patterns", suggested_updates)
        self.assertIn("active_context", suggested_updates)
        self.assertIn("progress", suggested_updates)
        
        # Verify content was correctly categorized
        self.assertIn("requirements", suggested_updates["project_brief"].lower())
        self.assertIn("python", suggested_updates["tech_context"].lower())
        self.assertIn("microservices", suggested_updates["system_patterns"].lower())
        self.assertIn("current focus", suggested_updates["active_context"].lower())
        self.assertIn("completed", suggested_updates["progress"].lower())
        
        # Apply the suggested updates
        memory_bank_info = asyncio.run(self.context_manager.bulk_update_context(suggested_updates))
        
        # Verify updates were applied
        for context_type in suggested_updates.keys():
            updated_content = asyncio.run(self.context_manager.get_context(context_type))
            self.assertEqual(updated_content, suggested_updates[context_type])
    
    def test_prune_context(self):
        """Test the prune_context method."""
        # Prepare multiple dated sections in a context file
        timestamp_format = "%Y-%m-%d"
        today = datetime.utcnow()
        date_old = (today - timedelta(days=120)).strftime(timestamp_format)
        date_recent = (today - timedelta(days=30)).strftime(timestamp_format)
        date_very_old = (today - timedelta(days=180)).strftime(timestamp_format)
        
        # Create a context file with multiple dated sections
        content = f"""# Test Content

## Main Section
This is the main content that should always be preserved.

## Update {date_very_old}
This is a very old update that should be pruned.

## Update {date_recent}
This is a recent update that should be preserved.

## Update {date_old}
This is an old update that should be pruned.
"""
        
        # Update the context file
        asyncio.run(self.context_manager.update_context("project_brief", content))
        
        # Execute pruning with 90 days threshold
        pruning_results = asyncio.run(self.context_manager.prune_context(max_age_days=90))
        
        # Verify pruning results
        self.assertIn("project_brief", pruning_results)
        self.assertEqual(pruning_results["project_brief"]["pruned_sections"], 2)
        self.assertEqual(pruning_results["project_brief"]["kept_sections"], 1)
        
        # Verify content was correctly pruned
        pruned_content = asyncio.run(self.context_manager.get_context("project_brief"))
        
        # Main section should be preserved
        self.assertIn("## Main Section", pruned_content)
        
        # Recent update should be preserved
        self.assertIn(f"## Update {date_recent}", pruned_content)
        
        # Old updates should be removed
        self.assertNotIn(f"## Update {date_very_old}", pruned_content)
        self.assertNotIn(f"## Update {date_old}", pruned_content)
    
    def test_prune_context_no_pruning_needed(self):
        """Test the prune_context method when no pruning is needed."""
        # Prepare context with only recent sections
        timestamp_format = "%Y-%m-%d"
        today = datetime.utcnow()
        date_recent1 = (today - timedelta(days=10)).strftime(timestamp_format)
        date_recent2 = (today - timedelta(days=20)).strftime(timestamp_format)
        
        # Create a context file with only recent sections
        content = f"""# Test Content

## Main Section
This is the main content.

## Update {date_recent1}
This is a very recent update.

## Update {date_recent2}
This is another recent update.
"""
        
        # Update the context file
        asyncio.run(self.context_manager.update_context("project_brief", content))
        
        # Execute pruning with 90 days threshold
        pruning_results = asyncio.run(self.context_manager.prune_context(max_age_days=90))
        
        # For newer content, the function might not return results if no pruning is needed
        if "project_brief" in pruning_results:
            self.assertEqual(pruning_results["project_brief"]["pruned_sections"], 0)
            self.assertEqual(pruning_results["project_brief"]["kept_sections"], 2)
        
        # Verify content remains unchanged
        pruned_content = asyncio.run(self.context_manager.get_context("project_brief"))
        self.assertEqual(pruned_content, content)

if __name__ == '__main__':
    unittest.main()
