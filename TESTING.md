# Testing the Claude Desktop Memory Bank

This document provides instructions for running tests on the Claude Desktop Memory Bank.

## Prerequisites

Before running tests, ensure you have:

- Python 3.8 or newer
- pip (Python package installer)
- virtualenv or venv module

## Setting Up Test Environment

1. **Create a virtual environment**:
   ```bash
   python -m venv test-env
   ```

2. **Activate the virtual environment**:
   - On Linux/macOS:
     ```bash
     source test-env/bin/activate
     ```
   - On Windows:
     ```bash
     test-env\Scripts\activate
     ```

3. **Install the package in development mode with dependencies**:
   ```bash
   pip install -e .
   ```

## Running Tests

### Running Basic Tests

These tests check the directory structure and basic file operations:

```bash
python -m tests.test_basic
```

### Running Full Server Tests

These tests verify the functionality of the memory bank server:

```bash
python -m tests.test_server
```

### Running a Specific Test Case

To run a specific test method:

```bash
python -m tests.test_server TestMemoryBank.test_global_memory_bank
```

## Test Coverage

To run tests with coverage reporting:

1. **Install coverage**:
   ```bash
   pip install coverage
   ```

2. **Run tests with coverage**:
   ```bash
   coverage run -m tests.test_server
   ```

3. **Generate coverage report**:
   ```bash
   coverage report
   ```

## Troubleshooting

If you encounter a `ModuleNotFoundError` for the `mcp` module, ensure you've properly installed the package dependencies:

```bash
pip install mcp httpx gitpython
```

If the MCP package is not available, you may need to get it from the Anthropic MCP SDK distribution.
