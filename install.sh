#!/bin/bash
# Installation script for Claude Desktop Memory Bank

# Create and activate virtual environment
echo "Creating virtual environment..."
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate

# Verify virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Failed to activate virtual environment. Exiting."
    exit 1
fi

# Upgrade pip
echo "Upgrading pip..."
.venv/bin/pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
.venv/bin/pip install -r requirements.txt

# Install the package in development mode
echo "Installing package in development mode..."
.venv/bin/pip install -e .

echo "Installation complete. Activate the virtual environment with:"
echo "source .venv/bin/activate"
