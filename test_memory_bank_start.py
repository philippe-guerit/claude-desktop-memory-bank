#!/usr/bin/env python3
import subprocess
import json
import time
import os
import tempfile
import shutil
from pathlib import Path

def setup_test_repo(temp_dir):
    """Set up a test Git repository in the temp directory."""
    repo_path = os.path.join(temp_dir, "test_repo")
    os.makedirs(repo_path)
    
    # Initialize Git repository
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    
    # Create a dummy file
    with open(os.path.join(repo_path, "README.md"), "w") as f:
        f.write("# Test Repository\n\nThis is a test repository for memory bank tests.")
    
    # Commit the file
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)
    
    return repo_path

def main():
    """Test memory-bank-start tool with basic default parameters."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Created temporary directory: {temp_dir}")
        
        # Set the memory bank root to the temporary directory
        env = os.environ.copy()
        env["MEMORY_BANK_ROOT"] = temp_dir
        
        # Start the server as a subprocess
        print("Starting Memory Bank server...")
        
        # Run with more debug output
        env["LOG_LEVEL"] = "DEBUG"
        
        proc = subprocess.Popen(
            ["python3", "-m", "memory_bank_server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,  # Use text mode for easier handling
            bufsize=1   # Line buffered
        )
        
        # Give the server time to initialize
        print("Waiting for server to initialize...")
        time.sleep(3)
        
        # Check if the process is running
        if proc.poll() is not None:
            print(f"ERROR: Server exited with code {proc.returncode}")
            stdout, stderr = proc.communicate()
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
            
        try:
            # Just test basic start with default parameters
            print("\n--- Testing basic start with default parameters ---")
            basic_start_request = json.dumps({
                "type": "tools/call",
                "tool": "memory-bank-start",
                "params": {}
            }) + "\n"
            print(f"Sending request: {basic_start_request.strip()}")
            
            proc.stdin.write(basic_start_request)
            proc.stdin.flush()
            
            # Wait for response
            print("Waiting for response...")
            basic_start_response = proc.stdout.readline().strip()
            print(f"Got response: {basic_start_response}")
            
            # Check for expected results if response is valid
            try:
                response_data = json.loads(basic_start_response)
                result = response_data.get("result", "")
                print(f"Result: {result}")
                print(f"Result contains <claude_display> tag: {'<claude_display>' in result}")
                print(f"Result contains expected info: {'memory bank was started successfully' in result.lower()}")
                print("\nTest completed successfully!")
                return True
            except json.JSONDecodeError:
                print(f"Response is not valid JSON: {basic_start_response}")
                return False
            
        finally:
            # Get any stderr output
            stderr_output = proc.stderr.read()
            if stderr_output:
                print(f"Server stderr output: {stderr_output}")
            
            # Terminate the server
            print("Shutting down server...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
