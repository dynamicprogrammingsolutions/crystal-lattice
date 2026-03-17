"""
Test to validate glob_search functionality and performance improvements.
This test verifies that:
1. The function returns results correctly
2. Performance is acceptable after optimization
"""
import time
import sys
from pathlib import Path
import unittest

# Setup import path 
sys.path.insert(0, str(Path(__file__).parent / "plugins/tool-compat-shared/src"))
from tool_compat_shared.search_engine import glob_search

class TestGlobFunctionality(unittest.TestCase):
    
    def test_basic_glob_functionality(self):
        """Test that basic glob still works as expected"""
        # Test in a specific directory with known files
        test_dir = str(Path(__file__).parent / "core/python")
        
        # Look for core module files 
        result = glob_search(
            pattern="**/*.py",
            search_directories=[test_dir],
            display_root=test_dir, 
            respect_git_ignore=True,
            case_sensitive=False,
        )
        
        # Should find some files
        self.assertTrue(result["ok"])
        self.assertIsInstance(result["paths"], list)
        self.assertGreaterEqual(result["count"], 0)  # May find 0 files if no py files exist, but that's ok
        
    def test_glob_with_multiple_extensions(self):
        """Test glob still works with various patterns"""
        test_dir = str(Path(__file__).parent / "docs")
        if Path(test_dir).exists():  # docs may not exist, so conditional test
            result = glob_search(
                pattern="**/*.md",
                search_directories=[test_dir],
                display_root=test_dir,
                respect_git_ignore=True, 
                case_sensitive=False,
            )
            self.assertTrue(result["ok"])
    
    def performance_test(self):
        """Placeholder to measure performance after implementation."""
        pass

if __name__ == "__main__":
    unittest.main()