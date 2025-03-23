"""
Unit tests for the direct access integration layer using unittest.

This module tests the DirectAccess class which provides a direct API
to the Memory Bank functionality without FastMCP dependency.
"""

import os
import unittest
import asyncio
from unittest.mock import MagicMock, patch

# Try to import the required modules
try:
    from memory_bank_server.server.direct_access import DirectAccess
    from memory_bank_server.services.context_service import ContextService
except ImportError:
    print("Unable to import required modules. This test may not run correctly.")


class TestDirectAccess(unittest.TestCase):
    """Test case for the DirectAccess integration layer."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock context service
        self.context_service = MagicMock()
        
        # Mock repository detection
        self.context_service.repository_service = MagicMock()
        self.context_service.repository_service.detect_repository.return_value = {
            'name': 'test-repo',
            'path': '/path/to/repo',
            'branch': 'main',
            'memory_bank_path': None
        }
        
        # Mock memory bank initialization
        self.context_service.repository_service.initialize_repository_memory_bank.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank',
            'repo_info': {
                'name': 'test-repo',
                'path': '/path/to/repo',
                'branch': 'main'
            }
        }
        
        # Mock memory bank selection
        self.context_service.set_memory_bank.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank',
            'repo_info': {
                'name': 'test-repo',
                'path': '/path/to/repo',
                'branch': 'main'
            }
        }
        
        # Mock memory bank listing
        self.context_service.get_memory_banks.return_value = {
            'global': [{'path': '/path/to/global'}],
            'projects': [
                {'name': 'test-project', 'metadata': {}}
            ],
            'repositories': [
                {'name': 'test-repo', 'repo_path': '/path/to/repo'}
            ]
        }
        
        # Mock current memory bank
        self.context_service.get_current_memory_bank.return_value = {
            'type': '