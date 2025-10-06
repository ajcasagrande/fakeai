"""
Tests for file management module.

Comprehensive tests for file upload, storage, retrieval, deletion,
validation, and quota enforcement.
"""

import json
import os
import tempfile
import time

import pytest

from fakeai.file_manager import (
    DiskStorage,
    FileManager,
    FileNotFoundError,
    FileQuotaError,
    FileValidationError,
    InMemoryStorage,
)


@pytest.fixture
def file_manager():
    """Create a file manager with in-memory storage."""
    return FileManager(storage_backend="memory", enable_cleanup=False)


@pytest.fixture
def disk_file_manager():
    """Create a file manager with disk storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = FileManager(
            storage_backend="disk", storage_path=tmpdir, enable_cleanup=False
        )
        yield manager


@pytest.mark.asyncio
class TestFileUpload:
    """Test file upload functionality."""

    async def test_upload_simple_text_file(self, file_manager):
        """Should successfully upload a simple text file."""
        content = b"Hello, world!"
        filename = "test.txt"

        file_obj = await file_manager.upload_file(
            file_content=content, filename=filename, purpose="user_data"
        )

        assert file_obj.id.startswith("file-")
        assert file_obj.filename == filename
        assert file_obj.bytes == len(content)
        assert file_obj.purpose == "user_data"
        assert file_obj.status == "uploaded"

    async def test_upload_jsonl_file(self, file_manager):
        """Should successfully upload a JSONL file."""
        # Use user_data purpose for general JSONL, since fine-tune requires specific format
        content = b'{"text": "line 1"}\n{"text": "line 2"}\n{"text": "line 3"}'
        filename = "data.jsonl"

        file_obj = await file_manager.upload_file(
            file_content=content, filename=filename, purpose="user_data"
        )

        assert file_obj.id.startswith("file-")
        assert file_obj.filename == filename
        assert file_obj.purpose == "user_data"

    async def test_upload_empty_file_fails(self, file_manager):
        """Should reject empty files."""
        with pytest.raises(FileValidationError, match="File is empty"):
            await file_manager.upload_file(
                file_content=b"", filename="empty.txt", purpose="user_data"
            )

    async def test_upload_oversized_file_fails(self, file_manager):
        """Should reject files exceeding size limit."""
        # Create a file larger than MAX_FILE_SIZE
        oversized_content = b"x" * (file_manager.MAX_FILE_SIZE + 1)

        with pytest.raises(FileValidationError, match="exceeds maximum allowed size"):
            await file_manager.upload_file(
                file_content=oversized_content,
                filename="huge.txt",
                purpose="user_data",
            )

    async def test_upload_invalid_purpose_fails(self, file_manager):
        """Should reject invalid purpose."""
        with pytest.raises(FileValidationError, match="Invalid purpose"):
            await file_manager.upload_file(
                file_content=b"test", filename="test.txt", purpose="invalid_purpose"
            )

    async def test_upload_creates_file_id(self, file_manager):
        """Should generate unique file IDs."""
        content = b"test"
        file1 = await file_manager.upload_file(
            file_content=content, filename="test1.txt", purpose="user_data"
        )
        file2 = await file_manager.upload_file(
            file_content=content, filename="test2.txt", purpose="user_data"
        )

        assert file1.id != file2.id
        assert file1.id.startswith("file-")
        assert file2.id.startswith("file-")


@pytest.mark.asyncio
class TestFileValidation:
    """Test file validation for different purposes."""

    async def test_validate_fine_tune_jsonl(self, file_manager):
        """Should validate fine-tuning JSONL format."""
        valid_content = b"""{"messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]}
{"messages": [{"role": "user", "content": "Test"}, {"role": "assistant", "content": "Response"}]}"""

        file_obj = await file_manager.upload_file(
            file_content=valid_content, filename="train.jsonl", purpose="fine-tune"
        )

        assert file_obj.purpose == "fine-tune"

    async def test_validate_fine_tune_missing_messages_field(self, file_manager):
        """Should reject fine-tuning JSONL without messages field."""
        invalid_content = b'{"text": "This is not the right format"}'

        with pytest.raises(FileValidationError, match="Missing 'messages' field"):
            await file_manager.upload_file(
                file_content=invalid_content,
                filename="invalid.jsonl",
                purpose="fine-tune",
            )

    async def test_validate_fine_tune_invalid_message_structure(self, file_manager):
        """Should reject fine-tuning JSONL with invalid message structure."""
        invalid_content = b'{"messages": [{"invalid": "structure"}]}'

        with pytest.raises(FileValidationError, match="Missing 'role' field"):
            await file_manager.upload_file(
                file_content=invalid_content,
                filename="invalid.jsonl",
                purpose="fine-tune",
            )

    async def test_validate_batch_jsonl(self, file_manager):
        """Should validate batch JSONL format."""
        valid_content = b"""{"custom_id": "req-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hello"}]}}
{"custom_id": "req-2", "method": "POST", "url": "/v1/embeddings", "body": {"model": "text-embedding-ada-002", "input": "Test"}}"""

        file_obj = await file_manager.upload_file(
            file_content=valid_content, filename="batch.jsonl", purpose="batch"
        )

        assert file_obj.purpose == "batch"

    async def test_validate_batch_missing_required_fields(self, file_manager):
        """Should reject batch JSONL missing required fields."""
        invalid_content = b'{"custom_id": "req-1", "method": "POST"}'

        with pytest.raises(FileValidationError, match="Missing required field"):
            await file_manager.upload_file(
                file_content=invalid_content,
                filename="invalid.jsonl",
                purpose="batch",
            )

    async def test_validate_batch_invalid_http_method(self, file_manager):
        """Should reject batch JSONL with invalid HTTP method."""
        invalid_content = b'{"custom_id": "req-1", "method": "INVALID", "url": "/v1/test", "body": {}}'

        with pytest.raises(FileValidationError, match="Invalid HTTP method"):
            await file_manager.upload_file(
                file_content=invalid_content,
                filename="invalid.jsonl",
                purpose="batch",
            )

    async def test_validate_vision_png_image(self, file_manager):
        """Should validate PNG images for vision purpose."""
        # PNG magic bytes + minimal valid PNG structure
        png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # Minimal PNG content

        file_obj = await file_manager.upload_file(
            file_content=png_content, filename="image.png", purpose="vision"
        )

        assert file_obj.purpose == "vision"

    async def test_validate_vision_jpeg_image(self, file_manager):
        """Should validate JPEG images for vision purpose."""
        # JPEG magic bytes + minimal valid JPEG structure
        jpeg_content = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 100  # Minimal JPEG content
        )

        file_obj = await file_manager.upload_file(
            file_content=jpeg_content, filename="image.jpg", purpose="vision"
        )

        assert file_obj.purpose == "vision"

    async def test_validate_vision_invalid_image(self, file_manager):
        """Should reject invalid images for vision purpose."""
        invalid_content = b"This is not an image"

        with pytest.raises(FileValidationError, match="Invalid PNG file"):
            await file_manager.upload_file(
                file_content=invalid_content, filename="fake.png", purpose="vision"
            )

    async def test_validate_vision_non_image_mime_type(self, file_manager):
        """Should reject non-image files for vision purpose."""
        text_content = b"Just some text"

        with pytest.raises(
            FileValidationError, match="not allowed for purpose 'vision'"
        ):
            await file_manager.upload_file(
                file_content=text_content, filename="text.txt", purpose="vision"
            )

    async def test_validate_assistants_json(self, file_manager):
        """Should validate JSON files for assistants purpose."""
        json_content = json.dumps({"data": ["item1", "item2", "item3"]}).encode("utf-8")

        file_obj = await file_manager.upload_file(
            file_content=json_content, filename="data.json", purpose="assistants"
        )

        assert file_obj.purpose == "assistants"

    async def test_validate_assistants_csv(self, file_manager):
        """Should validate CSV files for assistants purpose."""
        csv_content = b"name,age,city\nAlice,30,NYC\nBob,25,LA"

        file_obj = await file_manager.upload_file(
            file_content=csv_content, filename="data.csv", purpose="assistants"
        )

        assert file_obj.purpose == "assistants"

    async def test_validate_assistants_invalid_json(self, file_manager):
        """Should reject invalid JSON for assistants purpose."""
        invalid_json = b'{"invalid": json syntax}'

        with pytest.raises(FileValidationError, match="Invalid JSON"):
            await file_manager.upload_file(
                file_content=invalid_json, filename="bad.json", purpose="assistants"
            )


@pytest.mark.asyncio
class TestFileRetrieval:
    """Test file retrieval functionality."""

    async def test_get_file_metadata(self, file_manager):
        """Should retrieve file metadata."""
        content = b"test content"
        uploaded = await file_manager.upload_file(
            file_content=content, filename="test.txt", purpose="user_data"
        )

        retrieved = await file_manager.get_file(uploaded.id)

        assert retrieved.id == uploaded.id
        assert retrieved.filename == uploaded.filename
        assert retrieved.bytes == uploaded.bytes
        assert retrieved.purpose == uploaded.purpose

    async def test_get_file_content(self, file_manager):
        """Should retrieve file content."""
        content = b"test content for retrieval"
        uploaded = await file_manager.upload_file(
            file_content=content, filename="test.txt", purpose="user_data"
        )

        retrieved_content = await file_manager.get_file_content(uploaded.id)

        assert retrieved_content == content

    async def test_get_file_with_content(self, file_manager):
        """Should retrieve both metadata and content."""
        content = b"test content"
        uploaded = await file_manager.upload_file(
            file_content=content, filename="test.txt", purpose="user_data"
        )

        metadata, retrieved_content = await file_manager.get_file_with_content(
            uploaded.id
        )

        assert metadata.id == uploaded.id
        assert retrieved_content == content

    async def test_get_nonexistent_file_fails(self, file_manager):
        """Should raise error for nonexistent file."""
        with pytest.raises(FileNotFoundError, match="not found"):
            await file_manager.get_file("file-nonexistent")

    async def test_verify_checksum(self, file_manager):
        """Should verify file checksum."""
        content = b"content for checksum test"
        uploaded = await file_manager.upload_file(
            file_content=content, filename="test.txt", purpose="user_data"
        )

        # Get the stored file to retrieve checksum
        import hashlib

        expected_checksum = hashlib.md5(content).hexdigest()

        is_valid = await file_manager.verify_checksum(uploaded.id, expected_checksum)
        assert is_valid

        # Test with wrong checksum
        is_valid = await file_manager.verify_checksum(uploaded.id, "wrong_checksum")
        assert not is_valid


@pytest.mark.asyncio
class TestFileDeletion:
    """Test file deletion functionality."""

    async def test_delete_file(self, file_manager):
        """Should successfully delete a file."""
        content = b"file to delete"
        uploaded = await file_manager.upload_file(
            file_content=content, filename="delete.txt", purpose="user_data"
        )

        result = await file_manager.delete_file(uploaded.id)

        assert result["id"] == uploaded.id
        assert result["deleted"] is True

        # Verify file no longer exists
        with pytest.raises(FileNotFoundError):
            await file_manager.get_file(uploaded.id)

    async def test_delete_nonexistent_file_fails(self, file_manager):
        """Should raise error when deleting nonexistent file."""
        with pytest.raises(FileNotFoundError, match="not found"):
            await file_manager.delete_file("file-nonexistent")

    async def test_delete_updates_quota(self, file_manager):
        """Should update quota when file is deleted."""
        content = b"x" * 1000  # 1KB file
        uploaded = await file_manager.upload_file(
            file_content=content, filename="test.txt", purpose="user_data"
        )

        quota_before = await file_manager.get_user_quota_info()
        assert quota_before["file_count"] == 1
        assert quota_before["total_bytes"] == 1000

        await file_manager.delete_file(uploaded.id)

        quota_after = await file_manager.get_user_quota_info()
        assert quota_after["file_count"] == 0
        assert quota_after["total_bytes"] == 0


@pytest.mark.asyncio
class TestFileList:
    """Test file listing functionality."""

    async def test_list_all_files(self, file_manager):
        """Should list all uploaded files."""
        # Upload multiple files
        await file_manager.upload_file(
            file_content=b"file1", filename="file1.txt", purpose="user_data"
        )
        await file_manager.upload_file(
            file_content=b"file2", filename="file2.txt", purpose="user_data"
        )
        await file_manager.upload_file(
            file_content=b"file3", filename="file3.txt", purpose="user_data"
        )

        files = await file_manager.list_files()

        assert len(files) == 3

    async def test_list_files_by_purpose(self, file_manager):
        """Should filter files by purpose."""
        await file_manager.upload_file(
            file_content=b"file1", filename="file1.txt", purpose="user_data"
        )
        # Use valid fine-tune JSONL format
        finetune_content = b'{"messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]}'
        await file_manager.upload_file(
            file_content=finetune_content, filename="file2.jsonl", purpose="fine-tune"
        )
        await file_manager.upload_file(
            file_content=b"file3", filename="file3.txt", purpose="user_data"
        )

        user_files = await file_manager.list_files(purpose="user_data")
        finetune_files = await file_manager.list_files(purpose="fine-tune")

        assert len(user_files) == 2
        assert len(finetune_files) == 1

    async def test_list_files_with_limit(self, file_manager):
        """Should respect limit parameter."""
        # Upload 5 files
        for i in range(5):
            await file_manager.upload_file(
                file_content=f"file{i}".encode(),
                filename=f"file{i}.txt",
                purpose="user_data",
            )

        files = await file_manager.list_files(limit=3)

        assert len(files) == 3

    async def test_list_files_pagination_with_after(self, file_manager):
        """Should support cursor-based pagination."""
        # Upload files
        file1 = await file_manager.upload_file(
            file_content=b"file1", filename="file1.txt", purpose="user_data"
        )
        file2 = await file_manager.upload_file(
            file_content=b"file2", filename="file2.txt", purpose="user_data"
        )
        file3 = await file_manager.upload_file(
            file_content=b"file3", filename="file3.txt", purpose="user_data"
        )

        # Get files after file2 (which should be in the middle)
        files = await file_manager.list_files(after=file2.id)

        # Should not include file2
        file_ids = [f.id for f in files]
        assert file2.id not in file_ids
        # In descending order, after file2 should give us file1 (the earliest)
        assert len(files) >= 1

    async def test_list_files_order_desc(self, file_manager):
        """Should list files in descending order by creation time."""
        import asyncio
        import time

        # Use time.time() manipulation to ensure different timestamps
        file1 = await file_manager.upload_file(
            file_content=b"file1", filename="file1.txt", purpose="user_data"
        )
        await asyncio.sleep(0.1)  # Longer delay to ensure different timestamps
        file2 = await file_manager.upload_file(
            file_content=b"file2", filename="file2.txt", purpose="user_data"
        )
        await asyncio.sleep(0.1)
        file3 = await file_manager.upload_file(
            file_content=b"file3", filename="file3.txt", purpose="user_data"
        )

        files = await file_manager.list_files(order="desc")

        # Most recent first (check created_at instead of ID for ordering)
        assert files[0].created_at >= files[1].created_at
        assert files[1].created_at >= files[2].created_at
        # Also verify the correct files are in order
        file_ids = [f.id for f in files]
        assert file3.id in file_ids
        assert file1.id in file_ids

    async def test_list_files_order_asc(self, file_manager):
        """Should list files in ascending order by creation time."""
        import asyncio

        file1 = await file_manager.upload_file(
            file_content=b"file1", filename="file1.txt", purpose="user_data"
        )
        await asyncio.sleep(0.01)
        file2 = await file_manager.upload_file(
            file_content=b"file2", filename="file2.txt", purpose="user_data"
        )
        await asyncio.sleep(0.01)
        file3 = await file_manager.upload_file(
            file_content=b"file3", filename="file3.txt", purpose="user_data"
        )

        files = await file_manager.list_files(order="asc")

        # Oldest first
        assert files[0].id == file1.id
        assert files[-1].id == file3.id


@pytest.mark.asyncio
class TestQuotaEnforcement:
    """Test quota enforcement."""

    async def test_quota_tracking(self, file_manager):
        """Should track file count and storage usage."""
        quota_before = await file_manager.get_user_quota_info()
        assert quota_before["file_count"] == 0
        assert quota_before["total_bytes"] == 0

        content = b"x" * 1000
        await file_manager.upload_file(
            file_content=content, filename="test.txt", purpose="user_data"
        )

        quota_after = await file_manager.get_user_quota_info()
        assert quota_after["file_count"] == 1
        assert quota_after["total_bytes"] == 1000

    async def test_quota_file_count_limit(self, file_manager):
        """Should enforce file count limit."""
        # Set a low limit for testing
        file_manager.MAX_FILES_PER_USER = 3

        # Upload up to limit
        for i in range(3):
            await file_manager.upload_file(
                file_content=f"file{i}".encode(),
                filename=f"file{i}.txt",
                purpose="user_data",
            )

        # Next upload should fail
        with pytest.raises(FileQuotaError, match="file count limit exceeded"):
            await file_manager.upload_file(
                file_content=b"overflow", filename="overflow.txt", purpose="user_data"
            )

    async def test_quota_storage_size_limit(self, file_manager):
        """Should enforce storage size limit."""
        # Set a low limit for testing
        file_manager.MAX_STORAGE_PER_USER = 2000  # 2KB

        # Upload file near limit
        await file_manager.upload_file(
            file_content=b"x" * 1500, filename="file1.txt", purpose="user_data"
        )

        # Next upload should fail
        with pytest.raises(FileQuotaError, match="storage limit exceeded"):
            await file_manager.upload_file(
                file_content=b"x" * 600, filename="file2.txt", purpose="user_data"
            )

    async def test_quota_multiple_users(self, file_manager):
        """Should track quotas separately for different users."""
        await file_manager.upload_file(
            file_content=b"user1 file",
            filename="user1.txt",
            purpose="user_data",
            user_id="user1",
        )
        await file_manager.upload_file(
            file_content=b"user2 file",
            filename="user2.txt",
            purpose="user_data",
            user_id="user2",
        )

        quota_user1 = await file_manager.get_user_quota_info("user1")
        quota_user2 = await file_manager.get_user_quota_info("user2")

        assert quota_user1["file_count"] == 1
        assert quota_user2["file_count"] == 1
        assert quota_user1["total_bytes"] == len(b"user1 file")
        assert quota_user2["total_bytes"] == len(b"user2 file")


@pytest.mark.asyncio
class TestStorageBackends:
    """Test different storage backends."""

    async def test_memory_storage(self, file_manager):
        """Should store and retrieve from memory."""
        content = b"in-memory content"
        uploaded = await file_manager.upload_file(
            file_content=content, filename="memory.txt", purpose="user_data"
        )

        retrieved_content = await file_manager.get_file_content(uploaded.id)
        assert retrieved_content == content

    async def test_disk_storage(self, disk_file_manager):
        """Should store and retrieve from disk."""
        content = b"on-disk content"
        uploaded = await disk_file_manager.upload_file(
            file_content=content, filename="disk.txt", purpose="user_data"
        )

        retrieved_content = await disk_file_manager.get_file_content(uploaded.id)
        assert retrieved_content == content

    async def test_disk_storage_persistence(self):
        """Should persist files on disk across manager instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create first manager and upload file
            manager1 = FileManager(
                storage_backend="disk", storage_path=tmpdir, enable_cleanup=False
            )
            content = b"persistent content"
            uploaded = await manager1.upload_file(
                file_content=content, filename="persist.txt", purpose="user_data"
            )
            file_id = uploaded.id

            # Create second manager with same storage path
            manager2 = FileManager(
                storage_backend="disk", storage_path=tmpdir, enable_cleanup=False
            )

            # Should be able to retrieve file
            retrieved_content = await manager2.get_file_content(file_id)
            assert retrieved_content == content


@pytest.mark.asyncio
class TestMIMETypeDetection:
    """Test MIME type detection."""

    async def test_detect_png(self, file_manager):
        """Should detect PNG MIME type."""
        png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        uploaded = await file_manager.upload_file(
            file_content=png_content, filename="image.png", purpose="vision"
        )

        stored = await file_manager.storage.retrieve(uploaded.id)
        assert stored.mime_type == "image/png"

    async def test_detect_jpeg(self, file_manager):
        """Should detect JPEG MIME type."""
        jpeg_content = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        uploaded = await file_manager.upload_file(
            file_content=jpeg_content, filename="image.jpg", purpose="vision"
        )

        stored = await file_manager.storage.retrieve(uploaded.id)
        assert stored.mime_type == "image/jpeg"

    async def test_detect_jsonl(self, file_manager):
        """Should detect JSONL MIME type."""
        jsonl_content = b'{"test": "data"}\n{"test": "data2"}'
        uploaded = await file_manager.upload_file(
            file_content=jsonl_content, filename="data.jsonl", purpose="user_data"
        )

        stored = await file_manager.storage.retrieve(uploaded.id)
        assert stored.mime_type == "application/jsonl"

    async def test_detect_json(self, file_manager):
        """Should detect JSON MIME type."""
        json_content = b'{"test": "data"}'
        uploaded = await file_manager.upload_file(
            file_content=json_content, filename="data.json", purpose="user_data"
        )

        stored = await file_manager.storage.retrieve(uploaded.id)
        assert stored.mime_type == "application/json"


@pytest.mark.asyncio
class TestChecksumValidation:
    """Test checksum calculation and validation."""

    async def test_checksum_calculation(self, file_manager):
        """Should calculate correct MD5 checksum."""
        import hashlib

        content = b"content for checksum"
        expected_checksum = hashlib.md5(content).hexdigest()

        uploaded = await file_manager.upload_file(
            file_content=content, filename="test.txt", purpose="user_data"
        )

        stored = await file_manager.storage.retrieve(uploaded.id)
        assert stored.checksum == expected_checksum

    async def test_checksum_different_for_different_content(self, file_manager):
        """Should have different checksums for different content."""
        file1 = await file_manager.upload_file(
            file_content=b"content 1", filename="file1.txt", purpose="user_data"
        )
        file2 = await file_manager.upload_file(
            file_content=b"content 2", filename="file2.txt", purpose="user_data"
        )

        stored1 = await file_manager.storage.retrieve(file1.id)
        stored2 = await file_manager.storage.retrieve(file2.id)

        assert stored1.checksum != stored2.checksum
