# Testing Guide

This document describes the testing structure and practices for the Claude Desktop Memory Bank project.

## Test Organization

The tests are organized by component to improve maintainability and isolation:

```
tests/
├── conftest.py               # Shared fixtures and test utilities
├── test_cache/               # Tests for cache optimization
│   └── test_optimizer.py     # Tests for cache optimizations
├── test_storage/             # Tests for storage components
│   ├── test_bank_operations.py  # Tests for bank file operations
│   └── test_storage_manager.py  # Tests for the StorageManager
├── test_tools/               # Tests for MCP tool implementations
│   ├── test_activate_tool.py # Tests for the activate tool
│   ├── test_list_tool.py     # Tests for the list tool
│   ├── test_swap_tool.py     # Tests for the swap tool
│   └── test_update_tool.py   # Tests for the update tool
├── test_utils/               # Tests for utility functions
│   ├── test_file_utils.py    # Tests for file operations
│   └── test_git_utils.py     # Tests for Git utilities
├── test_integration/         # Integration tests
│   └── test_workflow.py      # Tests for complete workflows
└── test_main.py              # Tests for the main entry point
```

## Shared Fixtures

Common test fixtures are defined in `conftest.py` and include:

- `temp_storage_dir`: Creates a temporary directory for tests
- `storage_manager`: Creates a `StorageManager` with a temporary storage directory
- `server`: Creates a `MemoryBankServer` instance for testing tools
- `parse_response`: Helper function to parse MCP tool responses

## Running Tests

To run the complete test suite:

```bash
pytest
```

To run tests with coverage reporting:

```bash
pytest --cov=memory_bank
```

To run specific test categories:

```bash
# Run storage tests
pytest tests/test_storage/

# Run specific test file
pytest tests/test_tools/test_activate_tool.py

# Run specific test
pytest tests/test_tools/test_activate_tool.py::test_activate_tool
```

## Continuous Integration

The project uses GitHub Actions for automated testing:

- **Tests Workflow**: Runs all tests on multiple Python versions (3.8-3.12)
- **Linting Workflow**: Checks code style and quality with flake8, black, and isort
- **Coverage Reporting**: Uploads test coverage reports to Codecov

## Adding New Tests

When adding new tests, follow these guidelines:

1. **Test Location**: Add tests in the appropriate category directory
2. **Fixtures**: Use existing fixtures from `conftest.py` when possible
3. **Naming Convention**: Use descriptive names with `test_` prefix
4. **MCP Tool Tests**: Always test both success and error cases
5. **Mocks**: Use `unittest.mock` to mock external dependencies
6. **Async Tests**: Use `pytest.mark.asyncio` for asynchronous tests

## Testing Best Practices

1. **Isolation**: Each test should be independent and isolated
2. **Cleanup**: Clean up any resources created during tests
3. **Parameterization**: Use `pytest.mark.parametrize` for testing multiple cases
4. **Fixtures**: Use fixtures to share common setup code
5. **Assertions**: Use explicit assertions to clearly indicate what's being tested

## MCP Testing Tips

When testing MCP tools:

1. **Response Parsing**: Use the `parse_response` helper to handle TextContent objects
2. **Tool Mocking**: Mock `call_tool` to simulate MCP invocations
3. **Server Lifecycle**: Properly handle server startup and shutdown in tests
4. **Error Cases**: Test both success and error cases for all tools
5. **Validation**: Verify tool responses have the expected structure

## Coverage Goals

The project aims for the following test coverage targets:

- **Overall**: 90%+ code coverage
- **Core Components**: 95%+ code coverage for storage and tools
- **Utilities**: 80%+ code coverage for utility functions
- **Edge Cases**: Test both success and error paths

## Future Test Improvements

Areas for further test improvements:

1. **Performance Tests**: Add tests for measuring and optimizing performance
2. **Integration Testing**: Add more complex integration scenarios
3. **Server Testing**: Improve tests for server startup and shutdown
4. **Stress Testing**: Add tests for handling large memory banks
5. **Property-Based Testing**: Add property-based tests for complex functionality
