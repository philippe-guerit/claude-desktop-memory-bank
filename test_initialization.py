#!/usr/bin/env python3
import tempfile
import os
import asyncio

async def main():
    """Test the server initialization process."""
    try:
        # Import the server module
        from memory_bank_server.server import MemoryBankServer
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Created temporary directory: {temp_dir}")
            
            # Initialize the server with the temporary directory
            server = MemoryBankServer(temp_dir)
            print("Memory Bank Server object created successfully!")
            
            # Call the initialize method
            print("Initializing server...")
            await server.initialize()
            print("Server initialized successfully!")
            
            # Check that global memory bank was created
            global_dir = os.path.join(temp_dir, "global")
            if os.path.exists(global_dir):
                print("✅ Global memory bank directory created")
                
                # List files in the global directory
                files = os.listdir(global_dir)
                print(f"Files in global memory bank: {files}")
                
                # Verify new context files are created
                expected_files = [
                    "projectbrief.md",
                    "productContext.md", 
                    "systemPatterns.md", 
                    "techContext.md", 
                    "activeContext.md", 
                    "progress.md"
                ]
                
                all_files_present = True
                for file in expected_files:
                    if file in files:
                        print(f"✅ {file} exists")
                    else:
                        print(f"❌ {file} is missing")
                        all_files_present = False
                
                if all_files_present:
                    print("All expected context files are present!")
                else:
                    print("Some context files are missing!")
            else:
                print("❌ Global memory bank directory was not created")
            
            print("Initialization test completed successfully!")
            return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        exit(1)
