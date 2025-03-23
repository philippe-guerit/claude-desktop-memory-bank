#!/usr/bin/env python3
import subprocess
import time
import os
import tempfile

def main():
    """Test that the server starts and can be stopped."""
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
            env=env
        )
        
        # Give the server time to initialize
        time.sleep(2)
        
        # Check if the process is running
        if proc.poll() is None:
            print("Server is running successfully!")
            
            # Check if the global memory bank was created
            global_dir = os.path.join(temp_dir, "global")
            if os.path.exists(global_dir):
                print("Global memory bank directory was created successfully.")
                
                # List files in the global directory
                files = os.listdir(global_dir)
                print(f"Files in global memory bank: {files}")
            else:
                print("ERROR: Global memory bank directory was not created.")
        else:
            # If the process has exited, print the exit code and any output
            print(f"ERROR: Server exited with code {proc.returncode}")
            stdout, stderr = proc.communicate()
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return False
        
        # Terminate the server
        print("Shutting down server...")
        proc.terminate()
        proc.wait(timeout=5)
        
        print("Test completed successfully!")
        return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
