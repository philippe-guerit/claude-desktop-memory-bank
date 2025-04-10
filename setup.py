"""
Setup script for Claude Desktop Memory Bank.
"""

from setuptools import setup, find_packages

setup(
    name="claude-desktop-memory-bank",
    version="2.0.0",
    description="MCP server for Claude Desktop Memory Bank",
    author="Claude Team",
    author_email="info@anthropic.com",
    packages=find_packages(),
    install_requires=[
        "mcp[cli]>=1.6.0",
        "httpx>=0.23.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0",
        "gitpython>=3.1.30",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "pytest-cov>=4.0.0",
        ],
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "memory-bank=memory_bank.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
