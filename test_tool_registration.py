#!/usr/bin/env python3
import tempfile
import os

def main():
    """Test that all required tools are registered in the server."""
    try:
        # Import the server module
        from memory_bank_server.server import MemoryBankServer
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize the server with the temporary directory
            server = MemoryBankServer(temp_dir)
            
            # Check if server and tool handlers are initialized
            if not hasattr(server, 'server'):
                print("❌ FastMCP server not initialized")
                return False
            
            # Get all registered tools from the FastMCP server
            tool_handlers = server.server.tool_handlers
            
            # Print all registered tools
            print("Registered tools:")
            for name, handler in tool_handlers.items():
                print(f"- {name}")
            
            # Check for the new tools
            new_tools = [
                "bulk-update-context",
                "auto-summarize-context",
                "prune-context"
            ]
            
            # Verify new tools are registered
            all_registered = True
            for tool in new_tools:
                if tool in tool_handlers:
                    print(f"✅ {tool} is registered")
                else:
                    print(f"❌ {tool} is NOT registered")
                    all_registered = False
            
            if all_registered:
                print("\nAll new tools are successfully registered!")
            else:
                print("\nSome tools are missing!")
            
            return all_registered
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
