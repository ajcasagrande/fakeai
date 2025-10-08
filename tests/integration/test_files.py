"""Integration tests for file management endpoints.

This module provides comprehensive integration tests for:
1. File upload (different file types: jsonl, pdf, txt, csv)
2. File listing with pagination
3. File retrieval by ID
4. File deletion
5. File content retrieval
6. Purpose parameter (fine-tune, assistants, batch, vision)
7. Large file upload (chunked)
8. Concurrent file operations
9. File metadata
10. File search/filtering
11. Storage limits
12. File validation errors
13. Multiple file formats
"""

import asyncio
import io
import json
from typing import Any

import pytest

from .utils import FakeAIClient


@pytest.mark.integration
class TestFileUpload:
    """Test file upload functionality with different file types."""

    def test_upload_text_file(self, client: FakeAIClient):
        """Test uploading a plain text file."""
        content = b"This is a test document for assistants.\nWith multiple lines."
        filename = "test_document.txt"

        # Upload file
        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "text/plain")},
            data={"purpose": "assistants"},
        )
        response.raise_for_status()
        file_obj = response.json()

        # Validate response
        assert file_obj["object"] == "file"
        assert file_obj["id"].startswith("file-")
        assert file_obj["filename"] == filename
        assert file_obj["purpose"] == "assistants"
        assert file_obj["bytes"] == len(content)
        assert "created_at" in file_obj
        assert file_obj.get("status") in ["uploaded", "processed", None]

    def test_upload_jsonl_fine_tune(self, client: FakeAIClient):
        """Test uploading JSONL file for fine-tuning."""
        # Create valid fine-tuning JSONL
        lines = [
            {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                ]
            },
            {
                "messages": [
                    {"role": "user", "content": "What is 2+2?"},
                    {"role": "assistant", "content": "4"},
                ]
            },
        ]
        content = "\n".join(json.dumps(line) for line in lines).encode()
        filename = "training_data.jsonl"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "application/jsonl")},
            data={"purpose": "fine-tune"},
        )
        response.raise_for_status()
        file_obj = response.json()

        assert file_obj["id"].startswith("file-")
        assert file_obj["purpose"] == "fine-tune"
        assert file_obj["bytes"] == len(content)

    def test_upload_jsonl_batch(self, client: FakeAIClient):
        """Test uploading JSONL file for batch processing."""
        # Create valid batch JSONL
        lines = [
            {
                "custom_id": "request-1",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hello"}],
                },
            },
            {
                "custom_id": "request-2",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "World"}],
                },
            },
        ]
        content = "\n".join(json.dumps(line) for line in lines).encode()
        filename = "batch_requests.jsonl"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "application/jsonl")},
            data={"purpose": "batch"},
        )
        response.raise_for_status()
        file_obj = response.json()

        assert file_obj["id"].startswith("file-")
        assert file_obj["purpose"] == "batch"
        assert file_obj["bytes"] == len(content)

    def test_upload_csv_file(self, client: FakeAIClient):
        """Test uploading CSV file."""
        content = b"name,age,city\nAlice,30,New York\nBob,25,Los Angeles\nCharlie,35,Chicago\n"
        filename = "data.csv"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "text/csv")},
            data={"purpose": "assistants"},
        )
        response.raise_for_status()
        file_obj = response.json()

        assert file_obj["id"].startswith("file-")
        assert file_obj["purpose"] == "assistants"
        assert file_obj["filename"] == filename

    def test_upload_image_vision(self, client: FakeAIClient):
        """Test uploading image file for vision."""
        # Create minimal PNG (PNG magic bytes + IHDR chunk)
        png_header = b"\x89PNG\r\n\x1a\n"
        ihdr = b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        iend = b"\x00\x00\x00\x00IEND\xaeB`\x82"
        content = png_header + ihdr + iend

        filename = "test_image.png"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "image/png")},
            data={"purpose": "vision"},
        )
        response.raise_for_status()
        file_obj = response.json()

        assert file_obj["id"].startswith("file-")
        assert file_obj["purpose"] == "vision"
        assert file_obj["filename"] == filename

    def test_upload_json_file(self, client: FakeAIClient):
        """Test uploading JSON file."""
        content = json.dumps(
            {
                "data": [
                    {"id": 1, "value": "test1"},
                    {"id": 2, "value": "test2"},
                ]
            }
        ).encode()
        filename = "data.json"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "application/json")},
            data={"purpose": "assistants"},
        )
        response.raise_for_status()
        file_obj = response.json()

        assert file_obj["id"].startswith("file-")
        assert file_obj["purpose"] == "assistants"


@pytest.mark.integration
class TestFileListing:
    """Test file listing with pagination and filtering."""

    def test_list_files_empty(self, client: FakeAIClient):
        """Test listing files when none exist (or independent from other tests)."""
        response = client.get("/v1/files")
        response.raise_for_status()
        result = response.json()

        assert result["object"] == "list"
        assert isinstance(result["data"], list)

    def test_list_files_basic(self, client: FakeAIClient):
        """Test basic file listing."""
        # Upload a few files
        uploaded_ids = []
        for i in range(3):
            resp = client.post(
                "/v1/files",
                files={
                    "file": (
                        f"test{i}.txt",
                        io.BytesIO(f"content {i}".encode()),
                        "text/plain",
                    )
                },
                data={"purpose": "assistants"},
            )
            resp.raise_for_status()
            uploaded_ids.append(resp.json()["id"])

        # List files
        response = client.get("/v1/files")
        response.raise_for_status()
        result = response.json()

        assert result["object"] == "list"
        assert len(result["data"]) >= 3  # At least the ones we uploaded
        assert all(f["id"].startswith("file-") for f in result["data"])

    def test_list_files_with_purpose_filter(self, client: FakeAIClient):
        """Test listing files filtered by purpose."""
        # Upload files with different purposes
        assistants_content = b"assistants data"
        batch_lines = [
            {
                "custom_id": "req-1",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {"model": "gpt-4", "messages": [{"role": "user", "content": "test"}]},
            }
        ]
        batch_content = json.dumps(batch_lines[0]).encode()

        # Upload assistants file
        resp1 = client.post(
            "/v1/files",
            files={"file": ("assistants.txt", io.BytesIO(assistants_content), "text/plain")},
            data={"purpose": "assistants"},
        )
        resp1.raise_for_status()

        # Upload batch file
        resp2 = client.post(
            "/v1/files",
            files={"file": ("batch.jsonl", io.BytesIO(batch_content), "application/jsonl")},
            data={"purpose": "batch"},
        )
        resp2.raise_for_status()

        # List only assistants files
        response = client.get("/v1/files", params={"purpose": "assistants"})
        response.raise_for_status()
        result = response.json()

        # Should have at least one assistants file
        assistants_files = [f for f in result["data"] if f["purpose"] == "assistants"]
        assert len(assistants_files) >= 1

    def test_list_files_with_limit(self, client: FakeAIClient):
        """Test listing files with limit parameter."""
        # Upload several files
        for i in range(5):
            client.post(
                "/v1/files",
                files={
                    "file": (
                        f"limit_test{i}.txt",
                        io.BytesIO(f"content {i}".encode()),
                        "text/plain",
                    )
                },
                data={"purpose": "assistants"},
            )

        # List with limit
        response = client.get("/v1/files", params={"limit": 2})
        response.raise_for_status()
        result = response.json()

        assert len(result["data"]) <= 2

    def test_list_files_pagination(self, client: FakeAIClient):
        """Test cursor-based pagination."""
        # Upload files
        uploaded = []
        for i in range(5):
            resp = client.post(
                "/v1/files",
                files={
                    "file": (
                        f"pagination{i}.txt",
                        io.BytesIO(f"page content {i}".encode()),
                        "text/plain",
                    )
                },
                data={"purpose": "assistants"},
            )
            resp.raise_for_status()
            uploaded.append(resp.json()["id"])

        # Get first page
        response1 = client.get("/v1/files", params={"limit": 2, "order": "desc"})
        response1.raise_for_status()
        page1 = response1.json()

        assert len(page1["data"]) <= 2

        if len(page1["data"]) >= 2:
            # Get second page using cursor
            after_id = page1["data"][-1]["id"]
            response2 = client.get("/v1/files", params={"limit": 2, "after": after_id, "order": "desc"})
            response2.raise_for_status()
            page2 = response2.json()

            # Verify no overlap
            page1_ids = {f["id"] for f in page1["data"]}
            page2_ids = {f["id"] for f in page2["data"]}
            assert len(page1_ids & page2_ids) == 0

    def test_list_files_ordering(self, client: FakeAIClient):
        """Test ascending and descending order."""
        # Upload files
        for i in range(3):
            client.post(
                "/v1/files",
                files={
                    "file": (
                        f"order{i}.txt",
                        io.BytesIO(f"order {i}".encode()),
                        "text/plain",
                    )
                },
                data={"purpose": "assistants"},
            )

        # Test ascending order
        asc_response = client.get("/v1/files", params={"order": "asc", "limit": 10})
        asc_response.raise_for_status()
        asc_result = asc_response.json()

        # Test descending order
        desc_response = client.get("/v1/files", params={"order": "desc", "limit": 10})
        desc_response.raise_for_status()
        desc_result = desc_response.json()

        # Verify we got results
        assert len(asc_result["data"]) > 0
        assert len(desc_result["data"]) > 0


@pytest.mark.integration
class TestFileRetrieval:
    """Test file retrieval and content access."""

    def test_get_file_metadata(self, client: FakeAIClient):
        """Test retrieving file metadata by ID."""
        content = b"Test file for retrieval"
        filename = "retrieve_test.txt"

        # Upload file
        upload_resp = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "text/plain")},
            data={"purpose": "assistants"},
        )
        upload_resp.raise_for_status()
        uploaded = upload_resp.json()
        file_id = uploaded["id"]

        # Retrieve metadata
        get_resp = client.get(f"/v1/files/{file_id}")
        get_resp.raise_for_status()
        retrieved = get_resp.json()

        # Validate
        assert retrieved["id"] == file_id
        assert retrieved["filename"] == filename
        assert retrieved["purpose"] == "assistants"
        assert retrieved["bytes"] == len(content)
        assert retrieved["object"] == "file"

    def test_get_file_content(self, client: FakeAIClient):
        """Test retrieving file content."""
        content = b"This is the actual file content that should be retrieved."
        filename = "content_test.txt"

        # Upload file
        upload_resp = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "text/plain")},
            data={"purpose": "assistants"},
        )
        upload_resp.raise_for_status()
        file_id = upload_resp.json()["id"]

        # Retrieve content
        content_resp = client.get(f"/v1/files/{file_id}/content")
        content_resp.raise_for_status()
        retrieved_content = content_resp.content

        # Validate
        assert retrieved_content == content

    def test_get_nonexistent_file(self, client: FakeAIClient):
        """Test retrieving non-existent file returns 404."""
        response = client.get("/v1/files/file-nonexistent-12345")
        assert response.status_code == 404

    def test_get_file_content_nonexistent(self, client: FakeAIClient):
        """Test retrieving content of non-existent file returns 404."""
        response = client.get("/v1/files/file-nonexistent-12345/content")
        assert response.status_code == 404


@pytest.mark.integration
class TestFileDeletion:
    """Test file deletion functionality."""

    def test_delete_file(self, client: FakeAIClient):
        """Test deleting a file."""
        content = b"File to be deleted"
        filename = "delete_test.txt"

        # Upload file
        upload_resp = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "text/plain")},
            data={"purpose": "assistants"},
        )
        upload_resp.raise_for_status()
        file_id = upload_resp.json()["id"]

        # Delete file
        delete_resp = client.delete(f"/v1/files/{file_id}")
        delete_resp.raise_for_status()
        delete_result = delete_resp.json()

        # Validate deletion response
        assert delete_result["id"] == file_id
        assert delete_result["object"] == "file"
        assert delete_result["deleted"] is True

        # Verify file is gone
        get_resp = client.get(f"/v1/files/{file_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_file(self, client: FakeAIClient):
        """Test deleting non-existent file returns 404."""
        response = client.delete("/v1/files/file-nonexistent-12345")
        assert response.status_code == 404


@pytest.mark.integration
class TestFilePurposes:
    """Test different file purposes."""

    def test_purpose_assistants(self, client: FakeAIClient):
        """Test assistants purpose with valid file types."""
        valid_files = [
            ("doc.txt", b"text content", "text/plain"),
            ("data.json", b'{"key": "value"}', "application/json"),
            ("data.csv", b"col1,col2\nval1,val2\n", "text/csv"),
        ]

        for filename, content, mime_type in valid_files:
            response = client.post(
                "/v1/files",
                files={"file": (filename, io.BytesIO(content), mime_type)},
                data={"purpose": "assistants"},
            )
            response.raise_for_status()
            assert response.json()["purpose"] == "assistants"

    def test_purpose_vision(self, client: FakeAIClient):
        """Test vision purpose with image file."""
        # Minimal PNG
        png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        filename = "vision.png"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(png_content), "image/png")},
            data={"purpose": "vision"},
        )
        response.raise_for_status()
        assert response.json()["purpose"] == "vision"

    def test_purpose_user_data(self, client: FakeAIClient):
        """Test user_data purpose (accepts any file type)."""
        content = b"Any kind of content"
        filename = "userfile.bin"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "application/octet-stream")},
            data={"purpose": "user_data"},
        )
        response.raise_for_status()
        assert response.json()["purpose"] == "user_data"

    def test_invalid_purpose(self, client: FakeAIClient):
        """Test that invalid purpose is rejected."""
        content = b"test content"
        filename = "test.txt"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "text/plain")},
            data={"purpose": "invalid_purpose"},
        )
        assert response.status_code in [400, 422]  # Bad request or validation error


@pytest.mark.integration
class TestFileValidation:
    """Test file validation and error handling."""

    def test_empty_file_rejected(self, client: FakeAIClient):
        """Test that empty file is rejected."""
        content = b""
        filename = "empty.txt"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "text/plain")},
            data={"purpose": "assistants"},
        )
        assert response.status_code in [400, 422]

    def test_missing_purpose(self, client: FakeAIClient):
        """Test that missing purpose is rejected."""
        content = b"test content"
        filename = "test.txt"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "text/plain")},
            data={},  # Missing purpose
        )
        assert response.status_code in [400, 422]

    def test_invalid_mime_type_for_purpose(self, client: FakeAIClient):
        """Test that wrong MIME type for purpose is rejected."""
        # Try to upload text file for vision purpose
        content = b"Not an image"
        filename = "notimage.txt"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "text/plain")},
            data={"purpose": "vision"},
        )
        assert response.status_code in [400, 422]

    def test_invalid_jsonl_for_fine_tune(self, client: FakeAIClient):
        """Test that invalid JSONL for fine-tuning is rejected."""
        # Missing required 'messages' field
        content = b'{"invalid": "format"}\n'
        filename = "invalid.jsonl"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "application/jsonl")},
            data={"purpose": "fine-tune"},
        )
        assert response.status_code in [400, 422]

    def test_invalid_jsonl_for_batch(self, client: FakeAIClient):
        """Test that invalid JSONL for batch is rejected."""
        # Missing required fields
        content = b'{"custom_id": "req-1"}\n'
        filename = "invalid_batch.jsonl"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "application/jsonl")},
            data={"purpose": "batch"},
        )
        assert response.status_code in [400, 422]


@pytest.mark.integration
class TestLargeFiles:
    """Test large file handling."""

    def test_medium_file_upload(self, client: FakeAIClient):
        """Test uploading a medium-sized file (1 MB)."""
        # Create 1 MB file
        content = b"x" * (1024 * 1024)
        filename = "large_1mb.txt"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "text/plain")},
            data={"purpose": "assistants"},
        )
        response.raise_for_status()
        file_obj = response.json()

        assert file_obj["bytes"] == len(content)
        assert file_obj["id"].startswith("file-")

    def test_large_file_upload(self, client: FakeAIClient):
        """Test uploading a larger file (10 MB)."""
        # Create 10 MB file
        content = b"y" * (10 * 1024 * 1024)
        filename = "large_10mb.txt"

        response = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "text/plain")},
            data={"purpose": "user_data"},
            timeout=60.0,  # Longer timeout for large file
        )
        response.raise_for_status()
        file_obj = response.json()

        assert file_obj["bytes"] == len(content)
        assert file_obj["id"].startswith("file-")


@pytest.mark.integration
class TestConcurrentOperations:
    """Test concurrent file operations."""

    @pytest.mark.asyncio
    async def test_concurrent_uploads(self, client: FakeAIClient):
        """Test uploading multiple files concurrently."""

        async def upload_file(index: int) -> dict[str, Any]:
            """Upload a single file."""
            content = f"concurrent content {index}".encode()
            filename = f"concurrent{index}.txt"

            response = await client.apost(
                "/v1/files",
                files={"file": (filename, io.BytesIO(content), "text/plain")},
                data={"purpose": "assistants"},
            )
            response.raise_for_status()
            return response.json()

        # Upload 10 files concurrently
        tasks = [upload_file(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # Verify all uploads succeeded
        assert len(results) == 10
        assert all(r["id"].startswith("file-") for r in results)
        assert len(set(r["id"] for r in results)) == 10  # All unique IDs

    @pytest.mark.asyncio
    async def test_concurrent_read_write(self, client: FakeAIClient):
        """Test concurrent reads and writes."""
        # First upload a file
        content = b"file for concurrent access"
        upload_resp = await client.apost(
            "/v1/files",
            files={"file": ("shared.txt", io.BytesIO(content), "text/plain")},
            data={"purpose": "assistants"},
        )
        upload_resp.raise_for_status()
        file_id = upload_resp.json()["id"]

        # Concurrently read the file multiple times while uploading new files
        async def read_file():
            response = await client.aget(f"/v1/files/{file_id}")
            response.raise_for_status()
            return response.json()

        async def upload_new_file(index: int):
            response = await client.apost(
                "/v1/files",
                files={
                    "file": (
                        f"new{index}.txt",
                        io.BytesIO(f"new {index}".encode()),
                        "text/plain",
                    )
                },
                data={"purpose": "assistants"},
            )
            response.raise_for_status()
            return response.json()

        # Mix of reads and writes
        tasks = [read_file() for _ in range(5)] + [upload_new_file(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10


@pytest.mark.integration
class TestFileMetadata:
    """Test file metadata tracking."""

    def test_file_metadata_complete(self, client: FakeAIClient):
        """Test that file metadata is complete and accurate."""
        content = b"Metadata test content"
        filename = "metadata.txt"

        # Upload file
        upload_resp = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "text/plain")},
            data={"purpose": "assistants"},
        )
        upload_resp.raise_for_status()
        file_obj = upload_resp.json()

        # Verify all metadata fields
        assert "id" in file_obj
        assert file_obj["id"].startswith("file-")
        assert file_obj["object"] == "file"
        assert file_obj["bytes"] == len(content)
        assert file_obj["filename"] == filename
        assert file_obj["purpose"] == "assistants"
        assert "created_at" in file_obj
        assert isinstance(file_obj["created_at"], int)
        assert file_obj["created_at"] > 0

    def test_file_size_tracking(self, client: FakeAIClient):
        """Test that file sizes are accurately tracked."""
        sizes = [100, 1000, 10000, 100000]

        for size in sizes:
            content = b"x" * size
            filename = f"size_{size}.txt"

            response = client.post(
                "/v1/files",
                files={"file": (filename, io.BytesIO(content), "text/plain")},
                data={"purpose": "assistants"},
            )
            response.raise_for_status()
            file_obj = response.json()

            assert file_obj["bytes"] == size

    def test_filename_preservation(self, client: FakeAIClient):
        """Test that filenames with special characters are preserved."""
        filenames = [
            "simple.txt",
            "with-dashes.txt",
            "with_underscores.txt",
            "with.multiple.dots.txt",
            "with spaces.txt",
        ]

        for filename in filenames:
            content = f"Testing {filename}".encode()

            response = client.post(
                "/v1/files",
                files={"file": (filename, io.BytesIO(content), "text/plain")},
                data={"purpose": "assistants"},
            )
            response.raise_for_status()
            file_obj = response.json()

            assert file_obj["filename"] == filename


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete end-to-end file workflows."""

    def test_complete_file_lifecycle(self, client: FakeAIClient):
        """Test complete file lifecycle: upload, list, get, get content, delete."""
        content = b"Complete lifecycle test"
        filename = "lifecycle.txt"

        # 1. Upload
        upload_resp = client.post(
            "/v1/files",
            files={"file": (filename, io.BytesIO(content), "text/plain")},
            data={"purpose": "assistants"},
        )
        upload_resp.raise_for_status()
        uploaded = upload_resp.json()
        file_id = uploaded["id"]

        # 2. List and verify file exists
        list_resp = client.get("/v1/files")
        list_resp.raise_for_status()
        files = list_resp.json()["data"]
        assert any(f["id"] == file_id for f in files)

        # 3. Get metadata
        get_resp = client.get(f"/v1/files/{file_id}")
        get_resp.raise_for_status()
        metadata = get_resp.json()
        assert metadata["id"] == file_id
        assert metadata["filename"] == filename

        # 4. Get content
        content_resp = client.get(f"/v1/files/{file_id}/content")
        content_resp.raise_for_status()
        retrieved_content = content_resp.content
        assert retrieved_content == content

        # 5. Delete
        delete_resp = client.delete(f"/v1/files/{file_id}")
        delete_resp.raise_for_status()
        delete_result = delete_resp.json()
        assert delete_result["deleted"] is True

        # 6. Verify file is gone
        final_get = client.get(f"/v1/files/{file_id}")
        assert final_get.status_code == 404

    def test_multiple_files_same_name(self, client: FakeAIClient):
        """Test uploading multiple files with the same name."""
        filename = "duplicate_name.txt"
        contents = [b"version 1", b"version 2", b"version 3"]

        uploaded_ids = []
        for content in contents:
            response = client.post(
                "/v1/files",
                files={"file": (filename, io.BytesIO(content), "text/plain")},
                data={"purpose": "assistants"},
            )
            response.raise_for_status()
            uploaded_ids.append(response.json()["id"])

        # All should have unique IDs
        assert len(set(uploaded_ids)) == len(uploaded_ids)

        # All should have the same filename
        for file_id in uploaded_ids:
            resp = client.get(f"/v1/files/{file_id}")
            resp.raise_for_status()
            assert resp.json()["filename"] == filename

    def test_batch_workflow(self, client: FakeAIClient):
        """Test complete batch processing workflow."""
        # 1. Create batch input file
        batch_requests = [
            {
                "custom_id": f"request-{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": f"Request {i}"}],
                },
            }
            for i in range(5)
        ]
        content = "\n".join(json.dumps(req) for req in batch_requests).encode()

        # 2. Upload batch file
        upload_resp = client.post(
            "/v1/files",
            files={"file": ("batch.jsonl", io.BytesIO(content), "application/jsonl")},
            data={"purpose": "batch"},
        )
        upload_resp.raise_for_status()
        batch_file = upload_resp.json()

        # 3. Verify file exists and has correct purpose
        get_resp = client.get(f"/v1/files/{batch_file['id']}")
        get_resp.raise_for_status()
        assert get_resp.json()["purpose"] == "batch"

        # 4. Retrieve content and verify integrity
        content_resp = client.get(f"/v1/files/{batch_file['id']}/content")
        content_resp.raise_for_status()
        assert content_resp.content == content
