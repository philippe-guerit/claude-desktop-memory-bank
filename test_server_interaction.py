#!/usr/bin/env python3
import asyncio
import json
import sys
import subprocess
import time

async def send_request(proc, request):
    """Send a request to the server and read the response."""
    # Print the request for debugging
    print(f"Sending request: {request}")
    
    # Send the request to the server
    proc.stdin.write((request + "\n").encode())
    await proc.stdin.drain()
    
    # Read the response
    response = await proc.stdout.readline()
    return response.decode().strip()

async def main():
    """Main function to test server interaction."""
    # Start the server as a subprocess
    print("Starting Memory Bank server...")
    proc = await asyncio.create_subprocess_exec(
        "python3", "-m", "memory_bank_server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Give the server time to initialize
    await asyncio.sleep(1)
    
    try:
        # Test listing memory banks
        print("\n--- Testing list-memory-banks tool ---")
        request = json.dumps({
            "tool": "list-memory-banks",
            "params": {}
        })
        response = await send_request(proc, request)
        print(f"Response: {response}")
        
        # Test create-project
        print("\n--- Testing create-project tool ---")
        request = json.dumps({
            "tool": "create-project",
            "params": {
                "name": "test-project",
                "description": "Test project for server testing"
            }
        })
        response = await send_request(proc, request)
        print(f"Response: {response}")
        
        # Test update-context
        print("\n--- Testing update-context tool ---")
        request = json.dumps({
            "tool": "update-context",
            "params": {
                "context_type": "project_brief",
                "content": "# Test Project Brief\n\nThis is a test project brief created by the server test script."
            }
        })
        response = await send_request(proc, request)
        print(f"Response: {response}")
        
        # Test bulk-update-context
        print("\n--- Testing bulk-update-context tool ---")
        request = json.dumps({
            "tool": "bulk-update-context",
            "params": {
                "updates": {
                    "active_context": "# Active Context\n\nTesting bulk-update-context tool.",
                    "tech_context": "# Tech Context\n\nTesting bulk-update-context tool with multiple files."
                }
            }
        })
        response = await send_request(proc, request)
        print(f"Response: {response}")
        
        # Test auto-summarize-context
        print("\n--- Testing auto-summarize-context tool ---")
        request = json.dumps({
            "tool": "auto-summarize-context",
            "params": {
                "conversation_text": "Let's discuss the project requirements. We need a system that can handle user authentication and data visualization. For technology stack, we'll use Python with FastAPI for the backend and React for the frontend."
            }
        })
        response = await send_request(proc, request)
        print(f"Response: {response}")
        
        # Test prune-context
        print("\n--- Testing prune-context tool ---")
        request = json.dumps({
            "tool": "prune-context",
            "params": {
                "max_age_days": 30
            }
        })
        response = await send_request(proc, request)
        print(f"Response: {response}")
        
        print("\nAll tests completed successfully!")
    
    finally:
        # Terminate the server
        print("Shutting down server...")
        proc.terminate()
        await proc.wait()

if __name__ == "__main__":
    asyncio.run(main())
