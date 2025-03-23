#!/usr/bin/env python3

def main():
    """Test that all required modules can be imported."""
    try:
        # Import main modules
        from memory_bank_server.server import MemoryBankServer
        from memory_bank_server.context_manager import ContextManager
        from memory_bank_server.storage_manager import StorageManager
        from memory_bank_server.memory_bank_selector import MemoryBankSelector
        from memory_bank_server.repository_utils import RepositoryUtils
        
        print("✅ All modules imported successfully!")
        
        # Check for bulk_update_context method in ContextManager
        if hasattr(ContextManager, 'bulk_update_context'):
            print("✅ bulk_update_context method found in ContextManager")
        else:
            print("❌ bulk_update_context method not found in ContextManager")
        
        # Check for auto_summarize_context method in ContextManager
        if hasattr(ContextManager, 'auto_summarize_context'):
            print("✅ auto_summarize_context method found in ContextManager")
        else:
            print("❌ auto_summarize_context method not found in ContextManager")
        
        # Check for prune_context method in ContextManager
        if hasattr(ContextManager, 'prune_context'):
            print("✅ prune_context method found in ContextManager")
        else:
            print("❌ prune_context method not found in ContextManager")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
