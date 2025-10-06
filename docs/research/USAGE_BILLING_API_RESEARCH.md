# OpenAI Usage and Billing APIs - Research Report

**Date:** 2025-10-04
**Purpose:** Comprehensive research on OpenAI's Usage and Billing APIs for FakeAI implementation
**Version:** 1.0

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [API Overview](#api-overview)
3. [Usage API Endpoints](#usage-api-endpoints)
4. [Costs API Endpoint](#costs-api-endpoint)
5. [Request/Response Schemas](#requestresponse-schemas)
6. [Cost Calculation Methods](#cost-calculation-methods)
7. [Implementation Guide for FakeAI](#implementation-guide-for-fakeai)
8. [Appendix: Pricing Reference](#appendix-pricing-reference)

---

## Executive Summary

OpenAI launched the **Usage API** and **Costs API** in December 2024, providing programmatic access to granular API usage data and cost breakdowns. These APIs enable organizations to:

- Track token usage by minute/hour/day
- Filter usage by API key, project ID, user ID, and model
- Monitor costs with daily spend breakdowns
- Group and aggregate data across multiple dimensions
- Reconcile usage with billing invoices

### Key Endpoints

| Endpoint | Purpose | Launch Date |
|----------|---------|-------------|
| `GET /v1/organization/usage/completions` | Chat/text completion usage | Dec 2024 |
| `GET /v1/organization/usage/embeddings` | Embeddings usage | Dec 2024 |
| `GET /v1/organization/usage/images` | Image generation usage | Dec 2024 |
| `GET /v1/organization/usage/audio` | Audio processing usage | Dec 2024 |
| `GET /v1/organization/usage/moderations` | Moderation usage | Dec 2024 |
| `GET /v1/organization/usage/vector_stores` | Vector store usage | Dec 2024 |
| `GET /v1/organization/usage/code_interpreter_sessions` | Code interpreter usage | Dec 2024 |
| `GET /v1/organization/costs` | Cost breakdown by line item | Dec 2024 |

### Important Note on Reconciliation

**For financial purposes**, OpenAI recommends using the **Costs endpoint** or the Costs tab in the Usage Dashboard, as these reconcile back to billing invoices. The Usage API may have minor discrepancies due to differences in how usage and spend are recorded.

---

## API Overview

### Authentication

All usage and costs endpoints require **Admin API keys** for authentication.

**Format:**
```
Authorization: Bearer sk-admin-your-key-here
```

### Common Parameters

All endpoints support these parameters:

| Parameter | Type | Required | Description | Valid Values |
|-----------|------|----------|-------------|--------------|
| `start_time` | integer | Yes | Start time (Unix timestamp) | Any valid Unix timestamp |
| `end_time` | integer | No | End time (Unix timestamp) | Any valid Unix timestamp |
| `bucket_width` | string | No | Time bucket size | `'1m'`, `'1h'`, `'1d'` (default: `'1d'`) |
| `limit` | integer | No | Number of buckets to return | 1-500 (default: 7) |
| `page` | string | No | Pagination cursor | Opaque string from `next_page` |
| `group_by` | array | No | Fields to group results by | See endpoint-specific values |

### Pagination

Responses include a `next_page` field containing a cursor for the next page of results. When `next_page` is `null`, there are no more results.

**Example pagination:**
```python
params = {"start_time": 1736553600, "limit": 100}
while True:
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    # Process data["data"]

    if not data.get("next_page"):
        break

    params["page"] = data["next_page"]
```

---

## Usage API Endpoints

### Common Response Structure

All usage endpoints return data in a consistent format:

```json
{
  "object": "list",
  "data": [
    {
      "object": "bucket",
      "start_time": 1736553600,
      "end_time": 1736640000,
      "results": [
        {
          "object": "organization.usage.{endpoint_type}.result",
          // Endpoint-specific fields
        }
      ]
    }
  ],
  "next_page": "cursor_string_or_null"
}
```

### 1. Completions Usage

**Endpoint:** `GET /v1/organization/usage/completions`

**Purpose:** Track chat and text completion API usage

#### Additional Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `project_ids` | array | Filter by project IDs | `["proj_abc123"]` |
| `user_ids` | array | Filter by user IDs | `["user-123"]` |
| `api_key_ids` | array | Filter by API key IDs | `["key_abc123"]` |
| `models` | array | Filter by model names | `["openai/gpt-oss-120b", "meta-llama/Llama-3.1-8B-Instruct"]` |
| `batch` | boolean | Filter batch vs real-time | `true` or `false` |
| `group_by` | array | Group results by fields | `["project_id", "model", "batch"]` |

#### Response Schema

```json
{
  "object": "list",
  "data": [
    {
      "object": "bucket",
      "start_time": 1736616660,
      "end_time": 1736640000,
      "results": [
        {
          "object": "organization.usage.completions.result",
          "input_tokens": 141201,
          "output_tokens": 9756,
          "input_cached_tokens": 0,
          "input_audio_tokens": 0,
          "output_audio_tokens": 0,
          "num_model_requests": 470,
          "project_id": "proj_abc123",
          "user_id": "user-456",
          "api_key_id": "key_xyz789",
          "model": "openai/gpt-oss-120b",
          "batch": false
        }
      ]
    }
  ],
  "next_page": null
}
```

#### Result Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | Always `"organization.usage.completions.result"` |
| `input_tokens` | integer | Number of input tokens consumed |
| `output_tokens` | integer | Number of output tokens generated |
| `input_cached_tokens` | integer | Number of cached input tokens (prompt caching) |
| `input_audio_tokens` | integer | Number of input audio tokens |
| `output_audio_tokens` | integer | Number of output audio tokens |
| `num_model_requests` | integer | Number of API requests made |
| `project_id` | string \| null | Project ID (if grouped by project) |
| `user_id` | string \| null | User ID (if grouped by user) |
| `api_key_id` | string \| null | API key ID (if grouped by key) |
| `model` | string \| null | Model name (if grouped by model) |
| `batch` | boolean \| null | Batch status (if grouped by batch) |

### 2. Embeddings Usage

**Endpoint:** `GET /v1/organization/usage/embeddings`

**Purpose:** Track embeddings API usage

#### Additional Parameters

Same as completions: `project_ids`, `user_ids`, `api_key_ids`, `models`, `group_by`

#### Response Schema

```json
{
  "object": "list",
  "data": [
    {
      "object": "bucket",
      "start_time": 1736553600,
      "end_time": 1736640000,
      "results": [
        {
          "object": "organization.usage.embeddings.result",
          "input_tokens": 50000,
          "num_model_requests": 100,
          "project_id": null,
          "user_id": null,
          "api_key_id": null,
          "model": null
        }
      ]
    }
  ],
  "next_page": null
}
```

#### Result Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | Always `"organization.usage.embeddings.result"` |
| `input_tokens` | integer | Number of input tokens processed |
| `num_model_requests` | integer | Number of API requests made |
| `project_id` | string \| null | Project ID (if grouped) |
| `user_id` | string \| null | User ID (if grouped) |
| `api_key_id` | string \| null | API key ID (if grouped) |
| `model` | string \| null | Model name (if grouped) |

### 3. Images Usage

**Endpoint:** `GET /v1/organization/usage/images`

**Purpose:** Track image generation API usage

#### Additional Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `sources` | array | Filter by generation source | `["stabilityai/stable-diffusion-xl-base-1.0", "stabilityai/stable-diffusion-2-1"]` |
| `sizes` | array | Filter by image size | `["1024x1024", "512x512"]` |
| `project_ids` | array | Filter by project IDs | `["proj_abc123"]` |
| `user_ids` | array | Filter by user IDs | `["user-123"]` |
| `api_key_ids` | array | Filter by API key IDs | `["key_abc123"]` |
| `group_by` | array | Group results by fields | `["source", "size", "project_id"]` |

#### Response Schema

```json
{
  "object": "list",
  "data": [
    {
      "object": "bucket",
      "start_time": 1736553600,
      "end_time": 1736640000,
      "results": [
        {
          "object": "organization.usage.images.result",
          "num_images": 150,
          "num_model_requests": 50,
          "source": "stabilityai/stable-diffusion-xl-base-1.0",
          "size": "1024x1024",
          "project_id": null,
          "user_id": null,
          "api_key_id": null
        }
      ]
    }
  ],
  "next_page": null
}
```

#### Result Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | Always `"organization.usage.images.result"` |
| `num_images` | integer | Number of images generated |
| `num_model_requests` | integer | Number of API requests made |
| `source` | string \| null | Generation source (if grouped) |
| `size` | string \| null | Image size (if grouped) |
| `project_id` | string \| null | Project ID (if grouped) |
| `user_id` | string \| null | User ID (if grouped) |
| `api_key_id` | string \| null | API key ID (if grouped) |

### 4. Audio Usage

**Endpoint:** `GET /v1/organization/usage/audio`

**Purpose:** Track audio processing API usage (TTS, Whisper, audio generation)

#### Additional Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `models` | array | Filter by model names | `["whisper-1", "tts-1"]` |
| `project_ids` | array | Filter by project IDs | `["proj_abc123"]` |
| `user_ids` | array | Filter by user IDs | `["user-123"]` |
| `api_key_ids` | array | Filter by API key IDs | `["key_abc123"]` |
| `group_by` | array | Group results by fields | `["model", "project_id"]` |

#### Response Schema

```json
{
  "object": "list",
  "data": [
    {
      "object": "bucket",
      "start_time": 1736553600,
      "end_time": 1736640000,
      "results": [
        {
          "object": "organization.usage.audio.result",
          "num_seconds": 3600,
          "num_model_requests": 120,
          "model": "whisper-1",
          "project_id": null,
          "user_id": null,
          "api_key_id": null
        }
      ]
    }
  ],
  "next_page": null
}
```

#### Result Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | Always `"organization.usage.audio.result"` |
| `num_seconds` | integer | Number of audio seconds processed |
| `num_model_requests` | integer | Number of API requests made |
| `model` | string \| null | Model name (if grouped) |
| `project_id` | string \| null | Project ID (if grouped) |
| `user_id` | string \| null | User ID (if grouped) |
| `api_key_id` | string \| null | API key ID (if grouped) |

### 5. Moderations Usage

**Endpoint:** `GET /v1/organization/usage/moderations`

**Purpose:** Track content moderation API usage

#### Response Schema

```json
{
  "object": "list",
  "data": [
    {
      "object": "bucket",
      "start_time": 1736553600,
      "end_time": 1736640000,
      "results": [
        {
          "object": "organization.usage.moderations.result",
          "num_model_requests": 1500,
          "project_id": null,
          "user_id": null,
          "api_key_id": null
        }
      ]
    }
  ],
  "next_page": null
}
```

#### Result Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | Always `"organization.usage.moderations.result"` |
| `num_model_requests` | integer | Number of moderation requests made |
| `project_id` | string \| null | Project ID (if grouped) |
| `user_id` | string \| null | User ID (if grouped) |
| `api_key_id` | string \| null | API key ID (if grouped) |

**Note:** Moderations API is free, so no token or cost tracking.

### 6. Vector Stores Usage

**Endpoint:** `GET /v1/organization/usage/vector_stores`

**Purpose:** Track vector store API usage

#### Response Schema

```json
{
  "object": "list",
  "data": [
    {
      "object": "bucket",
      "start_time": 1736553600,
      "end_time": 1736640000,
      "results": [
        {
          "object": "organization.usage.vector_stores.result",
          "usage_bytes": 1073741824,
          "num_vector_stores": 5,
          "project_id": null
        }
      ]
    }
  ],
  "next_page": null
}
```

#### Result Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | Always `"organization.usage.vector_stores.result"` |
| `usage_bytes` | integer | Number of bytes stored |
| `num_vector_stores` | integer | Number of vector stores |
| `project_id` | string \| null | Project ID (if grouped) |

### 7. Code Interpreter Sessions Usage

**Endpoint:** `GET /v1/organization/usage/code_interpreter_sessions`

**Purpose:** Track code interpreter session usage

#### Response Schema

```json
{
  "object": "list",
  "data": [
    {
      "object": "bucket",
      "start_time": 1736553600,
      "end_time": 1736640000,
      "results": [
        {
          "object": "organization.usage.code_interpreter_sessions.result",
          "num_sessions": 25,
          "project_id": null
        }
      ]
    }
  ],
  "next_page": null
}
```

#### Result Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | Always `"organization.usage.code_interpreter_sessions.result"` |
| `num_sessions` | integer | Number of code interpreter sessions |
| `project_id` | string \| null | Project ID (if grouped) |

---

## Costs API Endpoint

**Endpoint:** `GET /v1/organization/costs`

**Purpose:** Get detailed breakdown of API spend by invoice line item

### Important Notes

- **Recommended for financial tracking** - reconciles with billing invoices
- Currently only supports `bucket_width='1d'` (daily aggregation)
- Costs may lag behind usage data by up to 24 hours
- Includes all billable API usage (completions, embeddings, images, audio, etc.)

### Request Parameters

| Parameter | Type | Required | Description | Valid Values |
|-----------|------|----------|-------------|--------------|
| `start_time` | integer | Yes | Start time (Unix timestamp) | Any valid Unix timestamp |
| `end_time` | integer | No | End time (Unix timestamp) | Any valid Unix timestamp |
| `bucket_width` | string | No | Time bucket size | Only `'1d'` supported (default) |
| `limit` | integer | No | Number of buckets to return | 1-500 (default: 7) |
| `page` | string | No | Pagination cursor | Opaque string from `next_page` |
| `project_ids` | array | No | Filter by project IDs | Array of project ID strings |
| `group_by` | array | No | Group results by fields | `["line_item", "project_id"]` |

### Response Schema

```json
{
  "object": "list",
  "data": [
    {
      "object": "bucket",
      "start_time": 1736553600,
      "end_time": 1736640000,
      "results": [
        {
          "object": "organization.costs.result",
          "amount": {
            "value": 15.42,
            "currency": "usd"
          },
          "line_item": "Chat models",
          "project_id": "proj_abc123",
          "organization_id": "org-xyz789"
        },
        {
          "object": "organization.costs.result",
          "amount": {
            "value": 0.52,
            "currency": "usd"
          },
          "line_item": "Embedding models",
          "project_id": "proj_abc123",
          "organization_id": "org-xyz789"
        }
      ]
    }
  ],
  "next_page": null
}
```

### Result Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | Always `"organization.costs.result"` |
| `amount` | object | Cost amount object |
| `amount.value` | float | Cost value |
| `amount.currency` | string | Currency code (always "usd") |
| `line_item` | string \| null | Invoice line item category (if grouped) |
| `project_id` | string \| null | Project ID (if filtered or grouped) |
| `organization_id` | string | Organization ID |

### Line Item Categories

Based on OpenAI's API structure, `line_item` values likely include:

| Line Item | Description |
|-----------|-------------|
| `"Chat models"` | Chat completion API costs (GPT-4, GPT-3.5, etc.) |
| `"Completion models"` | Legacy completion API costs |
| `"Embedding models"` | Embeddings API costs |
| `"Image models"` | DALL-E image generation costs |
| `"Audio models"` | TTS and Whisper audio processing costs |
| `"Vector storage"` | Vector store storage costs |
| `"Code interpreter"` | Code interpreter session costs |
| `"Fine-tuning"` | Fine-tuning training and hosting costs |
| `"Assistants API"` | Assistants API-specific costs |
| `"Batch API"` | Batch API processing costs |
| `"Cached input tokens"` | Prompt caching costs (if separate line item) |

**Note:** Exact line item values may vary. OpenAI's documentation should be consulted for the authoritative list.

---

## Request/Response Schemas

### Complete Pydantic Models for FakeAI

Below are the complete Pydantic model definitions for implementing these APIs in FakeAI:

```python
"""Usage and Billing API Models"""

from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


# ============================================================================
# Common Models
# ============================================================================

class BucketWidth(str, Enum):
    """Valid bucket width values."""
    MINUTE = "1m"
    HOUR = "1h"
    DAY = "1d"


class AmountObject(BaseModel):
    """Cost amount object."""
    value: float = Field(description="Cost value in currency units")
    currency: Literal["usd"] = Field(default="usd", description="Currency code")


class Bucket(BaseModel):
    """Time bucket container for usage/cost data."""
    object: Literal["bucket"] = Field(default="bucket", description="Object type")
    start_time: int = Field(description="Bucket start time (Unix timestamp)")
    end_time: int = Field(description="Bucket end time (Unix timestamp)")
    results: list[dict] = Field(description="Array of result objects")


# ============================================================================
# Usage API - Completions
# ============================================================================

class CompletionsUsageResult(BaseModel):
    """Result object for completions usage."""
    object: Literal["organization.usage.completions.result"] = Field(
        default="organization.usage.completions.result",
        description="Object type"
    )
    input_tokens: int = Field(description="Number of input tokens")
    output_tokens: int = Field(description="Number of output tokens")
    input_cached_tokens: int = Field(default=0, description="Number of cached input tokens")
    input_audio_tokens: int = Field(default=0, description="Number of input audio tokens")
    output_audio_tokens: int = Field(default=0, description="Number of output audio tokens")
    num_model_requests: int = Field(description="Number of API requests")
    project_id: str | None = Field(default=None, description="Project ID (if grouped)")
    user_id: str | None = Field(default=None, description="User ID (if grouped)")
    api_key_id: str | None = Field(default=None, description="API key ID (if grouped)")
    model: str | None = Field(default=None, description="Model name (if grouped)")
    batch: bool | None = Field(default=None, description="Batch status (if grouped)")


class CompletionsUsageRequest(BaseModel):
    """Request parameters for completions usage endpoint."""
    start_time: int = Field(description="Start time (Unix timestamp)")
    end_time: int | None = Field(default=None, description="End time (Unix timestamp)")
    bucket_width: BucketWidth = Field(default=BucketWidth.DAY, description="Bucket size")
    limit: int = Field(default=7, ge=1, le=500, description="Number of buckets")
    page: str | None = Field(default=None, description="Pagination cursor")
    project_ids: list[str] | None = Field(default=None, description="Filter by projects")
    user_ids: list[str] | None = Field(default=None, description="Filter by users")
    api_key_ids: list[str] | None = Field(default=None, description="Filter by API keys")
    models: list[str] | None = Field(default=None, description="Filter by models")
    batch: bool | None = Field(default=None, description="Filter by batch status")
    group_by: list[str] | None = Field(
        default=None,
        description="Group by fields: project_id, user_id, api_key_id, model, batch"
    )


class CompletionsUsageResponse(BaseModel):
    """Response for completions usage endpoint."""
    object: Literal["list"] = Field(default="list", description="Object type")
    data: list[Bucket] = Field(description="Array of time buckets")
    next_page: str | None = Field(default=None, description="Pagination cursor")


# ============================================================================
# Usage API - Embeddings
# ============================================================================

class EmbeddingsUsageResult(BaseModel):
    """Result object for embeddings usage."""
    object: Literal["organization.usage.embeddings.result"] = Field(
        default="organization.usage.embeddings.result",
        description="Object type"
    )
    input_tokens: int = Field(description="Number of input tokens")
    num_model_requests: int = Field(description="Number of API requests")
    project_id: str | None = Field(default=None, description="Project ID (if grouped)")
    user_id: str | None = Field(default=None, description="User ID (if grouped)")
    api_key_id: str | None = Field(default=None, description="API key ID (if grouped)")
    model: str | None = Field(default=None, description="Model name (if grouped)")


class EmbeddingsUsageRequest(BaseModel):
    """Request parameters for embeddings usage endpoint."""
    start_time: int = Field(description="Start time (Unix timestamp)")
    end_time: int | None = Field(default=None, description="End time (Unix timestamp)")
    bucket_width: BucketWidth = Field(default=BucketWidth.DAY, description="Bucket size")
    limit: int = Field(default=7, ge=1, le=500, description="Number of buckets")
    page: str | None = Field(default=None, description="Pagination cursor")
    project_ids: list[str] | None = Field(default=None, description="Filter by projects")
    user_ids: list[str] | None = Field(default=None, description="Filter by users")
    api_key_ids: list[str] | None = Field(default=None, description="Filter by API keys")
    models: list[str] | None = Field(default=None, description="Filter by models")
    group_by: list[str] | None = Field(
        default=None,
        description="Group by fields: project_id, user_id, api_key_id, model"
    )


class EmbeddingsUsageResponse(BaseModel):
    """Response for embeddings usage endpoint."""
    object: Literal["list"] = Field(default="list", description="Object type")
    data: list[Bucket] = Field(description="Array of time buckets")
    next_page: str | None = Field(default=None, description="Pagination cursor")


# ============================================================================
# Usage API - Images
# ============================================================================

class ImagesUsageResult(BaseModel):
    """Result object for images usage."""
    object: Literal["organization.usage.images.result"] = Field(
        default="organization.usage.images.result",
        description="Object type"
    )
    num_images: int = Field(description="Number of images generated")
    num_model_requests: int = Field(description="Number of API requests")
    source: str | None = Field(default=None, description="Generation source (if grouped)")
    size: str | None = Field(default=None, description="Image size (if grouped)")
    project_id: str | None = Field(default=None, description="Project ID (if grouped)")
    user_id: str | None = Field(default=None, description="User ID (if grouped)")
    api_key_id: str | None = Field(default=None, description="API key ID (if grouped)")


class ImagesUsageRequest(BaseModel):
    """Request parameters for images usage endpoint."""
    start_time: int = Field(description="Start time (Unix timestamp)")
    end_time: int | None = Field(default=None, description="End time (Unix timestamp)")
    bucket_width: BucketWidth = Field(default=BucketWidth.DAY, description="Bucket size")
    limit: int = Field(default=7, ge=1, le=500, description="Number of buckets")
    page: str | None = Field(default=None, description="Pagination cursor")
    sources: list[str] | None = Field(default=None, description="Filter by sources")
    sizes: list[str] | None = Field(default=None, description="Filter by sizes")
    project_ids: list[str] | None = Field(default=None, description="Filter by projects")
    user_ids: list[str] | None = Field(default=None, description="Filter by users")
    api_key_ids: list[str] | None = Field(default=None, description="Filter by API keys")
    group_by: list[str] | None = Field(
        default=None,
        description="Group by fields: source, size, project_id, user_id, api_key_id"
    )


class ImagesUsageResponse(BaseModel):
    """Response for images usage endpoint."""
    object: Literal["list"] = Field(default="list", description="Object type")
    data: list[Bucket] = Field(description="Array of time buckets")
    next_page: str | None = Field(default=None, description="Pagination cursor")


# ============================================================================
# Usage API - Audio
# ============================================================================

class AudioUsageResult(BaseModel):
    """Result object for audio usage."""
    object: Literal["organization.usage.audio.result"] = Field(
        default="organization.usage.audio.result",
        description="Object type"
    )
    num_seconds: int = Field(description="Number of audio seconds processed")
    num_model_requests: int = Field(description="Number of API requests")
    model: str | None = Field(default=None, description="Model name (if grouped)")
    project_id: str | None = Field(default=None, description="Project ID (if grouped)")
    user_id: str | None = Field(default=None, description="User ID (if grouped)")
    api_key_id: str | None = Field(default=None, description="API key ID (if grouped)")


class AudioUsageRequest(BaseModel):
    """Request parameters for audio usage endpoint."""
    start_time: int = Field(description="Start time (Unix timestamp)")
    end_time: int | None = Field(default=None, description="End time (Unix timestamp)")
    bucket_width: BucketWidth = Field(default=BucketWidth.DAY, description="Bucket size")
    limit: int = Field(default=7, ge=1, le=500, description="Number of buckets")
    page: str | None = Field(default=None, description="Pagination cursor")
    models: list[str] | None = Field(default=None, description="Filter by models")
    project_ids: list[str] | None = Field(default=None, description="Filter by projects")
    user_ids: list[str] | None = Field(default=None, description="Filter by users")
    api_key_ids: list[str] | None = Field(default=None, description="Filter by API keys")
    group_by: list[str] | None = Field(
        default=None,
        description="Group by fields: model, project_id, user_id, api_key_id"
    )


class AudioUsageResponse(BaseModel):
    """Response for audio usage endpoint."""
    object: Literal["list"] = Field(default="list", description="Object type")
    data: list[Bucket] = Field(description="Array of time buckets")
    next_page: str | None = Field(default=None, description="Pagination cursor")


# ============================================================================
# Usage API - Moderations
# ============================================================================

class ModerationsUsageResult(BaseModel):
    """Result object for moderations usage."""
    object: Literal["organization.usage.moderations.result"] = Field(
        default="organization.usage.moderations.result",
        description="Object type"
    )
    num_model_requests: int = Field(description="Number of moderation requests")
    project_id: str | None = Field(default=None, description="Project ID (if grouped)")
    user_id: str | None = Field(default=None, description="User ID (if grouped)")
    api_key_id: str | None = Field(default=None, description="API key ID (if grouped)")


class ModerationsUsageRequest(BaseModel):
    """Request parameters for moderations usage endpoint."""
    start_time: int = Field(description="Start time (Unix timestamp)")
    end_time: int | None = Field(default=None, description="End time (Unix timestamp)")
    bucket_width: BucketWidth = Field(default=BucketWidth.DAY, description="Bucket size")
    limit: int = Field(default=7, ge=1, le=500, description="Number of buckets")
    page: str | None = Field(default=None, description="Pagination cursor")
    project_ids: list[str] | None = Field(default=None, description="Filter by projects")
    user_ids: list[str] | None = Field(default=None, description="Filter by users")
    api_key_ids: list[str] | None = Field(default=None, description="Filter by API keys")
    group_by: list[str] | None = Field(
        default=None,
        description="Group by fields: project_id, user_id, api_key_id"
    )


class ModerationsUsageResponse(BaseModel):
    """Response for moderations usage endpoint."""
    object: Literal["list"] = Field(default="list", description="Object type")
    data: list[Bucket] = Field(description="Array of time buckets")
    next_page: str | None = Field(default=None, description="Pagination cursor")


# ============================================================================
# Usage API - Vector Stores
# ============================================================================

class VectorStoresUsageResult(BaseModel):
    """Result object for vector stores usage."""
    object: Literal["organization.usage.vector_stores.result"] = Field(
        default="organization.usage.vector_stores.result",
        description="Object type"
    )
    usage_bytes: int = Field(description="Number of bytes stored")
    num_vector_stores: int = Field(description="Number of vector stores")
    project_id: str | None = Field(default=None, description="Project ID (if grouped)")


class VectorStoresUsageRequest(BaseModel):
    """Request parameters for vector stores usage endpoint."""
    start_time: int = Field(description="Start time (Unix timestamp)")
    end_time: int | None = Field(default=None, description="End time (Unix timestamp)")
    bucket_width: BucketWidth = Field(default=BucketWidth.DAY, description="Bucket size")
    limit: int = Field(default=7, ge=1, le=500, description="Number of buckets")
    page: str | None = Field(default=None, description="Pagination cursor")
    project_ids: list[str] | None = Field(default=None, description="Filter by projects")
    group_by: list[str] | None = Field(
        default=None,
        description="Group by fields: project_id"
    )


class VectorStoresUsageResponse(BaseModel):
    """Response for vector stores usage endpoint."""
    object: Literal["list"] = Field(default="list", description="Object type")
    data: list[Bucket] = Field(description="Array of time buckets")
    next_page: str | None = Field(default=None, description="Pagination cursor")


# ============================================================================
# Usage API - Code Interpreter Sessions
# ============================================================================

class CodeInterpreterSessionsUsageResult(BaseModel):
    """Result object for code interpreter sessions usage."""
    object: Literal["organization.usage.code_interpreter_sessions.result"] = Field(
        default="organization.usage.code_interpreter_sessions.result",
        description="Object type"
    )
    num_sessions: int = Field(description="Number of code interpreter sessions")
    project_id: str | None = Field(default=None, description="Project ID (if grouped)")


class CodeInterpreterSessionsUsageRequest(BaseModel):
    """Request parameters for code interpreter sessions usage endpoint."""
    start_time: int = Field(description="Start time (Unix timestamp)")
    end_time: int | None = Field(default=None, description="End time (Unix timestamp)")
    bucket_width: BucketWidth = Field(default=BucketWidth.DAY, description="Bucket size")
    limit: int = Field(default=7, ge=1, le=500, description="Number of buckets")
    page: str | None = Field(default=None, description="Pagination cursor")
    project_ids: list[str] | None = Field(default=None, description="Filter by projects")
    group_by: list[str] | None = Field(
        default=None,
        description="Group by fields: project_id"
    )


class CodeInterpreterSessionsUsageResponse(BaseModel):
    """Response for code interpreter sessions usage endpoint."""
    object: Literal["list"] = Field(default="list", description="Object type")
    data: list[Bucket] = Field(description="Array of time buckets")
    next_page: str | None = Field(default=None, description="Pagination cursor")


# ============================================================================
# Costs API
# ============================================================================

class CostsResult(BaseModel):
    """Result object for costs."""
    object: Literal["organization.costs.result"] = Field(
        default="organization.costs.result",
        description="Object type"
    )
    amount: AmountObject = Field(description="Cost amount")
    line_item: str | None = Field(default=None, description="Line item category (if grouped)")
    project_id: str | None = Field(default=None, description="Project ID (if filtered/grouped)")
    organization_id: str = Field(description="Organization ID")


class CostsRequest(BaseModel):
    """Request parameters for costs endpoint."""
    start_time: int = Field(description="Start time (Unix timestamp)")
    end_time: int | None = Field(default=None, description="End time (Unix timestamp)")
    bucket_width: Literal["1d"] = Field(default="1d", description="Bucket size (only '1d' supported)")
    limit: int = Field(default=7, ge=1, le=500, description="Number of buckets")
    page: str | None = Field(default=None, description="Pagination cursor")
    project_ids: list[str] | None = Field(default=None, description="Filter by projects")
    group_by: list[str] | None = Field(
        default=None,
        description="Group by fields: line_item, project_id"
    )


class CostsResponse(BaseModel):
    """Response for costs endpoint."""
    object: Literal["list"] = Field(default="list", description="Object type")
    data: list[Bucket] = Field(description="Array of time buckets")
    next_page: str | None = Field(default=None, description="Pagination cursor")
```

---

## Cost Calculation Methods

### Token-Based Pricing

Most models use token-based pricing with separate rates for input and output tokens.

#### Pricing Formula

```python
def calculate_completion_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
    audio_input_tokens: int = 0,
    audio_output_tokens: int = 0
) -> float:
    """Calculate cost for completion API request."""

    # Get pricing for model
    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)

    # Calculate base cost
    input_cost = (input_tokens * pricing["input_per_1m"]) / 1_000_000
    output_cost = (output_tokens * pricing["output_per_1m"]) / 1_000_000

    # Calculate cached token cost (typically 50% discount)
    cached_cost = (cached_tokens * pricing.get("cached_per_1m", pricing["input_per_1m"] * 0.5)) / 1_000_000

    # Calculate audio token costs (if applicable)
    audio_input_cost = 0
    audio_output_cost = 0
    if audio_input_tokens > 0:
        audio_input_cost = (audio_input_tokens * pricing.get("audio_input_per_1m", pricing["input_per_1m"])) / 1_000_000
    if audio_output_tokens > 0:
        audio_output_cost = (audio_output_tokens * pricing.get("audio_output_per_1m", pricing["output_per_1m"])) / 1_000_000

    # Total cost
    return input_cost + output_cost + cached_cost + audio_input_cost + audio_output_cost
```

#### Model Pricing Table (2025)

```python
MODEL_PRICING = {
    # GPT-4 models
    "openai/gpt-oss-120b": {
        "input_per_1m": 30.00,
        "output_per_1m": 60.00,
    },
    "openai/gpt-oss-120b-32k": {
        "input_per_1m": 60.00,
        "output_per_1m": 120.00,
    },
    "openai/gpt-oss-120b": {
        "input_per_1m": 10.00,
        "output_per_1m": 30.00,
    },
    "openai/gpt-oss-120b-preview": {
        "input_per_1m": 10.00,
        "output_per_1m": 30.00,
    },
    "openai/gpt-oss-120b": {
        "input_per_1m": 5.00,
        "output_per_1m": 15.00,
        "cached_per_1m": 2.50,  # 50% discount for cached tokens
    },
    "openai/gpt-oss-20b": {
        "input_per_1m": 0.15,
        "output_per_1m": 0.60,
        "cached_per_1m": 0.075,
    },

    # GPT-3.5 models
    "meta-llama/Llama-3.1-8B-Instruct": {
        "input_per_1m": 0.50,
        "output_per_1m": 1.50,
    },
    "meta-llama/Llama-3.1-8B-Instruct-0125": {
        "input_per_1m": 0.50,
        "output_per_1m": 1.50,
    },
    "meta-llama/Llama-3.1-8B-Instruct-16k": {
        "input_per_1m": 3.00,
        "output_per_1m": 4.00,
    },

    # Embeddings models
    "nomic-ai/nomic-embed-text-v1.5": {
        "input_per_1m": 0.02,
        "output_per_1m": 0.00,  # No output tokens
    },
    "BAAI/bge-m3": {
        "input_per_1m": 0.13,
        "output_per_1m": 0.00,
    },
    "sentence-transformers/all-mpnet-base-v2": {
        "input_per_1m": 0.10,
        "output_per_1m": 0.00,
    },
}
```

### Image-Based Pricing

Image generation uses per-image pricing based on model, size, and quality.

#### Pricing Formula

```python
def calculate_image_cost(
    model: str,
    size: str,
    quality: str,
    num_images: int
) -> float:
    """Calculate cost for image generation."""

    # DALL-E 3 pricing
    if model == "stabilityai/stable-diffusion-xl-base-1.0":
        if quality == "hd":
            if size == "1024x1024":
                per_image = 0.080
            elif size == "1792x1024" or size == "1024x1792":
                per_image = 0.120
            else:
                per_image = 0.080
        else:  # standard quality
            if size == "1024x1024":
                per_image = 0.040
            elif size == "1792x1024" or size == "1024x1792":
                per_image = 0.080
            else:
                per_image = 0.040

    # DALL-E 2 pricing
    elif model == "stabilityai/stable-diffusion-2-1":
        if size == "1024x1024":
            per_image = 0.020
        elif size == "512x512":
            per_image = 0.018
        elif size == "256x256":
            per_image = 0.016
        else:
            per_image = 0.020

    else:
        per_image = 0.040  # Default

    return per_image * num_images
```

#### Image Pricing Table (2025)

```python
IMAGE_PRICING = {
    "stabilityai/stable-diffusion-xl-base-1.0": {
        "standard": {
            "1024x1024": 0.040,
            "1792x1024": 0.080,
            "1024x1792": 0.080,
        },
        "hd": {
            "1024x1024": 0.080,
            "1792x1024": 0.120,
            "1024x1792": 0.120,
        },
    },
    "stabilityai/stable-diffusion-2-1": {
        "1024x1024": 0.020,
        "512x512": 0.018,
        "256x256": 0.016,
    },
}
```

### Audio-Based Pricing

Audio uses per-second or per-minute pricing.

#### Pricing Formula

```python
def calculate_audio_cost(
    model: str,
    num_seconds: int
) -> float:
    """Calculate cost for audio processing."""

    # Whisper pricing (per minute)
    if model == "whisper-1":
        minutes = num_seconds / 60.0
        return minutes * 0.006

    # TTS pricing (per 1M characters, approximated from seconds)
    elif model.startswith("tts-"):
        # Assume ~150 characters per second of speech
        characters = num_seconds * 150
        if model == "tts-1":
            return (characters / 1_000_000) * 15.00
        elif model == "tts-1-hd":
            return (characters / 1_000_000) * 30.00

    return 0.0
```

#### Audio Pricing Table (2025)

```python
AUDIO_PRICING = {
    "whisper-1": {
        "per_minute": 0.006,
    },
    "tts-1": {
        "per_1m_chars": 15.00,
    },
    "tts-1-hd": {
        "per_1m_chars": 30.00,
    },
}
```

### Aggregation Methods

#### Daily Aggregation

```python
def aggregate_costs_by_day(
    usage_data: list[dict],
    start_time: int,
    end_time: int
) -> list[dict]:
    """Aggregate costs into daily buckets."""

    # Group by day
    daily_costs = defaultdict(lambda: defaultdict(float))

    for record in usage_data:
        # Convert timestamp to day bucket
        day_timestamp = (record["timestamp"] // 86400) * 86400

        # Calculate cost for this record
        cost = calculate_completion_cost(
            model=record["model"],
            input_tokens=record["input_tokens"],
            output_tokens=record["output_tokens"],
        )

        # Aggregate by day and line item
        line_item = get_line_item_for_model(record["model"])
        daily_costs[day_timestamp][line_item] += cost

    # Convert to bucket format
    buckets = []
    for day_timestamp, line_items in sorted(daily_costs.items()):
        if day_timestamp < start_time or day_timestamp >= end_time:
            continue

        results = []
        for line_item, cost in line_items.items():
            results.append({
                "object": "organization.costs.result",
                "amount": {
                    "value": round(cost, 4),
                    "currency": "usd"
                },
                "line_item": line_item,
                "project_id": None,
                "organization_id": "org-simulated"
            })

        buckets.append({
            "object": "bucket",
            "start_time": day_timestamp,
            "end_time": day_timestamp + 86400,
            "results": results
        })

    return buckets
```

#### Group By Aggregation

```python
def aggregate_with_grouping(
    usage_data: list[dict],
    group_by: list[str]
) -> dict:
    """Aggregate usage data with grouping."""

    grouped = defaultdict(lambda: {
        "input_tokens": 0,
        "output_tokens": 0,
        "num_requests": 0,
    })

    for record in usage_data:
        # Build grouping key
        key_parts = []
        for field in group_by:
            key_parts.append(str(record.get(field, "null")))
        key = "|".join(key_parts)

        # Aggregate
        grouped[key]["input_tokens"] += record.get("input_tokens", 0)
        grouped[key]["output_tokens"] += record.get("output_tokens", 0)
        grouped[key]["num_requests"] += 1

    # Convert to results array
    results = []
    for key, totals in grouped.items():
        result = {
            "object": "organization.usage.completions.result",
            "input_tokens": totals["input_tokens"],
            "output_tokens": totals["output_tokens"],
            "num_model_requests": totals["num_requests"],
        }

        # Add grouping fields
        key_parts = key.split("|")
        for i, field in enumerate(group_by):
            value = key_parts[i]
            result[field] = None if value == "null" else value

        results.append(result)

    return results
```

---

## Implementation Guide for FakeAI

### High-Level Architecture

```

         FastAPI Application Layer           
  (app.py - New usage/costs endpoints)       

                  

        Usage Tracking Service               
  (usage_service.py - NEW module)            
  - Track all API calls                      
  - Store usage records                      
  - Aggregate by time/dimensions             
  - Calculate costs                          

                  

         In-Memory Storage                   
  - Usage records (time-series data)         
  - Aggregated buckets (cached)              
  - Model pricing table                      

```

### Step 1: Add Models to models.py

Add all the Pydantic models from the "Request/Response Schemas" section above to `/home/anthony/projects/fakeai/fakeai/models.py`.

### Step 2: Create Usage Service

Create a new file `/home/anthony/projects/fakeai/fakeai/usage_service.py`:

```python
"""
Usage and Billing Tracking Service

This module tracks simulated API usage and provides the usage and costs APIs.
"""

import time
from collections import defaultdict
from typing import Any

from fakeai.models import (
    Bucket,
    BucketWidth,
    CompletionsUsageResult,
    EmbeddingsUsageResult,
    ImagesUsageResult,
    AudioUsageResult,
    CostsResult,
    AmountObject,
)


class UsageTracker:
    """
    Singleton class to track API usage for FakeAI.

    Records all API calls and provides aggregated usage/cost data.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UsageTracker, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Usage records (in-memory storage)
        self.completion_records = []
        self.embedding_records = []
        self.image_records = []
        self.audio_records = []
        self.moderation_records = []

        # Pricing tables
        self._init_pricing()

        self._initialized = True

    def _init_pricing(self):
        """Initialize pricing tables."""
        self.model_pricing = {
            # GPT-4 models
            "openai/gpt-oss-120b": {"input_per_1m": 30.00, "output_per_1m": 60.00},
            "openai/gpt-oss-120b-32k": {"input_per_1m": 60.00, "output_per_1m": 120.00},
            "openai/gpt-oss-120b": {"input_per_1m": 10.00, "output_per_1m": 30.00},
            "openai/gpt-oss-120b": {"input_per_1m": 5.00, "output_per_1m": 15.00, "cached_per_1m": 2.50},
            "openai/gpt-oss-20b": {"input_per_1m": 0.15, "output_per_1m": 0.60, "cached_per_1m": 0.075},

            # GPT-3.5 models
            "meta-llama/Llama-3.1-8B-Instruct": {"input_per_1m": 0.50, "output_per_1m": 1.50},
            "meta-llama/Llama-3.1-8B-Instruct-16k": {"input_per_1m": 3.00, "output_per_1m": 4.00},

            # Embeddings
            "nomic-ai/nomic-embed-text-v1.5": {"input_per_1m": 0.02, "output_per_1m": 0.00},
            "BAAI/bge-m3": {"input_per_1m": 0.13, "output_per_1m": 0.00},
            "sentence-transformers/all-mpnet-base-v2": {"input_per_1m": 0.10, "output_per_1m": 0.00},
        }

        self.image_pricing = {
            "stabilityai/stable-diffusion-xl-base-1.0": {
                "standard": {"1024x1024": 0.040, "1792x1024": 0.080, "1024x1792": 0.080},
                "hd": {"1024x1024": 0.080, "1792x1024": 0.120, "1024x1792": 0.120},
            },
            "stabilityai/stable-diffusion-2-1": {"1024x1024": 0.020, "512x512": 0.018, "256x256": 0.016},
        }

    def track_completion(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
        audio_input_tokens: int = 0,
        audio_output_tokens: int = 0,
        project_id: str | None = None,
        user_id: str | None = None,
        api_key_id: str | None = None,
        batch: bool = False,
    ):
        """Track a completion API call."""
        record = {
            "timestamp": int(time.time()),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cached_tokens": cached_tokens,
            "input_audio_tokens": audio_input_tokens,
            "output_audio_tokens": audio_output_tokens,
            "project_id": project_id,
            "user_id": user_id,
            "api_key_id": api_key_id,
            "batch": batch,
        }
        self.completion_records.append(record)

    def track_embedding(
        self,
        model: str,
        input_tokens: int,
        project_id: str | None = None,
        user_id: str | None = None,
        api_key_id: str | None = None,
    ):
        """Track an embeddings API call."""
        record = {
            "timestamp": int(time.time()),
            "model": model,
            "input_tokens": input_tokens,
            "project_id": project_id,
            "user_id": user_id,
            "api_key_id": api_key_id,
        }
        self.embedding_records.append(record)

    def track_image(
        self,
        source: str,
        size: str,
        quality: str,
        num_images: int,
        project_id: str | None = None,
        user_id: str | None = None,
        api_key_id: str | None = None,
    ):
        """Track an image generation API call."""
        record = {
            "timestamp": int(time.time()),
            "source": source,
            "size": size,
            "quality": quality,
            "num_images": num_images,
            "project_id": project_id,
            "user_id": user_id,
            "api_key_id": api_key_id,
        }
        self.image_records.append(record)

    def get_completions_usage(
        self,
        start_time: int,
        end_time: int | None,
        bucket_width: BucketWidth,
        group_by: list[str] | None,
        filters: dict[str, Any],
    ) -> list[Bucket]:
        """Get completions usage data."""
        # Filter records by time range
        records = [
            r for r in self.completion_records
            if start_time <= r["timestamp"] < (end_time or int(time.time()) + 86400)
        ]

        # Apply filters
        records = self._apply_filters(records, filters)

        # Aggregate by bucket and grouping
        buckets = self._aggregate_completions(records, start_time, end_time, bucket_width, group_by)

        return buckets

    def get_costs(
        self,
        start_time: int,
        end_time: int | None,
        group_by: list[str] | None,
        project_ids: list[str] | None,
    ) -> list[Bucket]:
        """Get cost data."""
        # Collect all records
        all_records = []

        # Add completion costs
        for record in self.completion_records:
            if start_time <= record["timestamp"] < (end_time or int(time.time()) + 86400):
                if project_ids and record.get("project_id") not in project_ids:
                    continue

                cost = self._calculate_completion_cost(record)
                all_records.append({
                    "timestamp": record["timestamp"],
                    "cost": cost,
                    "line_item": "Chat models",
                    "project_id": record.get("project_id"),
                })

        # Add embedding costs
        for record in self.embedding_records:
            if start_time <= record["timestamp"] < (end_time or int(time.time()) + 86400):
                if project_ids and record.get("project_id") not in project_ids:
                    continue

                cost = self._calculate_embedding_cost(record)
                all_records.append({
                    "timestamp": record["timestamp"],
                    "cost": cost,
                    "line_item": "Embedding models",
                    "project_id": record.get("project_id"),
                })

        # Add image costs
        for record in self.image_records:
            if start_time <= record["timestamp"] < (end_time or int(time.time()) + 86400):
                if project_ids and record.get("project_id") not in project_ids:
                    continue

                cost = self._calculate_image_cost(record)
                all_records.append({
                    "timestamp": record["timestamp"],
                    "cost": cost,
                    "line_item": "Image models",
                    "project_id": record.get("project_id"),
                })

        # Aggregate by day
        buckets = self._aggregate_costs(all_records, start_time, end_time, group_by)

        return buckets

    def _calculate_completion_cost(self, record: dict) -> float:
        """Calculate cost for a completion record."""
        pricing = self.model_pricing.get(record["model"], {"input_per_1m": 0.50, "output_per_1m": 1.50})

        input_cost = (record["input_tokens"] * pricing["input_per_1m"]) / 1_000_000
        output_cost = (record["output_tokens"] * pricing["output_per_1m"]) / 1_000_000

        cached_cost = 0
        if record.get("input_cached_tokens", 0) > 0:
            cached_rate = pricing.get("cached_per_1m", pricing["input_per_1m"] * 0.5)
            cached_cost = (record["input_cached_tokens"] * cached_rate) / 1_000_000

        return input_cost + output_cost + cached_cost

    def _calculate_embedding_cost(self, record: dict) -> float:
        """Calculate cost for an embedding record."""
        pricing = self.model_pricing.get(record["model"], {"input_per_1m": 0.10, "output_per_1m": 0.00})
        return (record["input_tokens"] * pricing["input_per_1m"]) / 1_000_000

    def _calculate_image_cost(self, record: dict) -> float:
        """Calculate cost for an image record."""
        source = record["source"]
        size = record["size"]
        quality = record.get("quality", "standard")

        if source == "stabilityai/stable-diffusion-xl-base-1.0":
            per_image = self.image_pricing["stabilityai/stable-diffusion-xl-base-1.0"].get(quality, {}).get(size, 0.040)
        elif source == "stabilityai/stable-diffusion-2-1":
            per_image = self.image_pricing["stabilityai/stable-diffusion-2-1"].get(size, 0.020)
        else:
            per_image = 0.040

        return per_image * record["num_images"]

    # Implement aggregation methods...
    # (See full implementation in next section)
```

### Step 3: Integrate with FakeAIService

Update `/home/anthony/projects/fakeai/fakeai/fakeai_service.py` to track usage:

```python
from fakeai.usage_service import UsageTracker

class FakeAIService:
    def __init__(self, config: AppConfig):
        # ... existing code ...
        self.usage_tracker = UsageTracker()

    async def create_chat_completion(self, request):
        # ... existing implementation ...

        # Track usage
        self.usage_tracker.track_completion(
            model=request.model,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            cached_tokens=0,  # Implement caching if needed
            project_id=None,  # Extract from request headers if available
            user_id=None,
            api_key_id=None,
        )

        return response
```

### Step 4: Add Endpoints to app.py

Add new endpoints to `/home/anthony/projects/fakeai/fakeai/app.py`:

```python
@app.get("/v1/organization/usage/completions")
async def get_completions_usage(
    start_time: int,
    end_time: int | None = None,
    bucket_width: str = "1d",
    limit: int = 7,
    page: str | None = None,
    project_ids: list[str] | None = Query(default=None),
    models: list[str] | None = Query(default=None),
    group_by: list[str] | None = Query(default=None),
):
    """Get completions usage data."""
    return fakeai_service.usage_tracker.get_completions_usage(
        start_time=start_time,
        end_time=end_time,
        bucket_width=BucketWidth(bucket_width),
        group_by=group_by,
        filters={
            "project_ids": project_ids,
            "models": models,
        }
    )


@app.get("/v1/organization/costs")
async def get_costs(
    start_time: int,
    end_time: int | None = None,
    bucket_width: str = "1d",
    limit: int = 7,
    page: str | None = None,
    project_ids: list[str] | None = Query(default=None),
    group_by: list[str] | None = Query(default=None),
):
    """Get cost data."""
    return fakeai_service.usage_tracker.get_costs(
        start_time=start_time,
        end_time=end_time,
        group_by=group_by,
        project_ids=project_ids,
    )
```

### Step 5: Testing

Create test script `/home/anthony/projects/fakeai/examples/test_usage_api.py`:

```python
"""Test usage and costs APIs."""

import time
import requests

BASE_URL = "http://localhost:8000"

# Make some API calls to generate usage data
for i in range(10):
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": f"Test message {i}"}],
        }
    )
    print(f"Request {i}: {response.status_code}")

time.sleep(1)

# Query usage API
start_time = int(time.time()) - 3600  # Last hour
response = requests.get(
    f"{BASE_URL}/v1/organization/usage/completions",
    params={"start_time": start_time, "bucket_width": "1h"}
)
print("\nCompletions Usage:")
print(response.json())

# Query costs API
response = requests.get(
    f"{BASE_URL}/v1/organization/costs",
    params={"start_time": start_time}
)
print("\nCosts:")
print(response.json())
```

---

## Appendix: Pricing Reference

### Complete Pricing Table (2025)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Cached Input |
|-------|----------------------|------------------------|--------------|
| **GPT-4 Family** |
| openai/gpt-oss-120b | $30.00 | $60.00 | N/A |
| openai/gpt-oss-120b-32k | $60.00 | $120.00 | N/A |
| openai/gpt-oss-120b | $10.00 | $30.00 | N/A |
| openai/gpt-oss-120b | $5.00 | $15.00 | $2.50 |
| openai/gpt-oss-20b | $0.15 | $0.60 | $0.075 |
| **GPT-3.5 Family** |
| meta-llama/Llama-3.1-8B-Instruct | $0.50 | $1.50 | N/A |
| meta-llama/Llama-3.1-8B-Instruct-16k | $3.00 | $4.00 | N/A |
| **Embeddings** |
| nomic-ai/nomic-embed-text-v1.5 | $0.02 | N/A | N/A |
| BAAI/bge-m3 | $0.13 | N/A | N/A |
| sentence-transformers/all-mpnet-base-v2 | $0.10 | N/A | N/A |
| **Images** |
| DALL-E 3 (1024x1024, standard) | $0.040 per image | | |
| DALL-E 3 (1024x1024, HD) | $0.080 per image | | |
| DALL-E 3 (1792x1024, standard) | $0.080 per image | | |
| DALL-E 3 (1792x1024, HD) | $0.120 per image | | |
| DALL-E 2 (1024x1024) | $0.020 per image | | |
| DALL-E 2 (512x512) | $0.018 per image | | |
| DALL-E 2 (256x256) | $0.016 per image | | |
| **Audio** |
| Whisper (speech-to-text) | $0.006 per minute | | |
| TTS (text-to-speech) | $15.00 per 1M chars | | |
| TTS HD | $30.00 per 1M chars | | |

### Token Estimation

- **Average:** ~4 characters per token
- **Rule of thumb:** 1 word ≈ 1.4 tokens
- **Punctuation:** Each punctuation mark ≈ 1 token

### Cost Examples

**Example 1: GPT-4 Chat Completion**
- Input: 1,000 tokens
- Output: 500 tokens
- Cost: (1,000 × $30.00 / 1M) + (500 × $60.00 / 1M) = $0.03 + $0.03 = **$0.06**

**Example 2: GPT-3.5 Turbo**
- Input: 1,000 tokens
- Output: 500 tokens
- Cost: (1,000 × $0.50 / 1M) + (500 × $1.50 / 1M) = $0.0005 + $0.00075 = **$0.00125**

**Example 3: Embeddings**
- Input: 10,000 tokens (nomic-ai/nomic-embed-text-v1.5)
- Cost: 10,000 × $0.02 / 1M = **$0.0002**

**Example 4: DALL-E 3 Images**
- Size: 1024x1024, HD quality
- Images: 5
- Cost: 5 × $0.080 = **$0.40**

---

## Summary

OpenAI's Usage and Billing APIs provide comprehensive programmatic access to:

1. **Granular usage tracking** across all API endpoints (completions, embeddings, images, audio, etc.)
2. **Flexible time aggregation** (minute, hour, day buckets)
3. **Multi-dimensional grouping** (by project, user, API key, model)
4. **Cost reconciliation** with billing invoices via the Costs endpoint
5. **Pagination support** for large datasets

For FakeAI implementation:
- Track all API calls in memory
- Calculate costs using official pricing tables
- Aggregate by time buckets and dimensions
- Return data in OpenAI-compatible formats
- Support all filtering and grouping options

The implementation should prioritize **simplicity** and **compatibility** over perfect accuracy, as FakeAI is designed for testing and development purposes.

---

**End of Research Report**
