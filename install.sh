#!/bin/bash
# Installation script for Claude Desktop Memory Bank

# Create and activate virtual environment
echo "Creating virtual environment..."
rm -rf .venv
python -m venv .venv
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install the package in development mode
echo "Installing package in development mode..."
pip install -e .

echo "Installation complete. Activate the virtual environment with:"
echo "source .venv/bin/activate"
