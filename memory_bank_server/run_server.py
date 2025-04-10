#!/usr/bin/env python3
import runpy
import sys
import os

# Set the directory to the project root
os.chdir('/home/pjm/code/claude-desktop-memory-bank')

# Run the memory_bank_server module
runpy.run_module('memory_bank_server', run_name='__main__')