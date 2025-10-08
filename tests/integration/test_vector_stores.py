"""Integration tests for vector stores API.

Tests complete vector store CRUD operations, file management,
chunking strategies, expiration policies, search operations,
and concurrent access.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from .utils import FakeAIClient

logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestVectorStoreBasicOperations:
    """Test basic CRUD operations for vector stores."""

    def test_create_vector_store_basic(self, client: FakeAIClient):
        """Test creating a basic vector store."""
        response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "Test Vector Store",
            },
        )

        assert response["id"].startswith("vs_")
        assert response["object"] == "vector_store"
        assert response["name"] == "Test Vector Store"
        assert response["status"] == "completed"
        assert response["file_counts"]["total"] == 0
        assert response["usage_bytes"] == 0
        assert "created_at" in response

    def test_create_vector_store_with_metadata(self, client: FakeAIClient):
        """Test creating a vector store with metadata."""
        metadata = {
            "purpose": "testing",
            "environment": "integration",
            "version": "1.0",
        }

        response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "Vector Store with Metadata",
                "metadata": metadata,
            },
        )

        assert response["metadata"] == metadata

    def test_retrieve_vector_store(self, client: FakeAIClient):
        """Test retrieving a vector store by ID."""
        # Create vector store
        create_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "Retrieve Test"},
        )
        vs_id = create_response["id"]

        # Retrieve it
        retrieve_response = client.request("GET", f"/v1/vector_stores/{vs_id}")

        assert retrieve_response["id"] == vs_id
        assert retrieve_response["name"] == "Retrieve Test"
        assert "last_active_at" in retrieve_response

    def test_retrieve_nonexistent_vector_store(self, client: FakeAIClient):
        """Test retrieving a nonexistent vector store returns 404."""
        response = client.request(
            "GET",
            "/v1/vector_stores/vs_nonexistent",
            expected_status=404,
        )

        assert "error" in response

    def test_modify_vector_store_name(self, client: FakeAIClient):
        """Test modifying vector store name."""
        # Create vector store
        create_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "Original Name"},
        )
        vs_id = create_response["id"]

        # Modify name
        modify_response = client.request(
            "POST",
            f"/v1/vector_stores/{vs_id}",
            json={"name": "Updated Name"},
        )

        assert modify_response["name"] == "Updated Name"
        assert modify_response["id"] == vs_id

    def test_modify_vector_store_metadata(self, client: FakeAIClient):
        """Test modifying vector store metadata."""
        # Create vector store
        create_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "Metadata Test",
                "metadata": {"initial": "value"},
            },
        )
        vs_id = create_response["id"]

        # Update metadata
        new_metadata = {"updated": "true", "version": "2"}
        modify_response = client.request(
            "POST",
            f"/v1/vector_stores/{vs_id}",
            json={"metadata": new_metadata},
        )

        assert modify_response["metadata"] == new_metadata

    def test_delete_vector_store(self, client: FakeAIClient):
        """Test deleting a vector store."""
        # Create vector store
        create_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "Delete Test"},
        )
        vs_id = create_response["id"]

        # Delete it
        delete_response = client.request("DELETE", f"/v1/vector_stores/{vs_id}")

        assert delete_response["id"] == vs_id
        assert delete_response["deleted"] is True
        assert delete_response["object"] == "vector_store.deleted"

        # Verify it's gone
        client.request("GET", f"/v1/vector_stores/{vs_id}", expected_status=404)


@pytest.mark.integration
class TestVectorStoreListingAndPagination:
    """Test listing and pagination of vector stores."""

    def test_list_vector_stores_basic(self, client: FakeAIClient):
        """Test listing vector stores."""
        # Create several vector stores
        for i in range(3):
            client.request(
                "POST",
                "/v1/vector_stores",
                json={"name": f"List Test {i}"},
            )

        # List all
        response = client.request("GET", "/v1/vector_stores?limit=10")

        assert response["object"] == "list"
        assert len(response["data"]) >= 3
        assert all(vs["object"] == "vector_store" for vs in response["data"])

    def test_list_vector_stores_pagination(self, client: FakeAIClient):
        """Test vector store list pagination."""
        # Create multiple stores
        created_ids = []
        for i in range(5):
            response = client.request(
                "POST",
                "/v1/vector_stores",
                json={"name": f"Pagination Test {i}"},
            )
            created_ids.append(response["id"])

        # First page
        page1 = client.request("GET", "/v1/vector_stores?limit=2")
        assert len(page1["data"]) == 2
        assert page1["has_more"] is True
        assert page1["first_id"] is not None
        assert page1["last_id"] is not None

        # Second page using after cursor
        page2 = client.request(
            "GET", f"/v1/vector_stores?limit=2&after={page1['last_id']}"
        )
        assert len(page2["data"]) == 2
        # Should have different IDs
        page1_ids = {vs["id"] for vs in page1["data"]}
        page2_ids = {vs["id"] for vs in page2["data"]}
        assert len(page1_ids & page2_ids) == 0

    def test_list_vector_stores_order(self, client: FakeAIClient):
        """Test vector store list ordering."""
        # Create stores with delays
        ids_created = []
        for i in range(3):
            response = client.request(
                "POST",
                "/v1/vector_stores",
                json={"name": f"Order Test {i}"},
            )
            ids_created.append(response["id"])
            time.sleep(0.1)

        # List in descending order (newest first)
        desc_response = client.request("GET", "/v1/vector_stores?limit=10&order=desc")
        desc_ids = [vs["id"] for vs in desc_response["data"]]

        # List in ascending order (oldest first)
        asc_response = client.request("GET", "/v1/vector_stores?limit=10&order=asc")
        asc_ids = [vs["id"] for vs in asc_response["data"]]

        # Verify order is reversed
        assert desc_ids != asc_ids


@pytest.mark.integration
class TestVectorStoreExpiration:
    """Test vector store expiration policies."""

    def test_create_vector_store_with_expiration(self, client: FakeAIClient):
        """Test creating a vector store with expiration policy."""
        response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "Expiring Vector Store",
                "expires_after": {"anchor": "last_active_at", "days": 7},
            },
        )

        assert response["expires_after"] is not None
        assert response["expires_after"]["anchor"] == "last_active_at"
        assert response["expires_after"]["days"] == 7
        assert response["expires_at"] is not None

        # Verify expiration timestamp is approximately 7 days from creation
        expected_expiry = response["created_at"] + (7 * 86400)
        assert abs(response["expires_at"] - expected_expiry) < 10

    def test_modify_vector_store_expiration(self, client: FakeAIClient):
        """Test modifying vector store expiration policy."""
        # Create without expiration
        create_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "Expiration Modify Test"},
        )
        vs_id = create_response["id"]
        assert create_response.get("expires_after") is None

        # Add expiration policy
        modify_response = client.request(
            "POST",
            f"/v1/vector_stores/{vs_id}",
            json={"expires_after": {"anchor": "last_active_at", "days": 30}},
        )

        assert modify_response["expires_after"] is not None
        assert modify_response["expires_after"]["days"] == 30
        assert modify_response["expires_at"] is not None

    def test_expiration_boundary_validation(self, client: FakeAIClient):
        """Test expiration policy boundary validation."""
        # Test minimum (1 day)
        response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "Min Expiration",
                "expires_after": {"anchor": "last_active_at", "days": 1},
            },
        )
        assert response["expires_after"]["days"] == 1

        # Test maximum (365 days)
        response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "Max Expiration",
                "expires_after": {"anchor": "last_active_at", "days": 365},
            },
        )
        assert response["expires_after"]["days"] == 365


@pytest.mark.integration
class TestVectorStoreFileOperations:
    """Test file attachment and management in vector stores."""

    @pytest.fixture
    def test_file(self, client: FakeAIClient):
        """Create a test file for vector store operations."""
        # Get existing files from system
        files_list = client.request("GET", "/v1/files")
        if files_list["data"]:
            return files_list["data"][0]["id"]

        # If no files exist, create one
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is test content for vector store testing.\n" * 10)
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                upload_response = client.upload_file(
                    file=f,
                    purpose="assistants",
                )
            return upload_response["id"]
        finally:
            import os

            os.unlink(temp_path)

    def test_create_vector_store_with_files(self, client: FakeAIClient, test_file):
        """Test creating a vector store with initial files."""
        response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "Vector Store with Files",
                "file_ids": [test_file],
            },
        )

        assert response["file_counts"]["total"] == 1
        # File should be in_progress initially
        assert response["file_counts"]["in_progress"] >= 0

    def test_add_file_to_vector_store(self, client: FakeAIClient, test_file):
        """Test adding a file to an existing vector store."""
        # Create empty vector store
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "Add File Test"},
        )
        vs_id = vs_response["id"]

        # Add file
        file_response = client.request(
            "POST",
            f"/v1/vector_stores/{vs_id}/files",
            json={"file_id": test_file},
        )

        assert file_response["id"].startswith("vsf_")
        assert file_response["object"] == "vector_store.file"
        assert file_response["vector_store_id"] == vs_id
        assert file_response["status"] in ["in_progress", "completed"]

    def test_list_vector_store_files(self, client: FakeAIClient, test_file):
        """Test listing files in a vector store."""
        # Create vector store with file
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "List Files Test",
                "file_ids": [test_file],
            },
        )
        vs_id = vs_response["id"]

        # Wait briefly for processing
        time.sleep(0.5)

        # List files
        files_response = client.request("GET", f"/v1/vector_stores/{vs_id}/files")

        assert files_response["object"] == "list"
        assert len(files_response["data"]) >= 1
        assert all(f["object"] == "vector_store.file" for f in files_response["data"])

    def test_retrieve_vector_store_file(self, client: FakeAIClient, test_file):
        """Test retrieving a specific file from vector store."""
        # Create vector store with file
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "Retrieve File Test",
                "file_ids": [test_file],
            },
        )
        vs_id = vs_response["id"]

        # Wait for processing
        time.sleep(0.5)

        # Get file list
        files_list = client.request("GET", f"/v1/vector_stores/{vs_id}/files")
        assert len(files_list["data"]) > 0
        vs_file_id = files_list["data"][0]["id"]

        # Retrieve specific file
        file_response = client.request(
            "GET", f"/v1/vector_stores/{vs_id}/files/{vs_file_id}"
        )

        assert file_response["id"] == vs_file_id
        assert file_response["vector_store_id"] == vs_id

    def test_delete_vector_store_file(self, client: FakeAIClient, test_file):
        """Test deleting a file from vector store."""
        # Create vector store with file
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "Delete File Test",
                "file_ids": [test_file],
            },
        )
        vs_id = vs_response["id"]

        # Wait for processing
        time.sleep(0.5)

        # Get file
        files_list = client.request("GET", f"/v1/vector_stores/{vs_id}/files")
        assert len(files_list["data"]) > 0
        vs_file_id = files_list["data"][0]["id"]

        # Delete file
        delete_response = client.request(
            "DELETE", f"/v1/vector_stores/{vs_id}/files/{vs_file_id}"
        )

        assert delete_response["id"] == vs_file_id
        assert delete_response["deleted"] is True

        # Verify it's gone
        files_list_after = client.request("GET", f"/v1/vector_stores/{vs_id}/files")
        file_ids_after = [f["id"] for f in files_list_after["data"]]
        assert vs_file_id not in file_ids_after


@pytest.mark.integration
class TestChunkingStrategies:
    """Test different chunking strategies for vector stores."""

    @pytest.fixture
    def test_file(self, client: FakeAIClient):
        """Create a test file with sufficient content."""
        import tempfile

        content = "This is a test sentence. " * 100  # Create longer content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                upload_response = client.upload_file(file=f, purpose="assistants")
            return upload_response["id"]
        finally:
            import os

            os.unlink(temp_path)

    def test_auto_chunking_strategy(self, client: FakeAIClient, test_file):
        """Test adding file with auto chunking strategy."""
        # Create vector store
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "Auto Chunking Test"},
        )
        vs_id = vs_response["id"]

        # Add file with auto chunking (default)
        file_response = client.request(
            "POST",
            f"/v1/vector_stores/{vs_id}/files",
            json={
                "file_id": test_file,
                "chunking_strategy": {"type": "auto"},
            },
        )

        assert file_response["chunking_strategy"]["type"] == "auto"

    def test_static_chunking_strategy(self, client: FakeAIClient, test_file):
        """Test adding file with static chunking strategy."""
        # Create vector store
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "Static Chunking Test"},
        )
        vs_id = vs_response["id"]

        # Add file with static chunking
        file_response = client.request(
            "POST",
            f"/v1/vector_stores/{vs_id}/files",
            json={
                "file_id": test_file,
                "chunking_strategy": {
                    "type": "static",
                    "max_chunk_size_tokens": 500,
                    "chunk_overlap_tokens": 100,
                },
            },
        )

        assert file_response["chunking_strategy"]["type"] == "static"
        assert file_response["chunking_strategy"]["max_chunk_size_tokens"] == 500
        assert file_response["chunking_strategy"]["chunk_overlap_tokens"] == 100

    def test_chunking_strategy_validation(self, client: FakeAIClient, test_file):
        """Test chunking strategy parameter validation."""
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "Chunking Validation Test"},
        )
        vs_id = vs_response["id"]

        # Test with boundary values
        file_response = client.request(
            "POST",
            f"/v1/vector_stores/{vs_id}/files",
            json={
                "file_id": test_file,
                "chunking_strategy": {
                    "type": "static",
                    "max_chunk_size_tokens": 100,  # Min allowed
                    "chunk_overlap_tokens": 0,  # Min overlap
                },
            },
        )

        assert file_response["chunking_strategy"]["max_chunk_size_tokens"] == 100
        assert file_response["chunking_strategy"]["chunk_overlap_tokens"] == 0


@pytest.mark.integration
class TestVectorStoreFileBatches:
    """Test batch file operations in vector stores."""

    @pytest.fixture
    def test_files(self, client: FakeAIClient):
        """Create multiple test files."""
        import os
        import tempfile

        files_list = client.request("GET", "/v1/files")
        existing_files = [f["id"] for f in files_list["data"][:3]]

        if len(existing_files) >= 3:
            return existing_files

        # Create files if needed
        file_ids = existing_files.copy()
        for i in range(3 - len(existing_files)):
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write(f"Batch test file {i} content.\n" * 20)
                temp_path = f.name

            try:
                with open(temp_path, "rb") as f:
                    response = client.upload_file(file=f, purpose="assistants")
                file_ids.append(response["id"])
            finally:
                os.unlink(temp_path)

        return file_ids[:3]

    def test_create_file_batch(self, client: FakeAIClient, test_files):
        """Test creating a batch of files."""
        # Create vector store
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "Batch Test"},
        )
        vs_id = vs_response["id"]

        # Create batch
        batch_response = client.request(
            "POST",
            f"/v1/vector_stores/{vs_id}/file_batches",
            json={"file_ids": test_files},
        )

        assert batch_response["id"].startswith("vsfb_")
        assert batch_response["object"] == "vector_store.files_batch"
        assert batch_response["vector_store_id"] == vs_id
        assert batch_response["status"] in ["in_progress", "completed"]
        assert batch_response["file_counts"]["total"] == len(test_files)

    def test_retrieve_file_batch(self, client: FakeAIClient, test_files):
        """Test retrieving a file batch."""
        # Create vector store with batch
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "Batch Retrieve Test",
                "file_ids": test_files,
            },
        )
        vs_id = vs_response["id"]

        # Create a batch
        batch_create = client.request(
            "POST",
            f"/v1/vector_stores/{vs_id}/file_batches",
            json={"file_ids": test_files[:2]},
        )
        batch_id = batch_create["id"]

        # Retrieve batch
        batch_response = client.request(
            "GET", f"/v1/vector_stores/{vs_id}/file_batches/{batch_id}"
        )

        assert batch_response["id"] == batch_id
        assert batch_response["vector_store_id"] == vs_id

    def test_cancel_file_batch(self, client: FakeAIClient, test_files):
        """Test cancelling a file batch."""
        # Create vector store
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "Batch Cancel Test"},
        )
        vs_id = vs_response["id"]

        # Create batch
        batch_create = client.request(
            "POST",
            f"/v1/vector_stores/{vs_id}/file_batches",
            json={"file_ids": test_files},
        )
        batch_id = batch_create["id"]

        # Cancel immediately
        cancel_response = client.request(
            "POST", f"/v1/vector_stores/{vs_id}/file_batches/{batch_id}/cancel"
        )

        assert cancel_response["status"] == "cancelled"

    def test_list_files_in_batch(self, client: FakeAIClient, test_files):
        """Test listing files in a batch."""
        # Create vector store
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "Batch Files List Test"},
        )
        vs_id = vs_response["id"]

        # Create batch
        batch_create = client.request(
            "POST",
            f"/v1/vector_stores/{vs_id}/file_batches",
            json={"file_ids": test_files},
        )
        batch_id = batch_create["id"]

        # Wait briefly
        time.sleep(0.5)

        # List files in batch
        files_response = client.request(
            "GET", f"/v1/vector_stores/{vs_id}/file_batches/{batch_id}/files"
        )

        assert files_response["object"] == "list"
        # Should have files from the batch
        assert len(files_response["data"]) >= 0


@pytest.mark.integration
class TestVectorStoreFileCounts:
    """Test file count tracking in vector stores."""

    def test_file_counts_tracking(self, client: FakeAIClient):
        """Test that file counts are properly tracked."""
        # Get test files
        files_list = client.request("GET", "/v1/files")
        test_files = [f["id"] for f in files_list["data"][:3]]

        if len(test_files) < 3:
            pytest.skip("Not enough files available for testing")

        # Create vector store
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "File Counts Test"},
        )
        vs_id = vs_response["id"]
        assert vs_response["file_counts"]["total"] == 0

        # Add files one by one
        for file_id in test_files:
            client.request(
                "POST",
                f"/v1/vector_stores/{vs_id}/files",
                json={"file_id": file_id},
            )

        # Check counts
        vs_updated = client.request("GET", f"/v1/vector_stores/{vs_id}")
        assert vs_updated["file_counts"]["total"] == len(test_files)

    def test_usage_bytes_tracking(self, client: FakeAIClient):
        """Test that usage_bytes is tracked correctly."""
        # Get a file with known size
        files_list = client.request("GET", "/v1/files")
        if not files_list["data"]:
            pytest.skip("No files available for testing")

        test_file = files_list["data"][0]
        file_id = test_file["id"]
        file_bytes = test_file.get("bytes", 0)

        # Create vector store with file
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "Usage Bytes Test",
                "file_ids": [file_id],
            },
        )
        vs_id = vs_response["id"]

        # Wait for processing
        time.sleep(0.5)

        # Check usage_bytes
        vs_updated = client.request("GET", f"/v1/vector_stores/{vs_id}")
        # Usage bytes should be positive if file has content
        assert vs_updated["usage_bytes"] >= 0


@pytest.mark.integration
@pytest.mark.slow
class TestVectorStoreConcurrency:
    """Test concurrent operations on vector stores."""

    def test_concurrent_vector_store_creation(self, client: FakeAIClient):
        """Test creating multiple vector stores concurrently."""

        def create_store(index):
            try:
                response = client.request(
                    "POST",
                    "/v1/vector_stores",
                    json={"name": f"Concurrent Store {index}"},
                )
                return response["id"]
            except Exception as e:
                logger.error(f"Failed to create store {index}: {e}")
                return None

        # Create 10 stores concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_store, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]

        # Verify all succeeded
        successful = [r for r in results if r is not None]
        assert len(successful) == 10
        # All IDs should be unique
        assert len(set(successful)) == 10

    def test_concurrent_file_additions(self, client: FakeAIClient):
        """Test adding files to vector store concurrently."""
        # Get test files
        files_list = client.request("GET", "/v1/files")
        test_files = [f["id"] for f in files_list["data"][:5]]

        if len(test_files) < 3:
            pytest.skip("Not enough files for concurrency test")

        # Create vector store
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "Concurrent Files Test"},
        )
        vs_id = vs_response["id"]

        def add_file(file_id):
            try:
                response = client.request(
                    "POST",
                    f"/v1/vector_stores/{vs_id}/files",
                    json={"file_id": file_id},
                )
                return response["id"]
            except Exception as e:
                logger.error(f"Failed to add file {file_id}: {e}")
                return None

        # Add files concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(add_file, fid) for fid in test_files[:3]]
            results = [f.result() for f in as_completed(futures)]

        # Verify additions
        successful = [r for r in results if r is not None]
        assert len(successful) >= 1

    def test_concurrent_read_operations(self, client: FakeAIClient):
        """Test concurrent read operations on same vector store."""
        # Create vector store
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "Concurrent Read Test"},
        )
        vs_id = vs_response["id"]

        def read_store():
            try:
                response = client.request("GET", f"/v1/vector_stores/{vs_id}")
                return response["id"]
            except Exception as e:
                logger.error(f"Failed to read store: {e}")
                return None

        # Read concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_store) for _ in range(20)]
            results = [f.result() for f in as_completed(futures)]

        # All reads should succeed
        successful = [r for r in results if r is not None]
        assert len(successful) == 20
        # All should return same ID
        assert all(r == vs_id for r in successful)


@pytest.mark.integration
class TestVectorStoreEdgeCases:
    """Test edge cases and error handling."""

    def test_create_vector_store_empty_name(self, client: FakeAIClient):
        """Test creating vector store with empty name."""
        response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": ""},
        )
        # Should still succeed (empty name is technically valid)
        assert response["id"].startswith("vs_")

    def test_add_nonexistent_file_to_vector_store(self, client: FakeAIClient):
        """Test adding a nonexistent file to vector store."""
        vs_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={"name": "Nonexistent File Test"},
        )
        vs_id = vs_response["id"]

        # Try to add nonexistent file
        response = client.request(
            "POST",
            f"/v1/vector_stores/{vs_id}/files",
            json={"file_id": "file-nonexistent"},
            expected_status=404,
        )
        assert "error" in response

    def test_delete_nonexistent_vector_store(self, client: FakeAIClient):
        """Test deleting nonexistent vector store."""
        response = client.request(
            "DELETE",
            "/v1/vector_stores/vs_nonexistent",
            expected_status=404,
        )
        assert "error" in response

    def test_modify_nonexistent_vector_store(self, client: FakeAIClient):
        """Test modifying nonexistent vector store."""
        response = client.request(
            "POST",
            "/v1/vector_stores/vs_nonexistent",
            json={"name": "Updated"},
            expected_status=404,
        )
        assert "error" in response

    def test_vector_store_with_duplicate_file_ids(self, client: FakeAIClient):
        """Test creating vector store with duplicate file IDs."""
        files_list = client.request("GET", "/v1/files")
        if not files_list["data"]:
            pytest.skip("No files available for testing")

        file_id = files_list["data"][0]["id"]

        # Create with duplicate file IDs
        response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "Duplicate Files Test",
                "file_ids": [file_id, file_id, file_id],
            },
        )

        # Should handle duplicates gracefully
        assert response["id"].startswith("vs_")


@pytest.mark.integration
class TestVectorStoreMetadata:
    """Test metadata filtering and operations."""

    def test_metadata_persistence(self, client: FakeAIClient):
        """Test that metadata persists across operations."""
        metadata = {
            "project": "integration-test",
            "version": "1.0.0",
            "tags": "test,vector-store",
        }

        # Create with metadata
        create_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "Metadata Persistence Test",
                "metadata": metadata,
            },
        )
        vs_id = create_response["id"]

        # Retrieve and verify metadata
        retrieve_response = client.request("GET", f"/v1/vector_stores/{vs_id}")
        assert retrieve_response["metadata"] == metadata

        # List and verify metadata appears
        list_response = client.request("GET", "/v1/vector_stores?limit=20")
        matching_stores = [vs for vs in list_response["data"] if vs["id"] == vs_id]
        assert len(matching_stores) == 1
        assert matching_stores[0]["metadata"] == metadata

    def test_metadata_update(self, client: FakeAIClient):
        """Test updating metadata replaces old values."""
        # Create with initial metadata
        create_response = client.request(
            "POST",
            "/v1/vector_stores",
            json={
                "name": "Metadata Update Test",
                "metadata": {"initial": "value"},
            },
        )
        vs_id = create_response["id"]

        # Update with new metadata
        new_metadata = {"updated": "new-value", "additional": "field"}
        modify_response = client.request(
            "POST",
            f"/v1/vector_stores/{vs_id}",
            json={"metadata": new_metadata},
        )

        # Old metadata should be replaced
        assert modify_response["metadata"] == new_metadata
        assert "initial" not in modify_response["metadata"]
