from setuptools import setup, find_packages

setup(
    name="claude-desktop-memory-bank",
    version="0.1.0",
    description="Memory Bank MCP Server for Claude Desktop",
    author="Anthropic",
    packages=find_packages(),
    install_requires=[
        "mcp",
        "httpx",
        "gitpython",
    ],
    entry_points={
        "console_scripts": [
            "memory-bank-server=memory_bank_server:main",
        ],
    },
    python_requires='>=3.8',
)
