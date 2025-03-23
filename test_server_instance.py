#!/usr/bin/env python3
import tempfile
import os
import inspect

def main():
    """Test that all required tools are registered in the server."""
    try:
        # Import the server module
        from memory_bank_server.server import MemoryBankServer
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Created temporary directory: {temp_dir}")
            
            # Initialize the server with the temporary directory
            server = MemoryBankServer(temp_dir)
            print("Memory Bank Server initialized successfully!")
            
            # Check for _register_tool_handlers method
            if hasattr(server, '_register_tool_handlers'):
                print("✅ _register_tool_handlers method found")
                
                # Inspect the method's source code
                source = inspect.getsource(server._register_tool_handlers)
                
                # Check for our new tools in the source code
                new_tools = [
                    "bulk-update-context",
                    "auto-summarize-context",
                    "prune-context"
                ]
                
                for tool in new_tools:
                    if tool in source:
                        print(f"✅ Found '{tool}' in tool handler registration source code")
                    else:
                        print(f"❌ Missing '{tool}' in tool handler registration source code")
            else:
                print("❌ _register_tool_handlers method not found")
            
            # Check for the ContextManager implementation
            if hasattr(server, 'context_manager'):
                print("✅ context_manager attribute found in MemoryBankServer")
                
                # Check for our new methods
                cm = server.context_manager
                if hasattr(cm, 'bulk_update_context'):
                    print("✅ bulk_update_context method found in context_manager")
                else:
                    print("❌ bulk_update_context method not found in context_manager")
                
                if hasattr(cm, 'auto_summarize_context'):
                    print("✅ auto_summarize_context method found in context_manager")
                else:
                    print("❌ auto_summarize_context method not found in context_manager")
                
                if hasattr(cm, 'prune_context'):
                    print("✅ prune_context method found in context_manager")
                else:
                    print("❌ prune_context method not found in context_manager")
            else:
                print("❌ context_manager attribute not found in MemoryBankServer")
            
            print("Server inspection completed successfully!")
            return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
