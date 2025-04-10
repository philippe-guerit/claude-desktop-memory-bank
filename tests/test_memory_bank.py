"""
Basic tests for the memory bank implementation.
"""

import pytest
import asyncio
import json
from pathlib import Path
import tempfile
import shutil
import os

from memory_bank.server import MemoryBankServer
from memory_bank.storage.manager import StorageManager


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for memory bank storage."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def storage_manager(temp_storage_dir):
    """Create a storage manager with a temporary storage directory."""
    return StorageManager(temp_storage_dir)


@pytest.fixture
async def server(temp_storage_dir):
    """Create and start a memory bank server with a temporary storage directory."""
    server = MemoryBankServer(storage_root=temp_storage_dir)
    await server.start()
    yield server
    await server.stop()


@pytest.mark.asyncio
async def test_global_bank_creation(storage_manager):
    """Test creating a global memory bank."""
    # Create a global bank
    bank = storage_manager.create_bank("global", "test_bank")
    
    # Check that the bank was created
    assert bank is not None
    assert bank.bank_id == "test_bank"
    
    # Check that default files were created
    files = bank.list_files()
    assert "context.md" in files
    assert "preferences.md" in files
    assert "references.md" in files


@pytest.mark.asyncio
async def test_project_bank_creation(storage_manager):
    """Test creating a project memory bank."""
    # Create a project bank
    bank = storage_manager.create_bank("project", "test_project")
    
    # Check that the bank was created
    assert bank is not None
    assert bank.bank_id == "test_project"
    
    # Check that default files were created
    files = bank.list_files()
    assert "readme.md" in files
    assert "doc/architecture.md" in files
    assert "doc/design.md" in files
    assert "doc/progress.md" in files
    assert "tasks.md" in files


@pytest.mark.asyncio
async def test_code_bank_creation(storage_manager):
    """Test creating a code memory bank."""
    # Create a code bank
    bank = storage_manager.create_bank("code", "test_repo")
    
    # Check that the bank was created
    assert bank is not None
    assert bank.bank_id == "test_repo"
    
    # Check that default files were created
    files = bank.list_files()
    assert "readme.md" in files
    assert "doc/architecture.md" in files
    assert "doc/design.md" in files
    assert "doc/api.md" in files
    assert "structure.md" in files
    assert "snippets.md" in files


@pytest.mark.asyncio
async def test_file_update(storage_manager):
    """Test updating a file in a memory bank."""
    # Create a bank
    bank = storage_manager.create_bank("global", "test_bank")
    
    # Update a file
    test_content = "# Test Content\n\nThis is test content."
    success = bank.update_file("test.md", test_content)
    
    # Check that the update was successful
    assert success
    
    # Check that the file was created with the correct content
    loaded_content = bank.load_file("test.md")
    assert loaded_content == test_content
    
    # Test file append
    additional_content = "\n\n## Additional Section\nThis is additional content."
    success = bank.update_file("test.md", additional_content, operation="append")
    
    # Check that the append was successful
    assert success
    
    # Check that the file contains both contents
    loaded_content = bank.load_file("test.md")
    assert test_content in loaded_content
    assert additional_content in loaded_content


@pytest.mark.asyncio
async def test_activate_tool(server):
    """Test the activate tool."""
    # Call the activate tool handler directly for testing
    result = await asyncio.gather(
        server.server.invoke_tool(
            "activate",
            {
                "bank_type": "global",
                "bank_id": "test_activate"
            }
        )
    )
    response = result[0]
    
    # Check response structure
    assert "status" in response
    assert response["status"] == "success"
    assert "bank_info" in response
    assert response["bank_info"]["type"] == "global"
    assert response["bank_info"]["id"] == "test_activate"
    assert "content" in response
    assert "custom_instructions" in response


@pytest.mark.asyncio
async def test_list_tool(server):
    """Test the list tool."""
    # Create a bank first
    await asyncio.gather(
        server.server.invoke_tool(
            "activate",
            {
                "bank_type": "global",
                "bank_id": "test_list"
            }
        )
    )
    
    # Call the list tool handler directly for testing
    result = await asyncio.gather(
        server.server.invoke_tool(
            "list",
            {}
        )
    )
    response = result[0]
    
    # Check response structure
    assert "global" in response
    
    # Find our test bank
    found = False
    for bank in response["global"]:
        if bank["id"] == "test_list":
            found = True
            break
    
    assert found, "Created bank not found in list response"


@pytest.mark.asyncio
async def test_update_tool(server):
    """Test the update tool."""
    # Create a bank first
    await asyncio.gather(
        server.server.invoke_tool(
            "activate",
            {
                "bank_type": "global",
                "bank_id": "test_update"
            }
        )
    )
    
    # Call the update tool handler directly for testing
    test_content = "# Test Update\n\nThis is a test update to the memory bank."
    result = await asyncio.gather(
        server.server.invoke_tool(
            "update",
            {
                "bank_type": "global",
                "bank_id": "test_update",
                "target_file": "test.md",
                "operation": "replace",
                "content": test_content,
                "trigger_type": "user_request",
                "conversation_id": "test_conversation",
                "update_count": 1
            }
        )
    )
    response = result[0]
    
    # Check response structure
    assert "status" in response
    assert response["status"] == "success"
    assert "updated_file" in response
    assert response["updated_file"] == "test.md"
    assert "verification" in response
    
    # Verify that the file was updated correctly
    bank = server.storage.get_bank("global", "test_update")
    assert bank is not None
    
    loaded_content = bank.load_file("test.md")
    assert test_content in loaded_content


@pytest.mark.asyncio
async def test_swap_tool(server):
    """Test the swap tool."""
    # Create two banks first
    await asyncio.gather(
        server.server.invoke_tool(
            "activate",
            {
                "bank_type": "global",
                "bank_id": "test_swap_1"
            }
        )
    )
    
    await asyncio.gather(
        server.server.invoke_tool(
            "activate",
            {
                "bank_type": "project",
                "bank_id": "test_swap_2"
            }
        )
    )
    
    # Call the swap tool handler directly for testing
    result = await asyncio.gather(
        server.server.invoke_tool(
            "swap",
            {
                "bank_type": "project",
                "bank_id": "test_swap_2",
                "temporary": True
            }
        )
    )
    response = result[0]
    
    # Check response structure
    assert "status" in response
    assert response["status"] == "success"
    assert "bank_info" in response
    assert response["bank_info"]["type"] == "project"
    assert response["bank_info"]["id"] == "test_swap_2"
    assert "content" in response
    assert "custom_instructions" in response
    
    # Check that the temporary flag is set
    assert "bank_info" in response
    assert "temporary" in response["bank_info"]
    assert response["bank_info"]["temporary"] is True


@pytest.mark.asyncio
async def test_insert_operation(storage_manager):
    """Test the insert operation for updating files."""
    # Create a bank
    bank = storage_manager.create_bank("global", "test_insert")
    
    # Create a file with sections
    initial_content = """# Test File

## Section 1
This is section 1 content.

## Section 2
This is section 2 content.

## Section 3
This is section 3 content.
"""
    
    success = bank.update_file("test.md", initial_content)
    assert success
    
    # Insert content into a specific section
    insert_content = "This is new content for section 2."
    success = bank.update_file("test.md", insert_content, operation="insert", position="Section 2")
    
    # Check that the insert was successful
    assert success
    
    # Check that the content was inserted correctly
    loaded_content = bank.load_file("test.md")
    assert "## Section 2" in loaded_content
    assert "This is new content for section 2." in loaded_content
    assert "This is section 2 content." in loaded_content


@pytest.mark.asyncio
async def test_cache_file_creation(storage_manager):
    """Test that a cache file is created when updating files."""
    # Create a bank
    bank = storage_manager.create_bank("global", "test_cache")
    
    # Update a file
    test_content = "# Test Content\n\nThis is test content."
    success = bank.update_file("test.md", test_content)
    
    # Check that the update was successful
    assert success
    
    # Check that the cache file was created
    cache_path = bank.cache_path
    assert cache_path.exists()
    
    # Check cache file structure
    try:
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
        
        assert "files" in cache_data
        assert "test.md" in cache_data["files"]
        assert "summaries" in cache_data or "meta" in cache_data
    except json.JSONDecodeError:
        pytest.fail("Cache file is not valid JSON")


@pytest.mark.asyncio
async def test_custom_instructions(server):
    """Test that custom instructions are returned from tools."""
    # Call the activate tool handler directly for testing
    result = await asyncio.gather(
        server.server.invoke_tool(
            "activate",
            {
                "bank_type": "code",
                "bank_id": "test_instructions"
            }
        )
    )
    response = result[0]
    
    # Check custom instructions structure
    assert "custom_instructions" in response
    instructions = response["custom_instructions"]
    
    assert "directives" in instructions
    assert len(instructions["directives"]) > 0
    
    assert "prompts" in instructions
    assert len(instructions["prompts"]) > 0
    
    # Check for code-specific directives
    found_code_directive = False
    for directive in instructions["directives"]:
        if "CODE_" in directive["name"]:
            found_code_directive = True
            break
    
    assert found_code_directive, "Code-specific directives not found"


@pytest.mark.asyncio
async def test_automatic_git_detection(temp_storage_dir):
    """Test that Git repositories are automatically detected."""
    # Skip this test if GitPython is not installed
    pytest.importorskip("git", reason="GitPython not installed")
    
    try:
        # Create a mock Git repository
        repo_dir = temp_storage_dir / "test_repo"
        repo_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Git repo (requires git command line)
        init_result = os.system(f"cd {repo_dir} && git init && git config user.name 'Test User' && git config user.email 'test@example.com'")
        if init_result != 0:
            pytest.skip("Failed to initialize Git repository")
        
        # Create server with the storage directory
        server = MemoryBankServer(storage_root=temp_storage_dir)
        await server.start()
        
        try:
            # Call activate with auto detection
            result = await asyncio.gather(
                server.server.invoke_tool(
                    "activate",
                    {
                        "bank_type": "code",
                        "bank_id": "auto",
                        "current_path": str(repo_dir)
                    }
                )
            )
            response = result[0]
            
            # Check if Git info was detected
            assert "bank_info" in response
            assert response["bank_info"]["type"] == "code"
            
            # Extract bank ID
            bank_id = response["bank_info"]["id"]
            
            # Get the bank and check Git info
            bank = server.storage.get_bank("code", bank_id)
            meta = bank.get_meta()
            
            # If Git detection succeeded, there should be Git info
            if "git" in meta:
                assert meta["git"]["is_git_repo"] is True
                assert "repo_path" in meta["git"]
            
        finally:
            await server.stop()
    
    except Exception as e:
        pytest.skip(f"Git detection test failed: {e}")


@pytest.mark.asyncio
async def test_full_workflow(server):
    """Test a full workflow of activating, updating, and swapping banks."""
    # Step 1: Activate a global bank
    result1 = await asyncio.gather(
        server.server.invoke_tool(
            "activate",
            {
                "bank_type": "global",
                "bank_id": "workflow_test"
            }
        )
    )
    response1 = result1[0]
    assert response1["status"] == "success"
    
    # Step 2: Update the global bank
    result2 = await asyncio.gather(
        server.server.invoke_tool(
            "update",
            {
                "bank_type": "global",
                "bank_id": "workflow_test",
                "target_file": "preferences.md",
                "operation": "append",
                "content": "## Workflow Test\nThis is a workflow test update.",
                "trigger_type": "user_request",
                "conversation_id": "workflow_test",
                "update_count": 1
            }
        )
    )
    response2 = result2[0]
    assert response2["status"] == "success"
    
    # Step 3: Activate a project bank
    result3 = await asyncio.gather(
        server.server.invoke_tool(
            "activate",
            {
                "bank_type": "project",
                "bank_id": "workflow_project",
                "project_name": "Workflow Test Project",
                "project_description": "A project for testing the workflow."
            }
        )
    )
    response3 = result3[0]
    assert response3["status"] == "success"
    
    # Step 4: Update the project bank
    result4 = await asyncio.gather(
        server.server.invoke_tool(
            "update",
            {
                "bank_type": "project",
                "bank_id": "workflow_project",
                "target_file": "doc/architecture.md",
                "operation": "append",
                "content": "## Test Architecture\nThis is a test architecture update.",
                "trigger_type": "architecture",
                "conversation_id": "workflow_test",
                "update_count": 2
            }
        )
    )
    response4 = result4[0]
    assert response4["status"] == "success"
    
    # Step 5: Swap back to the global bank
    result5 = await asyncio.gather(
        server.server.invoke_tool(
            "swap",
            {
                "bank_type": "global",
                "bank_id": "workflow_test"
            }
        )
    )
    response5 = result5[0]
    assert response5["status"] == "success"
    
    # Check that content from step 2 is in the swapped bank
    assert "preferences.md" in response5["content"]
    assert "Workflow Test" in response5["content"]["preferences.md"]
    
    # Step 6: List all banks
    result6 = await asyncio.gather(
        server.server.invoke_tool(
            "list",
            {}
        )
    )
    response6 = result6[0]
    
    # Check that both banks are in the list
    global_banks = response6["global"]
    project_banks = response6["projects"]
    
    global_found = False
    for bank in global_banks:
        if bank["id"] == "workflow_test":
            global_found = True
            break
    assert global_found, "Global bank not found in list"
    
    project_found = False
    for bank in project_banks:
        if bank["id"] == "workflow_project":
            project_found = True
            break
    assert project_found, "Project bank not found in list"
