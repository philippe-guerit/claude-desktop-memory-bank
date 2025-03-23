"""
Simple script to verify that imports work.
"""

import sys
import os

print("Python version:", sys.version)
print("Current directory:", os.getcwd())

try:
    from memory_bank_server.server.direct_access import DirectAccess
    print("Successfully imported DirectAccess")
except ImportError as e:
    print("Failed to import DirectAccess:", e)

try:
    from memory_bank_server.server.fastmcp_integration import FastMCPIntegration
    print("Successfully imported FastMCPIntegration")
except ImportError as e:
    print("Failed to import FastMCPIntegration:", e)

try:
    from memory_bank_server.server.memory_bank_server import MemoryBankServer
    print("Successfully imported MemoryBankServer")
except ImportError as e:
    print("Failed to import MemoryBankServer:", e)

print("Import verification complete")
