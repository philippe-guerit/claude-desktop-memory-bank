#!/bin/bash

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install the package in development mode
pip install -e .

# Print installation complete message
echo "Claude Desktop Memory Bank installed successfully!"
echo ""
echo "To run the server manually for testing:"
echo "  source venv/bin/activate"
echo "  memory-bank-server"
echo ""
echo "To configure Claude Desktop, update claude_desktop_config.json with:"
echo "{"
echo "  \"mcpServers\": {"
echo "    \"memory-bank\": {"
echo "      \"command\": \"$(pwd)/venv/bin/python\","
echo "      \"args\": [\"-m\", \"memory_bank_server\"],"
echo "      \"env\": {"
echo "        \"MEMORY_BANK_ROOT\": \"$(pwd)/storage\","
echo "        \"ENABLE_REPO_DETECTION\": \"true\""
echo "      }"
echo "    }"
echo "  }"
echo "}"
