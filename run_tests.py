"""
Main Test Runner
Discovers and runs all tests in the tests/ directory
"""
import unittest
import sys
import os

def run_all_tests():
    # Ensure current directory is in sys.path
    root_dir = os.path.abspath(os.path.dirname(__file__))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    # Discovery
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir='tests', pattern='test_*.py', top_level_dir=root_dir)

    # Run
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit code
    if not result.wasSuccessful():
        sys.exit(1)

if __name__ == '__main__':
    run_all_tests()
