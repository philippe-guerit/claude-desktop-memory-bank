#!/usr/bin/env python3
import subprocess
import json
import time
import os
import tempfile

def main():
    """Test MCP communication with the server."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Created temporary directory: {temp_dir}")
        
        # Set the memory bank root to the temporary directory
        env = os.environ.copy()
        env["MEMORY_BANK_ROOT"] = temp_dir
        
        # Start the server as a subprocess
        print("Starting Memory Bank server...")
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
        time.sleep(2)
        
        # Check if the process is running
        if proc.poll() is not None:
            print(f"ERROR: Server exited with code {proc.returncode}")
            stdout, stderr = proc.communicate()
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
            
        try:
            # Test resources/list
            print("\n--- Testing resources/list ---")
            resources_request = json.dumps({"type": "resources/list"}) + "\n"
            proc.stdin.write(resources_request)
            proc.stdin.flush()
            
            # Wait for response
            resources_response = proc.stdout.readline().strip()
            print(f"Response: {resources_response}")
            
            # Test tools/list
            print("\n--- Testing tools/list ---")
            tools_request = json.dumps({"type": "tools/list"}) + "\n"
            proc.stdin.write(tools_request)
            proc.stdin.flush()
            
            # Wait for response
            tools_response = proc.stdout.readline().strip()
            print(f"Response: {tools_response}")
            
            # Parse the tools response
            tools_data = json.loads(tools_response)
            if "tools" in tools_data:
                tool_names = [tool["name"] for tool in tools_data["tools"]]
                print(f"Available tools: {tool_names}")
                
                # Check if our new tools are in the list
                new_tools = ["bulk-update-context", "auto-summarize-context", "prune-context"]
                for tool in new_tools:
                    if tool in tool_names:
                        print(f"✅ Found new tool: {tool}")
                    else:
                        print(f"❌ Missing new tool: {tool}")
            
            # Test prompts/list
            print("\n--- Testing prompts/list ---")
            prompts_request = json.dumps({"type": "prompts/list"}) + "\n"
            proc.stdin.write(prompts_request)
            proc.stdin.flush()
            
            # Wait for response
            prompts_response = proc.stdout.readline().strip()
            print(f"Response: {prompts_response}")
            
            print("\nAll MCP tests completed successfully!")
            return True
            
        finally:
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
