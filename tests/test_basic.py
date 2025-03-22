import os
import unittest
import tempfile
import shutil
from pathlib import Path

class TestBasicFunctionality(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_directory_structure(self):
        """Test that the directory structure is correct."""
        # Check if main project directories exist
        self.assertTrue(os.path.exists('/home/pjm/code/claude-desktop-memory-bank/memory_bank_server'))
        self.assertTrue(os.path.exists('/home/pjm/code/claude-desktop-memory-bank/storage'))
        self.assertTrue(os.path.exists('/home/pjm/code/claude-desktop-memory-bank/tests'))
        
        # Check if storage subdirectories exist
        self.assertTrue(os.path.exists('/home/pjm/code/claude-desktop-memory-bank/storage/global'))
        self.assertTrue(os.path.exists('/home/pjm/code/claude-desktop-memory-bank/storage/projects'))
        self.assertTrue(os.path.exists('/home/pjm/code/claude-desktop-memory-bank/storage/repositories'))
        self.assertTrue(os.path.exists('/home/pjm/code/claude-desktop-memory-bank/storage/templates'))
        
        # Check if template files exist
        self.assertTrue(os.path.exists('/home/pjm/code/claude-desktop-memory-bank/storage/templates/projectbrief.md'))
        self.assertTrue(os.path.exists('/home/pjm/code/claude-desktop-memory-bank/storage/templates/activeContext.md'))
    
    def test_file_operations(self):
        """Test basic file operations."""
        # Create a test file
        test_file_path = os.path.join(self.temp_dir, "testfile.md")
        with open(test_file_path, 'w') as f:
            f.write("# Test Content\n\n## Section\nTest text.")
        
        # Check if file was created
        self.assertTrue(os.path.exists(test_file_path))
        
        # Read the file
        with open(test_file_path, 'r') as f:
            content = f.read()
        
        # Check content
        self.assertEqual(content, "# Test Content\n\n## Section\nTest text.")

if __name__ == '__main__':
    unittest.main()
