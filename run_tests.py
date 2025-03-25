#!/usr/bin/env python3
"""
Test runner script for Memory Bank project.

This script provides command-line options to run tests 
with different verbosity levels and pattern matching.
"""

import sys
import os
import subprocess
import argparse

def run_tests(patterns=None, verbose=False, coverage=False, failfast=False):
    """Run the tests with the given options."""
    # Build the pytest command with venv python
    venv_python = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python')
    cmd = [venv_python, "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add failfast
    if failfast:
        cmd.append("-x")
    
    # Add coverage if requested
    if coverage:
        cmd.append("--cov=memory_bank_server")
        cmd.append("--cov-report=term")
    
    # Add pattern if provided
    if patterns:
        # Split by spaces in case multiple patterns were provided
        cmd.extend(patterns.split())
    
    # Run the command
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Run Memory Bank tests')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-p', '--pattern', help='Test file pattern(s) (e.g., "tests/test_direct_access.py tests/test_context_service.py")')
    parser.add_argument('-c', '--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('-f', '--failfast', action='store_true', help='Stop on first failure')
    
    args = parser.parse_args()
    
    # Change to project root directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the tests
    return run_tests(args.pattern, args.verbose, args.coverage, args.failfast)

if __name__ == "__main__":
    sys.exit(main())
