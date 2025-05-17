"""Final tests to achieve 100% coverage for starburst_main.py"""

import subprocess
import sys
import unittest
from io import StringIO


class TestStarburst99FinalCoverage(unittest.TestCase):
    """Final tests for 100% coverage of starburst_main.py"""
    
    def test_import_error_branch(self):
        """Test the import error fallback by running script directly"""
        # Create a test script that imports starburst_main without package context
        test_script = '''
import sys
import os

# Add directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import which will hit the except ImportError block
import starburst_main

# Run a simple test
s = starburst_main.Starburst99()
print("Import successful")
'''
        
        # Write the test script temporarily
        with open('test_import_error.py', 'w') as f:
            f.write(test_script)
        
        try:
            # Run the script which should hit the except ImportError block
            result = subprocess.run([sys.executable, 'test_import_error.py'], 
                                  capture_output=True, text=True)
            self.assertIn("Import successful", result.stdout)
        finally:
            # Clean up
            import os
            if os.path.exists('test_import_error.py'):
                os.remove('test_import_error.py')
    
    def test_main_name_equals_main(self):
        """Test the if __name__ == '__main__' branch"""
        # Create a script that runs starburst_main as main
        test_script = '''
import sys
sys.argv = ['starburst_main.py', '--help']
exec(open('starburst_main.py').read())
'''
        
        # Write the test script
        with open('test_main_execution.py', 'w') as f:
            f.write(test_script)
        
        try:
            # Run the script
            result = subprocess.run([sys.executable, 'test_main_execution.py'], 
                                  capture_output=True, text=True)
            # Should show help message
            self.assertIn("usage:", result.stdout.lower())
        finally:
            # Clean up
            import os
            if os.path.exists('test_main_execution.py'):
                os.remove('test_main_execution.py')


if __name__ == '__main__':
    unittest.main()