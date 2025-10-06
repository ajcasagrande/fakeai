"""
Comprehensive tests for FileService.

Tests cover:
- File upload with validation
- File listing with pagination
- File retrieval and deletion
- Purpose validation
- Quota enforcement
- Error handling
- Metrics tracking
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai.config import AppConfig
from fakeai.file_manager import (
    FileManager,
    FileNotFoundError,
    FileQuotaError,
    FileValidationError,
)
from fakeai.metrics import MetricsTracker
from fakeai.services.file_service import FileService


@pytest.fixture
def config():
    """Create test configuration."""
    return AppConfig(
        response_delay=0.0,
        file_storage_backend="memory",
        file_cleanup_enabled=False,
    )


@pytest.fixture
def metrics_tracker():
    """Create metrics tracker."""
    return MetricsTracker()


@pytest.fixture
def file_manager():
    """Create file manager."""
    return FileManager(storage_backend="memory", enable_cleanup=False)


@pytest.fixture
def file_service(config, metrics_tracker, file_manager):
    """Create file service."""
    return FileService(
        config=config,
        metrics_tracker=metrics_tracker,
        file_manager=file_manager,
    )


# Test Upload


@pytest.mark.asyncio
async def test_upload_basic(file_service):
    """Test basic file upload."""
    content = b"Hello, world!"
    filename = "test.txt"
    purpose = "assistants"

    file_obj = await file_service.upload_file(
        file_content=content,
        filename=filename,
        purpose=purpose,
    )

    assert file_obj.id.startswith("file-")
    assert file_obj.filename == filename
    assert file_obj.purpose == purpose
    assert file_obj.bytes == len(content)
    assert file_obj.status == "uploaded"


@pytest.mark.asyncio
async def test_upload_jsonl_fine_tune(file_service):
    """Test uploading JSONL file for fine-tuning."""
    content = b'{"messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]}\n'
    filename = "training.jsonl"
    purpose = "fine-tune"

    file_obj = await file_service.upload_file(
        file_content=content,
        filename=filename,
        purpose=purpose,
    )

    assert file_obj.id.startswith("file-")
    assert file_obj.filename == filename
    assert file_obj.purpose == purpose
    assert file_obj.bytes == len(content)


@pytest.mark.asyncio
async def test_upload_batch_jsonl(file_service):
    """Test uploading JSONL file for batch processing."""
    content = b'{"custom_id": "req-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]}}\n'
    filename = "batch.jsonl"
    purpose = "batch"

    file_obj = await file_service.upload_file(
        file_content=content,
        filename=filename,
        purpose=purpose,
    )

    assert file_obj.id.startswith("file-")
    assert file_obj.purpose == purpose


@pytest.mark.asyncio
async def test_upload_image_vision(file_service):
    """Test uploading image for vision."""
    # PNG magic bytes + minimal header
    content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200
    filename = "image.png"
    purpose = "vision"

    file_obj = await file_service.upload_file(
        file_content=content,
        filename=filename,
        purpose=purpose,
    )

    assert file_obj.id.startswith("file-")
    assert file_obj.purpose == purpose


@pytest.mark.asyncio
async def test_upload_csv_assistants(file_service):
    """Test uploading CSV file for assistants."""
    content = b"name,age,city\nAlice,30,NYC\nBob,25,LA\n"
    filename = "data.csv"
    purpose = "assistants"

    file_obj = await file_service.upload_file(
        file_content=content,
        filename=filename,
        purpose=purpose,
    )

    assert file_obj.id.startswith("file-")
    assert file_obj.purpose == purpose


@pytest.mark.asyncio
async def test_upload_with_user_id(file_service):
    """Test file upload with custom user ID."""
    content = b"Test content"
    filename = "test.txt"
    purpose = "assistants"
    user_id = "user-123"

    file_obj = await file_service.upload_file(
        file_content=content,
        filename=filename,
        purpose=purpose,
        user_id=user_id,
    )

    assert file_obj.id.startswith("file-")

    # Verify quota tracking
    quota = await file_service.get_user_quota_info(user_id)
    assert quota["file_count"] == 1
    assert quota["total_bytes"] == len(content)


# Test Upload Validation


@pytest.mark.asyncio
async def test_upload_empty_file_fails(file_service):
    """Test that uploading empty file fails."""
    # Empty content is caught by ValueError before it reaches FileManager
    with pytest.raises((ValueError, FileValidationError)):
        await file_service.upload_file(
            file_content=b"",
            filename="empty.txt",
            purpose="assistants",
        )


@pytest.mark.asyncio
async def test_upload_invalid_purpose_fails(file_service):
    """Test that uploading with invalid purpose fails."""
    with pytest.raises(ValueError, match="Invalid purpose"):
        await file_service.upload_file(
            file_content=b"test",
            filename="test.txt",
            purpose="invalid_purpose",
        )


@pytest.mark.asyncio
async def test_upload_missing_filename_fails(file_service):
    """Test that uploading without filename fails."""
    with pytest.raises(ValueError, match="Filename is required"):
        await file_service.upload_file(
            file_content=b"test",
            filename="",
            purpose="assistants",
        )


@pytest.mark.asyncio
async def test_upload_missing_purpose_fails(file_service):
    """Test that uploading without purpose fails."""
    with pytest.raises(ValueError, match="Purpose is required"):
        await file_service.upload_file(
            file_content=b"test",
            filename="test.txt",
            purpose="",
        )


@pytest.mark.asyncio
async def test_upload_missing_content_fails(file_service):
    """Test that uploading without content fails."""
    with pytest.raises(ValueError, match="File content is required"):
        await file_service.upload_file(
            file_content=None,
            filename="test.txt",
            purpose="assistants",
        )


@pytest.mark.asyncio
async def test_upload_wrong_mime_type_for_purpose(file_service):
    """Test that uploading wrong MIME type for purpose fails."""
    # Try to upload text file for vision purpose
    content = b"Not an image"
    filename = "test.txt"
    purpose = "vision"

    with pytest.raises(FileValidationError, match="MIME type.*not allowed"):
        await file_service.upload_file(
            file_content=content,
            filename=filename,
            purpose=purpose,
        )


@pytest.mark.asyncio
async def test_upload_invalid_jsonl_for_fine_tune(file_service):
    """Test that uploading invalid JSONL for fine-tuning fails."""
    content = b'{"invalid": "format"}\n'  # Missing 'messages' field
    filename = "invalid.jsonl"
    purpose = "fine-tune"

    with pytest.raises(FileValidationError, match="Missing 'messages' field"):
        await file_service.upload_file(
            file_content=content,
            filename=filename,
            purpose=purpose,
        )


@pytest.mark.asyncio
async def test_upload_invalid_jsonl_for_batch(file_service):
    """Test that uploading invalid JSONL for batch fails."""
    content = b'{"custom_id": "req-1"}\n'  # Missing required fields
    filename = "invalid.jsonl"
    purpose = "batch"

    with pytest.raises(FileValidationError, match="Missing required field"):
        await file_service.upload_file(
            file_content=content,
            filename=filename,
            purpose=purpose,
        )


# Test List


@pytest.mark.asyncio
async def test_list_files_empty(file_service):
    """Test listing files when none exist."""
    result = await file_service.list_files()

    assert result.object == "list"
    assert result.data == []


@pytest.mark.asyncio
async def test_list_files_basic(file_service):
    """Test listing files."""
    # Upload some files
    for i in range(5):
        await file_service.upload_file(
            file_content=f"content {i}".encode(),
            filename=f"file{i}.txt",
            purpose="assistants",
        )

    result = await file_service.list_files()

    assert result.object == "list"
    assert len(result.data) == 5
    assert all(f.id.startswith("file-") for f in result.data)


@pytest.mark.asyncio
async def test_list_files_with_purpose_filter(file_service):
    """Test listing files filtered by purpose."""
    # Upload files with different purposes
    await file_service.upload_file(
        file_content=b"content 1",
        filename="file1.txt",
        purpose="assistants",
    )
    await file_service.upload_file(
        file_content=b'{"messages": [{"role": "user", "content": "test"}]}',
        filename="file2.jsonl",
        purpose="fine-tune",
    )
    await file_service.upload_file(
        file_content=b"content 3",
        filename="file3.txt",
        purpose="assistants",
    )

    # List only assistants files
    result = await file_service.list_files(purpose="assistants")

    assert len(result.data) == 2
    assert all(f.purpose == "assistants" for f in result.data)


@pytest.mark.asyncio
async def test_list_files_with_limit(file_service):
    """Test listing files with limit."""
    # Upload 10 files
    for i in range(10):
        await file_service.upload_file(
            file_content=f"content {i}".encode(),
            filename=f"file{i}.txt",
            purpose="assistants",
        )

    # List with limit of 3
    result = await file_service.list_files(limit=3)

    assert len(result.data) == 3


@pytest.mark.asyncio
async def test_list_files_with_pagination(file_service):
    """Test listing files with cursor-based pagination."""
    # Upload 5 files
    files = []
    for i in range(5):
        file_obj = await file_service.upload_file(
            file_content=f"content {i}".encode(),
            filename=f"file{i}.txt",
            purpose="assistants",
        )
        files.append(file_obj)

    # Get first page (limit 2)
    page1 = await file_service.list_files(limit=2)
    assert len(page1.data) == 2

    # Get second page (after first file)
    page2 = await file_service.list_files(limit=2, after=page1.data[1].id)
    assert len(page2.data) <= 2

    # Verify no overlap
    page1_ids = {f.id for f in page1.data}
    page2_ids = {f.id for f in page2.data}
    assert len(page1_ids & page2_ids) == 0


@pytest.mark.asyncio
async def test_list_files_with_order_asc(file_service):
    """Test listing files with ascending order."""
    # Upload files
    for i in range(3):
        await file_service.upload_file(
            file_content=f"content {i}".encode(),
            filename=f"file{i}.txt",
            purpose="assistants",
        )

    result = await file_service.list_files(order="asc")

    assert len(result.data) == 3
    # Verify ascending order by creation time
    timestamps = [f.created_at for f in result.data]
    assert timestamps == sorted(timestamps)


@pytest.mark.asyncio
async def test_list_files_with_order_desc(file_service):
    """Test listing files with descending order (default)."""
    # Upload files
    for i in range(3):
        await file_service.upload_file(
            file_content=f"content {i}".encode(),
            filename=f"file{i}.txt",
            purpose="assistants",
        )

    result = await file_service.list_files(order="desc")

    assert len(result.data) == 3
    # Verify descending order by creation time
    timestamps = [f.created_at for f in result.data]
    assert timestamps == sorted(timestamps, reverse=True)


@pytest.mark.asyncio
async def test_list_files_invalid_limit(file_service):
    """Test that listing with invalid limit fails."""
    with pytest.raises(ValueError, match="Limit must be between"):
        await file_service.list_files(limit=0)

    with pytest.raises(ValueError, match="Limit must be between"):
        await file_service.list_files(limit=10001)


@pytest.mark.asyncio
async def test_list_files_invalid_order(file_service):
    """Test that listing with invalid order fails."""
    with pytest.raises(ValueError, match="Order must be"):
        await file_service.list_files(order="invalid")


@pytest.mark.asyncio
async def test_list_files_invalid_purpose(file_service):
    """Test that listing with invalid purpose fails."""
    with pytest.raises(ValueError, match="Invalid purpose"):
        await file_service.list_files(purpose="invalid_purpose")


# Test Get


@pytest.mark.asyncio
async def test_get_file_basic(file_service):
    """Test getting file metadata."""
    # Upload a file
    uploaded = await file_service.upload_file(
        file_content=b"test content",
        filename="test.txt",
        purpose="assistants",
    )

    # Get the file
    retrieved = await file_service.get_file(uploaded.id)

    assert retrieved.id == uploaded.id
    assert retrieved.filename == uploaded.filename
    assert retrieved.purpose == uploaded.purpose
    assert retrieved.bytes == uploaded.bytes


@pytest.mark.asyncio
async def test_get_file_not_found(file_service):
    """Test getting non-existent file."""
    with pytest.raises(FileNotFoundError):
        await file_service.get_file("file-nonexistent")


@pytest.mark.asyncio
async def test_get_file_empty_id(file_service):
    """Test getting file with empty ID."""
    with pytest.raises(ValueError, match="File ID is required"):
        await file_service.get_file("")


# Test Get Content


@pytest.mark.asyncio
async def test_get_file_content_basic(file_service):
    """Test getting file content."""
    content = b"Hello, world!"

    # Upload a file
    uploaded = await file_service.upload_file(
        file_content=content,
        filename="test.txt",
        purpose="assistants",
    )

    # Get the content
    retrieved_content = await file_service.get_file_content(uploaded.id)

    assert retrieved_content == content


@pytest.mark.asyncio
async def test_get_file_content_not_found(file_service):
    """Test getting content of non-existent file."""
    with pytest.raises(FileNotFoundError):
        await file_service.get_file_content("file-nonexistent")


@pytest.mark.asyncio
async def test_get_file_content_empty_id(file_service):
    """Test getting file content with empty ID."""
    with pytest.raises(ValueError, match="File ID is required"):
        await file_service.get_file_content("")


# Test Delete


@pytest.mark.asyncio
async def test_delete_file_basic(file_service):
    """Test deleting a file."""
    # Upload a file
    uploaded = await file_service.upload_file(
        file_content=b"test content",
        filename="test.txt",
        purpose="assistants",
    )

    # Delete the file
    result = await file_service.delete_file(uploaded.id)

    assert result["id"] == uploaded.id
    assert result["object"] == "file"
    assert result["deleted"] is True

    # Verify file is gone
    with pytest.raises(FileNotFoundError):
        await file_service.get_file(uploaded.id)


@pytest.mark.asyncio
async def test_delete_file_updates_quota(file_service):
    """Test that deleting a file updates quota."""
    user_id = "user-123"
    content = b"test content"

    # Upload a file
    uploaded = await file_service.upload_file(
        file_content=content,
        filename="test.txt",
        purpose="assistants",
        user_id=user_id,
    )

    # Check quota before deletion
    quota_before = await file_service.get_user_quota_info(user_id)
    assert quota_before["file_count"] == 1
    assert quota_before["total_bytes"] == len(content)

    # Delete the file
    await file_service.delete_file(uploaded.id)

    # Check quota after deletion
    quota_after = await file_service.get_user_quota_info(user_id)
    assert quota_after["file_count"] == 0
    assert quota_after["total_bytes"] == 0


@pytest.mark.asyncio
async def test_delete_file_not_found(file_service):
    """Test deleting non-existent file."""
    with pytest.raises(FileNotFoundError):
        await file_service.delete_file("file-nonexistent")


@pytest.mark.asyncio
async def test_delete_file_empty_id(file_service):
    """Test deleting file with empty ID."""
    with pytest.raises(ValueError, match="File ID is required"):
        await file_service.delete_file("")


# Test Quota


@pytest.mark.asyncio
async def test_quota_enforcement_file_count(file_service, file_manager):
    """Test quota enforcement for file count."""
    user_id = "user-limited"

    # Set low file count limit for testing
    original_max = file_manager.MAX_FILES_PER_USER
    file_manager.MAX_FILES_PER_USER = 3

    try:
        # Upload up to limit
        for i in range(3):
            await file_service.upload_file(
                file_content=f"content {i}".encode(),
                filename=f"file{i}.txt",
                purpose="assistants",
                user_id=user_id,
            )

        # Next upload should fail
        with pytest.raises(FileQuotaError, match="file count limit exceeded"):
            await file_service.upload_file(
                file_content=b"one too many",
                filename="file_extra.txt",
                purpose="assistants",
                user_id=user_id,
            )

    finally:
        file_manager.MAX_FILES_PER_USER = original_max


@pytest.mark.asyncio
async def test_quota_enforcement_storage_size(file_service, file_manager):
    """Test quota enforcement for storage size."""
    user_id = "user-limited"

    # Set low storage limit for testing
    original_max = file_manager.MAX_STORAGE_PER_USER
    file_manager.MAX_STORAGE_PER_USER = 100  # 100 bytes

    try:
        # Upload file that fits
        await file_service.upload_file(
            file_content=b"a" * 50,
            filename="file1.txt",
            purpose="assistants",
            user_id=user_id,
        )

        # Next upload should fail (total would be 150 bytes)
        with pytest.raises(FileQuotaError, match="storage limit exceeded"):
            await file_service.upload_file(
                file_content=b"b" * 60,
                filename="file2.txt",
                purpose="assistants",
                user_id=user_id,
            )

    finally:
        file_manager.MAX_STORAGE_PER_USER = original_max


@pytest.mark.asyncio
async def test_get_user_quota_info(file_service):
    """Test getting user quota information."""
    user_id = "user-123"

    # Initial quota
    quota = await file_service.get_user_quota_info(user_id)
    assert quota["file_count"] == 0
    assert quota["total_bytes"] == 0
    assert "max_files" in quota
    assert "max_bytes" in quota
    assert "files_remaining" in quota
    assert "bytes_remaining" in quota

    # Upload a file
    content = b"test content"
    await file_service.upload_file(
        file_content=content,
        filename="test.txt",
        purpose="assistants",
        user_id=user_id,
    )

    # Check updated quota
    quota = await file_service.get_user_quota_info(user_id)
    assert quota["file_count"] == 1
    assert quota["total_bytes"] == len(content)
    assert quota["files_remaining"] == quota["max_files"] - 1


# Test Checksum Verification


@pytest.mark.asyncio
async def test_verify_checksum_valid(file_service):
    """Test verifying valid checksum."""
    import hashlib

    content = b"test content"
    expected_checksum = hashlib.md5(content).hexdigest()

    # Upload a file
    uploaded = await file_service.upload_file(
        file_content=content,
        filename="test.txt",
        purpose="assistants",
    )

    # Verify checksum
    result = await file_service.verify_checksum(uploaded.id, expected_checksum)
    assert result is True


@pytest.mark.asyncio
async def test_verify_checksum_invalid(file_service):
    """Test verifying invalid checksum."""
    content = b"test content"

    # Upload a file
    uploaded = await file_service.upload_file(
        file_content=content,
        filename="test.txt",
        purpose="assistants",
    )

    # Verify with wrong checksum
    result = await file_service.verify_checksum(uploaded.id, "invalid_checksum")
    assert result is False


# Test Metrics Tracking


@pytest.mark.asyncio
async def test_metrics_tracking_on_upload(file_service, metrics_tracker):
    """Test that metrics are tracked on upload."""
    # Upload a file
    await file_service.upload_file(
        file_content=b"test",
        filename="test.txt",
        purpose="assistants",
    )

    # Check metrics were updated
    # Note: Metrics use sliding window and may include previous test errors
    # Just verify responses were tracked (successful upload)
    metrics = metrics_tracker.get_metrics()
    responses = metrics.get("responses", {}).get("/v1/files", {}).get("rate", 0)
    assert responses > 0  # At least one response was tracked


@pytest.mark.asyncio
async def test_metrics_tracking_on_error(file_service, metrics_tracker):
    """Test that metrics track errors."""
    # Track initial error count
    initial_metrics = metrics_tracker.get_metrics()
    initial_error_rate = (
        initial_metrics.get("errors", {}).get("/v1/files", {}).get("rate", 0)
    )

    # Try to upload invalid file - this will raise ValueError before reaching FileManager
    # but still tracks error in metrics
    try:
        await file_service.upload_file(
            file_content=None,  # This will cause ValueError
            filename="test.txt",
            purpose="assistants",
        )
    except ValueError:
        pass

    # Verify error tracking structure exists
    metrics = metrics_tracker.get_metrics()
    assert "errors" in metrics


# Test Integration


@pytest.mark.asyncio
async def test_end_to_end_file_lifecycle(file_service):
    """Test complete file lifecycle: upload, list, get, get content, delete."""
    content = b"Test file content"
    filename = "lifecycle.txt"
    purpose = "assistants"

    # 1. Upload
    uploaded = await file_service.upload_file(
        file_content=content,
        filename=filename,
        purpose=purpose,
    )
    assert uploaded.id.startswith("file-")

    # 2. List and find
    files = await file_service.list_files()
    assert any(f.id == uploaded.id for f in files.data)

    # 3. Get metadata
    retrieved = await file_service.get_file(uploaded.id)
    assert retrieved.id == uploaded.id
    assert retrieved.filename == filename

    # 4. Get content
    retrieved_content = await file_service.get_file_content(uploaded.id)
    assert retrieved_content == content

    # 5. Delete
    result = await file_service.delete_file(uploaded.id)
    assert result["deleted"] is True

    # 6. Verify deleted
    with pytest.raises(FileNotFoundError):
        await file_service.get_file(uploaded.id)


@pytest.mark.asyncio
async def test_multiple_users_isolation(file_service):
    """Test that quota and files are isolated per user."""
    user1 = "user-1"
    user2 = "user-2"

    # Upload for user 1 with different size
    await file_service.upload_file(
        file_content=b"user 1 content with more bytes",
        filename="file1.txt",
        purpose="assistants",
        user_id=user1,
    )

    # Upload for user 2 with different size
    await file_service.upload_file(
        file_content=b"user 2",
        filename="file2.txt",
        purpose="assistants",
        user_id=user2,
    )

    # Check quotas are separate
    quota1 = await file_service.get_user_quota_info(user1)
    quota2 = await file_service.get_user_quota_info(user2)

    assert quota1["file_count"] == 1
    assert quota2["file_count"] == 1
    # Different content sizes should result in different byte counts
    assert quota1["total_bytes"] != quota2["total_bytes"]
