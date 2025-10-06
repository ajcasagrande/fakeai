# Fine-Tuning API Research Report

**Date:** 2025-10-04
**Purpose:** Research fine-tuning APIs from OpenAI and other providers for potential FakeAI implementation
**Version:** 1.0

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [OpenAI Fine-Tuning API](#openai-fine-tuning-api)
3. [Azure OpenAI Fine-Tuning](#azure-openai-fine-tuning)
4. [Anthropic Claude Fine-Tuning](#anthropic-claude-fine-tuning)
5. [Training Data Format (JSONL)](#training-data-format-jsonl)
6. [Fine-Tuning Methods](#fine-tuning-methods)
7. [Implementation Strategy for FakeAI](#implementation-strategy-for-fakeai)
8. [Complete API Schemas](#complete-api-schemas)
9. [Cost and Pricing Models](#cost-and-pricing-models)
10. [Appendix: Code Examples](#appendix-code-examples)

---

## 1. Executive Summary

Fine-tuning APIs allow developers to customize pre-trained language models for specific tasks using their own training data. This research covers:

- **OpenAI Fine-Tuning API**: Primary reference implementation with comprehensive endpoints
- **Azure OpenAI**: Enterprise variant with additional features and token-based billing
- **Anthropic Claude**: Limited fine-tuning via Amazon Bedrock only
- **Three Fine-Tuning Methods**: Supervised (SFT), Direct Preference Optimization (DPO), and Reinforcement (RFT)
- **JSONL Training Format**: Conversational format with system/user/assistant roles
- **Job Lifecycle**: 6 status states from validation to completion
- **Checkpoints**: Epoch-based model artifacts with validation metrics

**Key Finding**: OpenAI's fine-tuning API is comprehensive and well-documented, making it the ideal target for FakeAI simulation implementation.

---

## 2. OpenAI Fine-Tuning API

### 2.1 API Endpoints

#### 2.1.1 Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/fine_tuning/jobs` | POST | Create a fine-tuning job |
| `/v1/fine_tuning/jobs` | GET | List fine-tuning jobs (paginated) |
| `/v1/fine_tuning/jobs/{job_id}` | GET | Retrieve specific job details |
| `/v1/fine_tuning/jobs/{job_id}/cancel` | POST | Cancel a running job |
| `/v1/fine_tuning/jobs/{job_id}/events` | GET | List job events (with streaming) |
| `/v1/fine_tuning/jobs/{job_id}/checkpoints` | GET | List job checkpoints |

#### 2.1.2 Job Lifecycle States

Fine-tuning jobs progress through the following states:

1. **`validating_files`** - Initial validation of training and validation files
2. **`queued`** - Job is queued and waiting for resources
3. **`running`** - Job is actively training
4. **`succeeded`** - Job completed successfully
5. **`failed`** - Job failed (check error field for details)
6. **`cancelled`** - Job was cancelled by user

### 2.2 Request/Response Schemas

#### 2.2.1 Create Fine-Tuning Job

**Endpoint:** `POST /v1/fine_tuning/jobs`

**Request Body:**
```json
{
  "model": "openai/gpt-oss-20b-2024-07-18",           // Required: Base model ID
  "training_file": "file-abc123",               // Required: Training file ID
  "validation_file": "file-xyz789",             // Optional: Validation file ID
  "hyperparameters": {                          // Optional: Training hyperparameters
    "n_epochs": "auto",                         // int or "auto", default: "auto"
    "batch_size": "auto",                       // int or "auto", default: "auto"
    "learning_rate_multiplier": "auto"          // float or "auto", default: "auto"
  },
  "suffix": "my-custom-model",                  // Optional: Model name suffix (max 40 chars)
  "seed": 42,                                   // Optional: Random seed for reproducibility
  "method": {                                   // Optional: Fine-tuning method
    "type": "supervised"                        // "supervised", "dpo", or "reinforcement"
  },
  "integrations": [                             // Optional: Third-party integrations
    {
      "type": "wandb",
      "wandb": {
        "project": "my-fine-tuning-project",
        "entity": "my-org"
      }
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": "ftjob-abc123",
  "object": "fine_tuning.job",
  "model": "openai/gpt-oss-20b-2024-07-18",
  "created_at": 1704067200,
  "finished_at": null,
  "fine_tuned_model": null,
  "organization_id": "org-123",
  "result_files": [],
  "status": "validating_files",
  "validation_file": "file-xyz789",
  "training_file": "file-abc123",
  "hyperparameters": {
    "n_epochs": "auto",
    "batch_size": "auto",
    "learning_rate_multiplier": "auto"
  },
  "trained_tokens": null,
  "error": null,
  "user_provided_suffix": "my-custom-model",
  "seed": 42,
  "estimated_finish": 1704070800,
  "method": {
    "type": "supervised",
    "supervised": {
      "hyperparameters": {
        "n_epochs": "auto",
        "batch_size": "auto",
        "learning_rate_multiplier": "auto"
      }
    }
  },
  "integrations": []
}
```

#### 2.2.2 List Fine-Tuning Jobs

**Endpoint:** `GET /v1/fine_tuning/jobs`

**Query Parameters:**
- `after` (string): Identifier for pagination (returns jobs after this ID)
- `limit` (integer): Number of jobs to return (default: 20, max: 100)

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "ftjob-abc123",
      "object": "fine_tuning.job",
      "model": "openai/gpt-oss-20b-2024-07-18",
      "created_at": 1704067200,
      "finished_at": 1704070800,
      "fine_tuned_model": "ft:openai/gpt-oss-20b-2024-07-18:my-org:my-custom-model:abc123",
      "status": "succeeded",
      "hyperparameters": {
        "n_epochs": 3,
        "batch_size": 1,
        "learning_rate_multiplier": 1.8
      },
      "trained_tokens": 15000,
      "error": null
    }
  ],
  "has_more": false
}
```

#### 2.2.3 Retrieve Fine-Tuning Job

**Endpoint:** `GET /v1/fine_tuning/jobs/{job_id}`

**Response:** Same as individual job object shown above.

#### 2.2.4 Cancel Fine-Tuning Job

**Endpoint:** `POST /v1/fine_tuning/jobs/{job_id}/cancel`

**Response:**
```json
{
  "id": "ftjob-abc123",
  "object": "fine_tuning.job",
  "status": "cancelled",
  "model": "openai/gpt-oss-20b-2024-07-18",
  "created_at": 1704067200,
  "finished_at": 1704068000
}
```

#### 2.2.5 List Fine-Tuning Events

**Endpoint:** `GET /v1/fine_tuning/jobs/{job_id}/events`

**Query Parameters:**
- `after` (string): Identifier for pagination
- `limit` (integer): Number of events to return (default: 20)
- `stream` (boolean): Enable Server-Sent Events streaming (default: false)

**Response (Non-Streaming):**
```json
{
  "object": "list",
  "data": [
    {
      "id": "ft-event-abc123",
      "object": "fine_tuning.job.event",
      "created_at": 1704067200,
      "level": "info",
      "message": "Job enqueued. Waiting for jobs ahead to complete.",
      "type": "message"
    },
    {
      "id": "ft-event-def456",
      "object": "fine_tuning.job.event",
      "created_at": 1704067300,
      "level": "info",
      "message": "Job started.",
      "type": "message"
    },
    {
      "id": "ft-event-ghi789",
      "object": "fine_tuning.job.event",
      "created_at": 1704067350,
      "level": "info",
      "message": "Step 100/1500: training loss=2.43",
      "type": "metrics",
      "data": {
        "step": 100,
        "train_loss": 2.43,
        "train_mean_token_accuracy": 0.56
      }
    },
    {
      "id": "ft-event-jkl012",
      "object": "fine_tuning.job.event",
      "created_at": 1704068000,
      "level": "info",
      "message": "Checkpoint created at step 500.",
      "type": "checkpoint_created",
      "data": {
        "step": 500,
        "checkpoint_id": "ftckpt-abc123"
      }
    },
    {
      "id": "ft-event-mno345",
      "object": "fine_tuning.job.event",
      "created_at": 1704070800,
      "level": "info",
      "message": "Job completed successfully. Fine-tuned model ft:openai/gpt-oss-20b:org:suffix:abc123 created.",
      "type": "message"
    }
  ],
  "has_more": false
}
```

**Event Types:**
- `message` - General status messages
- `metrics` - Training metrics (loss, accuracy)
- `checkpoint_created` - Checkpoint creation notifications

**Event Levels:**
- `info` - Informational messages
- `warning` - Warning messages
- `error` - Error messages

**Streaming Format (SSE):**
When `stream=true`, events are sent as Server-Sent Events:
```
event: message
data: {"id": "ft-event-abc123", "object": "fine_tuning.job.event", ...}

event: message
data: {"id": "ft-event-def456", "object": "fine_tuning.job.event", ...}

event: done
data: [DONE]
```

#### 2.2.6 List Fine-Tuning Checkpoints

**Endpoint:** `GET /v1/fine_tuning/jobs/{job_id}/checkpoints`

**Query Parameters:**
- `after` (string): Identifier for pagination
- `limit` (integer): Number of checkpoints to return (default: 10)

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "ftckpt-abc123",
      "object": "fine_tuning.job.checkpoint",
      "created_at": 1704068000,
      "fine_tuning_job_id": "ftjob-abc123",
      "fine_tuned_model_checkpoint": "ft:openai/gpt-oss-20b:org:suffix:abc123:ckpt-500",
      "step_number": 500,
      "metrics": {
        "step": 500,
        "train_loss": 2.15,
        "train_mean_token_accuracy": 0.62,
        "valid_loss": 2.28,
        "valid_mean_token_accuracy": 0.59,
        "full_valid_loss": 2.31,
        "full_valid_mean_token_accuracy": 0.58
      }
    },
    {
      "id": "ftckpt-def456",
      "object": "fine_tuning.job.checkpoint",
      "created_at": 1704069000,
      "fine_tuning_job_id": "ftjob-abc123",
      "fine_tuned_model_checkpoint": "ft:openai/gpt-oss-20b:org:suffix:abc123:ckpt-1000",
      "step_number": 1000,
      "metrics": {
        "step": 1000,
        "train_loss": 1.87,
        "train_mean_token_accuracy": 0.71,
        "valid_loss": 2.12,
        "valid_mean_token_accuracy": 0.65,
        "full_valid_loss": 2.18,
        "full_valid_mean_token_accuracy": 0.63
      }
    },
    {
      "id": "ftckpt-ghi789",
      "object": "fine_tuning.job.checkpoint",
      "created_at": 1704070800,
      "fine_tuning_job_id": "ftjob-abc123",
      "fine_tuned_model_checkpoint": "ft:openai/gpt-oss-20b:org:suffix:abc123",
      "step_number": 1500,
      "metrics": {
        "step": 1500,
        "train_loss": 1.62,
        "train_mean_token_accuracy": 0.78,
        "valid_loss": 2.03,
        "valid_mean_token_accuracy": 0.69,
        "full_valid_loss": 2.09,
        "full_valid_mean_token_accuracy": 0.67
      }
    }
  ],
  "has_more": false
}
```

**Checkpoint Notes:**
- Checkpoints are created at the end of each training epoch
- The final checkpoint becomes the fine-tuned model
- Previous checkpoints are available for rollback
- Each checkpoint is a fully functional model that can be deployed
- Checkpoints can be used as base models for subsequent fine-tuning

### 2.3 Validation Metrics

#### 2.3.1 Metrics Definitions

| Metric | Description | Range |
|--------|-------------|-------|
| `step` | Current training step | Integer |
| `train_loss` | Cross-entropy loss on training batch | Float (lower is better) |
| `train_mean_token_accuracy` | Average token-level accuracy on training batch | 0.0 - 1.0 |
| `valid_loss` | Cross-entropy loss on validation batch | Float (lower is better) |
| `valid_mean_token_accuracy` | Average token-level accuracy on validation batch | 0.0 - 1.0 |
| `full_valid_loss` | Loss computed on entire validation set | Float (lower is better) |
| `full_valid_mean_token_accuracy` | Accuracy computed on entire validation set | 0.0 - 1.0 |

#### 2.3.2 Metric Interpretation

**Training vs Validation Loss:**
- If `train_loss` decreases but `valid_loss` increases → **Overfitting**
- If both decrease together → **Good training progress**
- If both plateau → **Convergence** (training complete)

**Full Validation vs Batch Validation:**
- `valid_loss` - Computed on random validation batches during training (fast)
- `full_valid_loss` - Computed on entire validation set (more accurate, slower)
- Full validation metrics are more reliable for model selection

**Token Accuracy:**
- Percentage of tokens predicted correctly
- Complementary to loss metrics
- Higher is better (close to 1.0)

#### 2.3.3 Checkpoint Selection Strategy

**Best Practices:**
1. Monitor `full_valid_loss` - primary indicator of model quality
2. Watch for overfitting (train_loss drops, valid_loss rises)
3. Select checkpoint with lowest `full_valid_loss`
4. Use final checkpoint if validation loss keeps decreasing

---

## 3. Azure OpenAI Fine-Tuning

### 3.1 Key Differences from OpenAI

#### 3.1.1 API Versioning

Azure uses explicit API versions in the URL:
```
POST https://{endpoint}/openai/fine_tuning/jobs?api-version=2024-10-21
```

**Available API Versions:**
- `2024-10-21` - Latest stable version
- `2024-08-01-preview` - v1 API preview
- `2023-12-01-preview` - Legacy version

#### 3.1.2 Authentication

Azure uses key-based or token-based authentication:
```
Authorization: Bearer {azure_token}
api-key: {your-api-key}
```

#### 3.1.3 Additional Features

**1. Token-Based Billing:**
- Starting 2024, Azure uses token-based billing for fine-tuning
- More granular cost control
- Pay only for tokens processed

**2. LoRA (Low-Rank Adaptation):**
- Efficient fine-tuning method
- Reduces computational requirements
- Faster training times
- Lower memory usage

**3. Serverless Fine-Tuning:**
- Consumption-based pricing ($1.70 per million tokens)
- No infrastructure management
- Auto-scaling resources

**4. Global Training:**
- GPT-4o, 4o-mini available in all regions
- Reduced latency
- Better availability

**5. Cost Management:**
- Inactive deployment doesn't affect model retention
- Hourly hosting cost for deployed models
- Can redeploy at any time

### 3.2 Model Availability

**Generally Available (GA):**
- GPT-4o (openai/gpt-oss-120b-2024-08-06)
- GPT-4o-mini (openai/gpt-oss-20b-2024-07-18)
- GPT-3.5-turbo (gpt-35-turbo-0125)

**In Development:**
- GPT-4.1, 4.1-mini, 4.1-nano
- Reinforcement fine-tuning for o4-mini (preview)

### 3.3 Azure-Specific Request Fields

```json
{
  "model": "openai/gpt-oss-120b-2024-08-06",
  "training_file": "file-abc123",
  "validation_file": "file-xyz789",
  "hyperparameters": {
    "n_epochs": 3,
    "batch_size": 1,
    "learning_rate_multiplier": 1.8
  },
  "suffix": "custom-model",
  "seed": 42,
  "use_lora": true                  // Azure-specific: Enable LoRA
}
```

---

## 4. Anthropic Claude Fine-Tuning

### 4.1 Availability and Limitations

**Key Points:**
- Fine-tuning available **ONLY** through **Amazon Bedrock**
- Not available via Anthropic's native API
- Limited to Claude 3 Haiku model
- No direct API from Anthropic for fine-tuning

### 4.2 Amazon Bedrock Integration

**Supported Model:**
- Claude 3 Haiku (generally available)

**Access Requirements:**
- AWS account
- Amazon Bedrock access
- Claude 3 Haiku preview access (contact AWS team)

### 4.3 Fine-Tuning Process

**1. Data Preparation:**
- JSONL format required
- System prompt + message pairs
- Max training data size: 10GB
- Max validation data size: 1GB

**2. Training:**
- Uses Amazon's infrastructure
- Data remains in your AWS environment
- Proprietary training data stays private

**3. Benefits:**
- Faster inference at lower cost
- Consistent, brand-aligned formatting
- Domain-specific optimization

### 4.4 Why Not Included in FakeAI

**Rationale:**
- Not a standard API pattern
- Requires AWS Bedrock (external dependency)
- Limited model support
- Not widely used compared to OpenAI fine-tuning
- FakeAI focuses on simulating standard APIs

**Recommendation:** Focus on OpenAI and Azure OpenAI fine-tuning APIs for FakeAI implementation.

---

## 5. Training Data Format (JSONL)

### 5.1 JSONL Structure

**Format:** JSON Lines - one valid JSON object per line

**Basic Structure:**
```jsonl
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

**Each line is a complete training example** - do NOT split across lines.

### 5.2 Message Roles

| Role | Required | Purpose | Example |
|------|----------|---------|---------|
| `system` | Optional | Define assistant behavior | "You are a helpful customer support agent." |
| `user` | Required | User input/query | "What is your return policy?" |
| `assistant` | Required | Expected model output | "Our return policy allows returns within 30 days..." |

### 5.3 Example Training Data

#### 5.3.1 Simple Single-Turn Conversations

```jsonl
{"messages": [{"role": "system", "content": "You are a happy assistant that puts a positive spin on everything."}, {"role": "user", "content": "I fell off my bike today."}, {"role": "assistant", "content": "It's great that you're getting exercise outdoors!"}]}
{"messages": [{"role": "system", "content": "You are a happy assistant that puts a positive spin on everything."}, {"role": "user", "content": "I lost my wallet."}, {"role": "assistant", "content": "Now you have a great reason to get a new stylish wallet!"}]}
{"messages": [{"role": "system", "content": "You are a happy assistant that puts a positive spin on everything."}, {"role": "user", "content": "It's raining today."}, {"role": "assistant", "content": "Perfect weather for cozy indoor activities!"}]}
```

#### 5.3.2 Multi-Turn Conversations

```jsonl
{"messages": [{"role": "system", "content": "You are a helpful math tutor."}, {"role": "user", "content": "How do I solve 2x + 5 = 15?"}, {"role": "assistant", "content": "Let's solve this step by step. First, subtract 5 from both sides."}, {"role": "user", "content": "OK, so 2x = 10?"}, {"role": "assistant", "content": "Exactly! Now divide both sides by 2 to get x = 5."}]}
{"messages": [{"role": "system", "content": "You are a helpful coding assistant."}, {"role": "user", "content": "How do I read a file in Python?"}, {"role": "assistant", "content": "You can use the open() function with a with statement: with open('file.txt', 'r') as f: content = f.read()"}, {"role": "user", "content": "What if the file doesn't exist?"}, {"role": "assistant", "content": "You should use try/except to catch FileNotFoundError: try: with open('file.txt', 'r') as f: content = f.read() except FileNotFoundError: print('File not found')"}]}
```

#### 5.3.3 Function Calling Format

```jsonl
{"messages": [{"role": "system", "content": "You are a helpful assistant with access to weather data."}, {"role": "user", "content": "What's the weather in San Francisco?"}, {"role": "assistant", "content": null, "tool_calls": [{"id": "call_abc123", "type": "function", "function": {"name": "get_weather", "arguments": "{\"location\": \"San Francisco, CA\"}"}}]}, {"role": "tool", "tool_call_id": "call_abc123", "content": "{\"temperature\": 65, \"conditions\": \"sunny\"}"}, {"role": "assistant", "content": "The weather in San Francisco is currently 65°F and sunny!"}]}
```

### 5.4 Data Quality Requirements

#### 5.4.1 File Format Requirements

- **Encoding:** UTF-8 with BOM (Byte Order Mark)
- **File Extension:** `.jsonl`
- **Max File Size:**
  - Training: 512 MB (OpenAI), 10 GB (Azure)
  - Validation: 512 MB (OpenAI), 1 GB (Azure)
- **Min Examples:** 10 (recommended: 50-100)
- **Max Examples:** No hard limit (practical: 10,000-100,000)

#### 5.4.2 Content Requirements

**Do:**
-  Use consistent formatting
-  Include diverse examples
-  Provide high-quality expected outputs
-  Balance example types
-  Include edge cases
-  Use double quotes for strings

**Don't:**
-  Include personally identifiable information (PII)
-  Use single quotes (invalid JSON)
-  Split JSON objects across lines
-  Include comments (not valid JSON)
-  Have duplicate examples
-  Use inconsistent formatting

#### 5.4.3 Validation Data

**Purpose:**
- Measure model performance during training
- Detect overfitting
- Select best checkpoint

**Format:** Same as training data (JSONL)

**Size:** Typically 10-20% of training data size

**Example:**
- Training: 500 examples
- Validation: 50-100 examples

---

## 6. Fine-Tuning Methods

OpenAI supports three fine-tuning methods: Supervised Fine-Tuning (SFT), Direct Preference Optimization (DPO), and Reinforcement Fine-Tuning (RFT).

### 6.1 Supervised Fine-Tuning (SFT)

#### 6.1.1 Overview

**What It Is:**
- Traditional supervised learning approach
- Learn from input-output pairs
- Train model to predict correct answers
- Most common and straightforward method

**When to Use:**
- You have clear correct answers
- Task has deterministic outputs
- Examples: classification, extraction, formatting
- Simple use cases

#### 6.1.2 Training Process

1. Model receives input (user message)
2. Model generates output (assistant message)
3. Compare output to expected answer (training data)
4. Adjust model weights to minimize difference
5. Repeat for all examples

#### 6.1.3 Request Format

```json
{
  "model": "openai/gpt-oss-20b-2024-07-18",
  "training_file": "file-abc123",
  "validation_file": "file-xyz789",
  "method": {
    "type": "supervised",
    "supervised": {
      "hyperparameters": {
        "n_epochs": 3,
        "batch_size": 1,
        "learning_rate_multiplier": 1.8
      }
    }
  }
}
```

#### 6.1.4 Hyperparameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `n_epochs` | Number of training passes | "auto" | 1-50 |
| `batch_size` | Examples per batch | "auto" | 1-256 |
| `learning_rate_multiplier` | Learning rate scale factor | "auto" | 0.01-10.0 |

**Auto Mode:**
- OpenAI automatically selects optimal values
- Based on dataset size and characteristics
- Recommended for most users

### 6.2 Direct Preference Optimization (DPO)

#### 6.2.1 Overview

**What It Is:**
- Alignment technique using preference pairs
- Train model to prefer better outputs over worse ones
- Simpler than RLHF (Reinforcement Learning from Human Feedback)
- More stable training

**When to Use:**
- You have ranked output pairs (better vs worse)
- Subjective quality matters (tone, style, helpfulness)
- After SFT for further alignment
- Examples: customer service tone, creative writing style

#### 6.2.2 Training Process

1. Model generates two outputs for same input
2. Human ranks outputs (which is better?)
3. Model learns to increase probability of better output
4. Model learns to decrease probability of worse output
5. Repeat with many preference pairs

**Key Difference from SFT:**
- SFT: "This is the correct answer"
- DPO: "This answer is better than that answer"

#### 6.2.3 Data Format (DPO-Specific)

```jsonl
{"messages": [{"role": "user", "content": "Write a poem about coding."}], "chosen": {"role": "assistant", "content": "Code flows like poetry, elegant and bright..."}, "rejected": {"role": "assistant", "content": "Writing code is boring..."}}
{"messages": [{"role": "user", "content": "Explain recursion simply."}], "chosen": {"role": "assistant", "content": "Imagine a function that calls itself to solve smaller versions of the same problem..."}, "rejected": {"role": "assistant", "content": "Recursion is when code recurses recursively in a recursive manner."}}
```

**Fields:**
- `messages` - Input context
- `chosen` - Preferred output (higher quality)
- `rejected` - Dispreferred output (lower quality)

#### 6.2.4 Request Format

```json
{
  "model": "openai/gpt-oss-20b-2024-07-18",
  "training_file": "file-abc123",
  "validation_file": "file-xyz789",
  "method": {
    "type": "dpo",
    "dpo": {
      "hyperparameters": {
        "n_epochs": 1,
        "batch_size": 8,
        "learning_rate_multiplier": 1.0,
        "beta": 0.1
      }
    }
  }
}
```

#### 6.2.5 DPO-Specific Hyperparameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `beta` | Preference strength coefficient | 0.1 | 0.01-1.0 |
| `n_epochs` | Training epochs | 1-3 | 1-10 |

**Beta Parameter:**
- Controls how strongly model prefers chosen over rejected
- Higher beta → stronger preference enforcement
- Lower beta → softer preference learning
- Typical: 0.1-0.3

#### 6.2.6 Benefits Over RLHF

1. **Simpler:** No separate reward model needed
2. **Faster:** Direct optimization, no policy updates
3. **Stable:** Less prone to training instabilities
4. **Efficient:** Requires less compute
5. **Effective:** Comparable alignment quality

### 6.3 Reinforcement Fine-Tuning (RFT)

#### 6.3.1 Overview

**What It Is:**
- Uses reinforcement learning with reward signals
- Model learns from feedback scores (graders)
- Optimizes for complex, multi-faceted objectives
- Most flexible but most complex

**When to Use:**
- Complex evaluation criteria
- Multiple objectives to balance
- Programmatic grading available
- Need reasoning model adaptation
- Examples: code generation, complex reasoning, game playing

#### 6.3.2 Training Process

1. Model generates output for input
2. Grader evaluates output (reward signal)
3. High-scoring outputs → increased probability
4. Low-scoring outputs → decreased probability
5. Model learns to maximize reward
6. Repeat across many examples

**Key Difference:**
- SFT: Learn from fixed answers
- DPO: Learn from preferences
- RFT: Learn from reward signals

#### 6.3.3 Grader Configuration

**Grader Types:**
1. **Rule-Based:** Programmatic checks (e.g., code syntax, format validation)
2. **Model-Based:** Use another LLM to score (e.g., GPT-4o judges GPT-4o-mini output)
3. **Hybrid:** Combination of rules and model judgments

**Example Grader Config:**
```json
{
  "grader": {
    "type": "model",
    "model": "openai/gpt-oss-120b",
    "prompt": "Rate this response on accuracy (0-10) and helpfulness (0-10). Return JSON: {\"accuracy\": X, \"helpfulness\": Y}"
  }
}
```

#### 6.3.4 Request Format

```json
{
  "model": "o4-mini-2025-04-16",
  "training_file": "file-abc123",
  "validation_file": "file-xyz789",
  "method": {
    "type": "reinforcement",
    "reinforcement": {
      "hyperparameters": {
        "n_epochs": 1,
        "learning_rate_multiplier": 1.0
      },
      "grader": {
        "type": "model",
        "model": "openai/gpt-oss-120b-2024-08-06",
        "prompt": "Evaluate the response quality..."
      }
    }
  }
}
```

#### 6.3.5 RFT-Specific Features

**Metrics Published:**
- Per-step training metrics available as events
- Real-time monitoring of reward signals
- Detailed convergence tracking

**Cost Model:**
- Billed by wall-clock time ($100/hour for o4-mini)
- Not billed by tokens (unlike SFT/DPO)
- Grader model usage billed separately at inference rates

**Training Time:**
- Typically longer than SFT/DPO
- More computationally intensive
- Can take hours to days depending on data size

### 6.4 Method Comparison

| Aspect | SFT | DPO | RFT |
|--------|-----|-----|-----|
| **Complexity** | Low | Medium | High |
| **Data Format** | Input-output pairs | Preference pairs | Input + grader |
| **Training Speed** | Fast | Medium | Slow |
| **Cost** | Token-based | Token-based | Time-based |
| **Use Case** | Clear answers | Preference learning | Complex objectives |
| **Stability** | High | High | Medium |
| **Flexibility** | Low | Medium | High |

### 6.5 Best Practices

#### 6.5.1 Method Selection

**Start with SFT:**
- Begin with supervised fine-tuning
- Establish baseline performance
- Most use cases work well with SFT alone

**Add DPO for Alignment:**
- After SFT, use DPO for refinement
- Industry standard: SFT → DPO pipeline
- Improves subjective quality

**Use RFT for Complex Tasks:**
- Only when SFT/DPO insufficient
- Complex reasoning tasks
- Multi-objective optimization
- Code generation, mathematical reasoning

#### 6.5.2 Combined Approach

**Recommended Workflow:**
```
1. SFT (base fine-tuning)
   ↓
2. DPO (alignment)
   ↓
3. RFT (optional, for complex tasks)
```

**Example:**
- **Stage 1 (SFT):** Train on 1000 customer support conversations
- **Stage 2 (DPO):** Refine with 200 preference pairs (polite vs rude responses)
- **Stage 3 (RFT):** Optimize for customer satisfaction score (optional)

---

## 7. Implementation Strategy for FakeAI

### 7.1 Core Requirements

To simulate OpenAI's fine-tuning API in FakeAI, we need:

1. **File Storage:** Leverage existing `/v1/files` endpoints
2. **Job Management:** Track fine-tuning jobs with state transitions
3. **Event Streaming:** Simulate training progress with SSE
4. **Checkpoint Generation:** Create epoch-based checkpoints
5. **Metrics Simulation:** Generate realistic training/validation metrics
6. **Model Registration:** Auto-create fine-tuned models

### 7.2 Architecture Design

#### 7.2.1 Data Structures

**FineTuningJob:**
```python
class FineTuningJob:
    id: str                          # ftjob-{uuid}
    model: str                       # Base model
    status: JobStatus                # Enum: validating_files, queued, running, succeeded, failed, cancelled
    training_file: str               # File ID
    validation_file: str | None      # File ID
    hyperparameters: Hyperparameters
    method: Method                   # Supervised, DPO, or RFT
    created_at: int                  # Unix timestamp
    started_at: int | None           # When training started
    finished_at: int | None          # When training finished
    fine_tuned_model: str | None     # ft:{model}:{org}:{suffix}:{id}
    trained_tokens: int | None       # Total tokens processed
    error: Error | None              # Error details if failed
    result_files: list[str]          # Result file IDs
    seed: int | None                 # Random seed
    estimated_finish: int | None     # Estimated completion time
    integrations: list[Integration]  # W&B, etc.
```

**JobStatus Enum:**
```python
class JobStatus(str, Enum):
    VALIDATING_FILES = "validating_files"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

**FineTuningEvent:**
```python
class FineTuningEvent:
    id: str                    # ft-event-{uuid}
    created_at: int            # Unix timestamp
    level: EventLevel          # info, warning, error
    message: str               # Human-readable message
    type: EventType            # message, metrics, checkpoint_created
    data: dict | None          # Additional structured data
```

**FineTuningCheckpoint:**
```python
class FineTuningCheckpoint:
    id: str                                    # ftckpt-{uuid}
    fine_tuning_job_id: str                    # Parent job ID
    created_at: int                            # Unix timestamp
    fine_tuned_model_checkpoint: str           # Model name
    step_number: int                           # Training step
    metrics: CheckpointMetrics                 # Training metrics
```

**CheckpointMetrics:**
```python
class CheckpointMetrics:
    step: int
    train_loss: float
    train_mean_token_accuracy: float
    valid_loss: float | None
    valid_mean_token_accuracy: float | None
    full_valid_loss: float | None
    full_valid_mean_token_accuracy: float | None
```

#### 7.2.2 Service Methods

**Core Methods:**
```python
class FakeAIService:
    # Job Management
    async def create_fine_tuning_job(self, request: FineTuningJobRequest) -> FineTuningJob
    async def list_fine_tuning_jobs(self, after: str | None, limit: int) -> FineTuningJobListResponse
    async def get_fine_tuning_job(self, job_id: str) -> FineTuningJob
    async def cancel_fine_tuning_job(self, job_id: str) -> FineTuningJob

    # Events
    async def list_fine_tuning_events(self, job_id: str, after: str | None, limit: int) -> FineTuningEventListResponse
    async def stream_fine_tuning_events(self, job_id: str) -> AsyncGenerator[FineTuningEvent]

    # Checkpoints
    async def list_fine_tuning_checkpoints(self, job_id: str, after: str | None, limit: int) -> CheckpointListResponse

    # Background Processing
    async def _simulate_fine_tuning_job(self, job_id: str) -> None
    async def _generate_training_events(self, job_id: str) -> None
    async def _create_checkpoints(self, job_id: str, epoch: int) -> None
    async def _finalize_fine_tuned_model(self, job_id: str) -> None
```

### 7.3 Simulation Logic

#### 7.3.1 Job Creation Flow

**Step 1: Validation**
```python
async def create_fine_tuning_job(self, request):
    # 1. Create job in validating_files state
    job = FineTuningJob(
        id=f"ftjob-{uuid.uuid4().hex}",
        status=JobStatus.VALIDATING_FILES,
        created_at=int(time.time()),
        ...
    )

    # 2. Start background simulation
    asyncio.create_task(self._simulate_fine_tuning_job(job.id))

    return job
```

**Step 2: Background Simulation**
```python
async def _simulate_fine_tuning_job(self, job_id):
    job = self.fine_tuning_jobs[job_id]

    # Phase 1: File validation (2-5 seconds)
    await asyncio.sleep(random.uniform(2, 5))
    await self._emit_event(job_id, "Files validated successfully")

    # Phase 2: Queue (5-30 seconds)
    job.status = JobStatus.QUEUED
    await asyncio.sleep(random.uniform(5, 30))
    await self._emit_event(job_id, "Job started")

    # Phase 3: Training (simulate 3 epochs)
    job.status = JobStatus.RUNNING
    job.started_at = int(time.time())

    n_epochs = job.hyperparameters.n_epochs or 3
    total_steps = 1000 * n_epochs  # Simulate 1000 steps per epoch

    for step in range(1, total_steps + 1):
        # Generate realistic metrics
        metrics = self._generate_training_metrics(step, total_steps)

        # Emit metrics event every 100 steps
        if step % 100 == 0:
            await self._emit_metrics_event(job_id, step, metrics)

        # Create checkpoint at end of each epoch
        if step % 1000 == 0:
            epoch = step // 1000
            await self._create_checkpoint(job_id, step, metrics, epoch)

        # Small delay to simulate training
        await asyncio.sleep(0.01)

    # Phase 4: Finalization
    job.status = JobStatus.SUCCEEDED
    job.finished_at = int(time.time())
    job.fine_tuned_model = self._generate_model_name(job)
    job.trained_tokens = self._calculate_trained_tokens(job)

    await self._emit_event(job_id, f"Job completed. Model {job.fine_tuned_model} created.")

    # Register fine-tuned model
    self._register_fine_tuned_model(job)
```

#### 7.3.2 Metrics Generation

**Realistic Loss Curves:**
```python
def _generate_training_metrics(self, step: int, total_steps: int) -> dict:
    """Generate realistic training metrics with decreasing loss."""
    progress = step / total_steps

    # Initial loss starts high (2.5-3.0), decreases to 1.5-2.0
    base_train_loss = 2.8 - (progress * 1.0)
    base_valid_loss = 2.9 - (progress * 0.8)  # Valid loss higher (gap = overfitting signal)

    # Add realistic noise
    train_loss = base_train_loss + random.gauss(0, 0.1)
    valid_loss = base_valid_loss + random.gauss(0, 0.15)

    # Accuracy increases (0.5 → 0.75)
    train_accuracy = 0.5 + (progress * 0.25) + random.gauss(0, 0.02)
    valid_accuracy = 0.48 + (progress * 0.22) + random.gauss(0, 0.03)

    return {
        "step": step,
        "train_loss": round(train_loss, 4),
        "train_mean_token_accuracy": round(train_accuracy, 4),
        "valid_loss": round(valid_loss, 4),
        "valid_mean_token_accuracy": round(valid_accuracy, 4),
    }
```

**Full Validation Metrics:**
```python
def _generate_full_validation_metrics(self, step: int, total_steps: int) -> dict:
    """Generate full validation metrics (more accurate, slightly worse than batch)."""
    batch_metrics = self._generate_training_metrics(step, total_steps)

    # Full validation is ~5% worse than batch validation
    return {
        "full_valid_loss": round(batch_metrics["valid_loss"] * 1.05, 4),
        "full_valid_mean_token_accuracy": round(batch_metrics["valid_mean_token_accuracy"] * 0.95, 4),
    }
```

#### 7.3.3 Checkpoint Creation

```python
async def _create_checkpoint(self, job_id: str, step: int, metrics: dict, epoch: int):
    """Create checkpoint at end of epoch."""
    job = self.fine_tuning_jobs[job_id]

    # Generate checkpoint ID and model name
    checkpoint_id = f"ftckpt-{uuid.uuid4().hex}"

    # Final checkpoint gets the main model name, others get :ckpt-{step}
    if step == job.total_steps:
        checkpoint_model = self._generate_model_name(job)
    else:
        base_name = self._generate_model_name(job)
        checkpoint_model = f"{base_name}:ckpt-{step}"

    # Add full validation metrics
    full_metrics = self._generate_full_validation_metrics(step, job.total_steps)
    checkpoint_metrics = {**metrics, **full_metrics}

    # Create checkpoint
    checkpoint = FineTuningCheckpoint(
        id=checkpoint_id,
        fine_tuning_job_id=job_id,
        created_at=int(time.time()),
        fine_tuned_model_checkpoint=checkpoint_model,
        step_number=step,
        metrics=CheckpointMetrics(**checkpoint_metrics),
    )

    # Store checkpoint
    self.fine_tuning_checkpoints[checkpoint_id] = checkpoint

    # Emit event
    await self._emit_event(
        job_id,
        f"Checkpoint created at step {step} (epoch {epoch})",
        event_type="checkpoint_created",
        data={"step": step, "checkpoint_id": checkpoint_id}
    )

    # Register checkpoint as usable model
    self._register_fine_tuned_model_checkpoint(checkpoint)
```

#### 7.3.4 Model Registration

```python
def _generate_model_name(self, job: FineTuningJob) -> str:
    """Generate fine-tuned model name."""
    # Format: ft:{base_model}:{org}:{suffix}:{short_id}
    # Example: ft:openai/gpt-oss-20b-2024-07-18:my-org:custom-model:abc123

    base_model = job.model
    org = "fakeai"  # Simulated organization
    suffix = job.user_provided_suffix or "model"
    short_id = job.id[-6:]  # Last 6 chars of job ID

    return f"ft:{base_model}:{org}:{suffix}:{short_id}"

def _register_fine_tuned_model(self, job: FineTuningJob):
    """Register fine-tuned model so it can be used in completions."""
    model_id = job.fine_tuned_model

    # Use existing _ensure_model_exists pattern
    self._ensure_model_exists(model_id)

    # Update model metadata
    model = self.models[model_id]
    model.owned_by = "fakeai"
    model.root = job.model  # Base model
    model.parent = job.model
```

### 7.4 Event Streaming Implementation

#### 7.4.1 Event Storage

```python
class FakeAIService:
    def __init__(self):
        self.fine_tuning_jobs: dict[str, FineTuningJob] = {}
        self.fine_tuning_events: dict[str, list[FineTuningEvent]] = {}  # job_id → events
        self.fine_tuning_checkpoints: dict[str, FineTuningCheckpoint] = {}
        self.event_subscribers: dict[str, list[asyncio.Queue]] = {}  # job_id → queues
```

#### 7.4.2 Event Emission

```python
async def _emit_event(
    self,
    job_id: str,
    message: str,
    level: str = "info",
    event_type: str = "message",
    data: dict | None = None
):
    """Emit event and notify subscribers."""
    event = FineTuningEvent(
        id=f"ft-event-{uuid.uuid4().hex}",
        created_at=int(time.time()),
        level=level,
        message=message,
        type=event_type,
        data=data,
    )

    # Store event
    if job_id not in self.fine_tuning_events:
        self.fine_tuning_events[job_id] = []
    self.fine_tuning_events[job_id].append(event)

    # Notify subscribers (for streaming)
    if job_id in self.event_subscribers:
        for queue in self.event_subscribers[job_id]:
            await queue.put(event)
```

#### 7.4.3 SSE Streaming

```python
async def stream_fine_tuning_events(self, job_id: str):
    """Stream events using Server-Sent Events."""
    # Create subscriber queue
    queue = asyncio.Queue()

    if job_id not in self.event_subscribers:
        self.event_subscribers[job_id] = []
    self.event_subscribers[job_id].append(queue)

    try:
        # Send existing events
        if job_id in self.fine_tuning_events:
            for event in self.fine_tuning_events[job_id]:
                yield f"event: message\ndata: {event.model_dump_json()}\n\n"

        # Stream new events
        job = self.fine_tuning_jobs[job_id]
        while job.status in [JobStatus.VALIDATING_FILES, JobStatus.QUEUED, JobStatus.RUNNING]:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"event: message\ndata: {event.model_dump_json()}\n\n"
            except asyncio.TimeoutError:
                # Send keepalive
                yield ": keepalive\n\n"

        # Send done signal
        yield "event: done\ndata: [DONE]\n\n"

    finally:
        # Cleanup
        self.event_subscribers[job_id].remove(queue)
```

### 7.5 API Endpoint Implementation

#### 7.5.1 FastAPI Routes

```python
# In app.py

@app.post("/v1/fine_tuning/jobs", dependencies=[Depends(verify_api_key)])
async def create_fine_tuning_job(
    request: FineTuningJobRequest
) -> FineTuningJob:
    """Create a fine-tuning job."""
    return await fakeai_service.create_fine_tuning_job(request)

@app.get("/v1/fine_tuning/jobs", dependencies=[Depends(verify_api_key)])
async def list_fine_tuning_jobs(
    after: str | None = None,
    limit: int = 20
) -> FineTuningJobListResponse:
    """List fine-tuning jobs with pagination."""
    return await fakeai_service.list_fine_tuning_jobs(after, limit)

@app.get("/v1/fine_tuning/jobs/{job_id}", dependencies=[Depends(verify_api_key)])
async def get_fine_tuning_job(job_id: str) -> FineTuningJob:
    """Get fine-tuning job details."""
    return await fakeai_service.get_fine_tuning_job(job_id)

@app.post("/v1/fine_tuning/jobs/{job_id}/cancel", dependencies=[Depends(verify_api_key)])
async def cancel_fine_tuning_job(job_id: str) -> FineTuningJob:
    """Cancel a fine-tuning job."""
    return await fakeai_service.cancel_fine_tuning_job(job_id)

@app.get("/v1/fine_tuning/jobs/{job_id}/events", dependencies=[Depends(verify_api_key)])
async def list_fine_tuning_events(
    job_id: str,
    after: str | None = None,
    limit: int = 20,
    stream: bool = False
) -> StreamingResponse | FineTuningEventListResponse:
    """List or stream fine-tuning job events."""
    if stream:
        return StreamingResponse(
            fakeai_service.stream_fine_tuning_events(job_id),
            media_type="text/event-stream"
        )
    else:
        return await fakeai_service.list_fine_tuning_events(job_id, after, limit)

@app.get("/v1/fine_tuning/jobs/{job_id}/checkpoints", dependencies=[Depends(verify_api_key)])
async def list_fine_tuning_checkpoints(
    job_id: str,
    after: str | None = None,
    limit: int = 10
) -> CheckpointListResponse:
    """List fine-tuning job checkpoints."""
    return await fakeai_service.list_fine_tuning_checkpoints(job_id, after, limit)
```

### 7.6 Configuration

**Add to AppConfig:**
```python
class AppConfig(BaseSettings):
    # ... existing fields

    # Fine-tuning simulation settings
    fine_tuning_validation_delay: float = 3.0     # File validation time
    fine_tuning_queue_delay: float = 15.0         # Queue wait time
    fine_tuning_step_delay: float = 0.01          # Per-step delay
    fine_tuning_steps_per_epoch: int = 1000       # Steps per epoch
    fine_tuning_default_epochs: int = 3           # Default epochs
```

### 7.7 Testing Strategy

#### 7.7.1 Unit Tests

```python
@pytest.mark.asyncio
async def test_create_fine_tuning_job():
    service = FakeAIService(config)

    request = FineTuningJobRequest(
        model="openai/gpt-oss-20b-2024-07-18",
        training_file="file-abc123"
    )

    job = await service.create_fine_tuning_job(request)

    assert job.id.startswith("ftjob-")
    assert job.status == JobStatus.VALIDATING_FILES
    assert job.model == "openai/gpt-oss-20b-2024-07-18"

@pytest.mark.asyncio
async def test_job_lifecycle():
    service = FakeAIService(config)
    job = await service.create_fine_tuning_job(request)

    # Wait for completion
    await asyncio.sleep(5)

    # Check status progression
    updated_job = await service.get_fine_tuning_job(job.id)
    assert updated_job.status in [JobStatus.RUNNING, JobStatus.SUCCEEDED]

@pytest.mark.asyncio
async def test_event_streaming():
    service = FakeAIService(config)
    job = await service.create_fine_tuning_job(request)

    events = []
    async for event in service.stream_fine_tuning_events(job.id):
        events.append(event)
        if len(events) >= 5:
            break

    assert len(events) >= 5
    assert events[0].message == "Job enqueued"
```

#### 7.7.2 Integration Tests

```python
def test_openai_client_fine_tuning():
    """Test with official OpenAI Python client."""
    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000"
    )

    # Create job
    job = client.fine_tuning.jobs.create(
        training_file="file-abc123",
        model="openai/gpt-oss-20b-2024-07-18"
    )

    assert job.id.startswith("ftjob-")

    # List jobs
    jobs = client.fine_tuning.jobs.list()
    assert len(jobs.data) > 0

    # Stream events
    for event in client.fine_tuning.jobs.events(job.id, stream=True):
        print(event.message)
```

### 7.8 Phased Implementation Plan

#### Phase 1: Core Infrastructure (Week 1)
- [ ] Define Pydantic models for all schemas
- [ ] Implement job storage and state management
- [ ] Create basic service methods (create, list, get)
- [ ] Add FastAPI routes

#### Phase 2: Job Simulation (Week 2)
- [ ] Implement background job simulation
- [ ] Generate realistic training metrics
- [ ] Handle job cancellation
- [ ] Error handling and validation

#### Phase 3: Events and Streaming (Week 3)
- [ ] Event storage and emission
- [ ] SSE streaming implementation
- [ ] Event pagination
- [ ] Keepalive and connection handling

#### Phase 4: Checkpoints (Week 4)
- [ ] Checkpoint generation at epoch boundaries
- [ ] Checkpoint metrics calculation
- [ ] Checkpoint model registration
- [ ] Checkpoint API endpoints

#### Phase 5: Polish and Testing (Week 5)
- [ ] Comprehensive unit tests
- [ ] Integration tests with OpenAI client
- [ ] Documentation updates
- [ ] Performance optimization

---

## 8. Complete API Schemas

### 8.1 Request Schemas

#### 8.1.1 FineTuningJobRequest

```python
class Method(BaseModel):
    """Fine-tuning method configuration."""
    type: Literal["supervised", "dpo", "reinforcement"] = Field(
        description="Fine-tuning method type"
    )
    supervised: SupervisedMethod | None = Field(
        default=None,
        description="Supervised fine-tuning configuration"
    )
    dpo: DpoMethod | None = Field(
        default=None,
        description="DPO configuration"
    )
    reinforcement: ReinforcementMethod | None = Field(
        default=None,
        description="Reinforcement fine-tuning configuration"
    )

class SupervisedMethod(BaseModel):
    """Supervised fine-tuning method configuration."""
    hyperparameters: Hyperparameters | None = Field(
        default=None,
        description="Training hyperparameters"
    )

class DpoMethod(BaseModel):
    """DPO method configuration."""
    hyperparameters: DpoHyperparameters | None = Field(
        default=None,
        description="DPO hyperparameters"
    )

class ReinforcementMethod(BaseModel):
    """Reinforcement fine-tuning method configuration."""
    hyperparameters: Hyperparameters | None = Field(
        default=None,
        description="Training hyperparameters"
    )
    grader: Grader | None = Field(
        default=None,
        description="Grader configuration"
    )

class Hyperparameters(BaseModel):
    """Training hyperparameters."""
    n_epochs: int | Literal["auto"] = Field(
        default="auto",
        description="Number of training epochs"
    )
    batch_size: int | Literal["auto"] = Field(
        default="auto",
        description="Training batch size"
    )
    learning_rate_multiplier: float | Literal["auto"] = Field(
        default="auto",
        description="Learning rate multiplier"
    )

class DpoHyperparameters(Hyperparameters):
    """DPO-specific hyperparameters."""
    beta: float = Field(
        default=0.1,
        description="Preference strength coefficient"
    )

class Grader(BaseModel):
    """Grader configuration for RFT."""
    type: Literal["model", "rule", "hybrid"] = Field(
        description="Grader type"
    )
    model: str | None = Field(
        default=None,
        description="Model to use for grading"
    )
    prompt: str | None = Field(
        default=None,
        description="Grading prompt"
    )

class Integration(BaseModel):
    """Third-party integration configuration."""
    type: Literal["wandb"] = Field(description="Integration type")
    wandb: WandbIntegration | None = Field(
        default=None,
        description="Weights & Biases configuration"
    )

class WandbIntegration(BaseModel):
    """Weights & Biases integration."""
    project: str = Field(description="W&B project name")
    entity: str | None = Field(
        default=None,
        description="W&B entity (organization)"
    )
    tags: list[str] | None = Field(
        default=None,
        description="Tags for run"
    )

class FineTuningJobRequest(BaseModel):
    """Request to create a fine-tuning job."""
    model: str = Field(description="Base model ID to fine-tune")
    training_file: str = Field(description="Training file ID")
    validation_file: str | None = Field(
        default=None,
        description="Validation file ID"
    )
    hyperparameters: Hyperparameters | None = Field(
        default=None,
        description="Training hyperparameters (deprecated, use method.*.hyperparameters)"
    )
    suffix: str | None = Field(
        default=None,
        max_length=40,
        description="Model name suffix"
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility"
    )
    method: Method | None = Field(
        default=None,
        description="Fine-tuning method configuration"
    )
    integrations: list[Integration] | None = Field(
        default=None,
        description="Third-party integrations"
    )
```

### 8.2 Response Schemas

#### 8.2.1 FineTuningJob

```python
class JobStatus(str, Enum):
    """Fine-tuning job status."""
    VALIDATING_FILES = "validating_files"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Error(BaseModel):
    """Error information."""
    code: str = Field(description="Error code")
    message: str = Field(description="Error message")
    param: str | None = Field(
        default=None,
        description="Parameter that caused the error"
    )

class FineTuningJob(BaseModel):
    """Fine-tuning job object."""
    id: str = Field(description="Job ID")
    object: Literal["fine_tuning.job"] = Field(
        default="fine_tuning.job",
        description="Object type"
    )
    model: str = Field(description="Base model ID")
    created_at: int = Field(description="Unix timestamp of creation")
    finished_at: int | None = Field(
        default=None,
        description="Unix timestamp of completion"
    )
    fine_tuned_model: str | None = Field(
        default=None,
        description="Fine-tuned model ID"
    )
    organization_id: str = Field(description="Organization ID")
    result_files: list[str] = Field(
        default_factory=list,
        description="Result file IDs"
    )
    status: JobStatus = Field(description="Job status")
    validation_file: str | None = Field(
        default=None,
        description="Validation file ID"
    )
    training_file: str = Field(description="Training file ID")
    hyperparameters: Hyperparameters = Field(
        description="Training hyperparameters"
    )
    trained_tokens: int | None = Field(
        default=None,
        description="Total tokens trained"
    )
    error: Error | None = Field(
        default=None,
        description="Error details if failed"
    )
    user_provided_suffix: str | None = Field(
        default=None,
        description="User-provided model suffix"
    )
    seed: int | None = Field(
        default=None,
        description="Random seed"
    )
    estimated_finish: int | None = Field(
        default=None,
        description="Estimated completion timestamp"
    )
    method: Method | None = Field(
        default=None,
        description="Fine-tuning method"
    )
    integrations: list[Integration] = Field(
        default_factory=list,
        description="Integrations"
    )

class FineTuningJobListResponse(BaseModel):
    """List of fine-tuning jobs."""
    object: Literal["list"] = Field(
        default="list",
        description="Object type"
    )
    data: list[FineTuningJob] = Field(description="Job objects")
    has_more: bool = Field(description="Whether there are more results")
```

#### 8.2.2 FineTuningEvent

```python
class EventLevel(str, Enum):
    """Event level."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class EventType(str, Enum):
    """Event type."""
    MESSAGE = "message"
    METRICS = "metrics"
    CHECKPOINT_CREATED = "checkpoint_created"

class FineTuningEvent(BaseModel):
    """Fine-tuning job event."""
    id: str = Field(description="Event ID")
    object: Literal["fine_tuning.job.event"] = Field(
        default="fine_tuning.job.event",
        description="Object type"
    )
    created_at: int = Field(description="Unix timestamp")
    level: EventLevel = Field(description="Event level")
    message: str = Field(description="Human-readable message")
    type: EventType = Field(description="Event type")
    data: dict[str, Any] | None = Field(
        default=None,
        description="Additional structured data"
    )

class FineTuningEventListResponse(BaseModel):
    """List of fine-tuning events."""
    object: Literal["list"] = Field(
        default="list",
        description="Object type"
    )
    data: list[FineTuningEvent] = Field(description="Event objects")
    has_more: bool = Field(description="Whether there are more results")
```

#### 8.2.3 FineTuningCheckpoint

```python
class CheckpointMetrics(BaseModel):
    """Checkpoint metrics."""
    step: int = Field(description="Training step")
    train_loss: float = Field(description="Training loss")
    train_mean_token_accuracy: float = Field(
        description="Training token accuracy"
    )
    valid_loss: float | None = Field(
        default=None,
        description="Validation loss (batch)"
    )
    valid_mean_token_accuracy: float | None = Field(
        default=None,
        description="Validation token accuracy (batch)"
    )
    full_valid_loss: float | None = Field(
        default=None,
        description="Validation loss (full)"
    )
    full_valid_mean_token_accuracy: float | None = Field(
        default=None,
        description="Validation token accuracy (full)"
    )

class FineTuningCheckpoint(BaseModel):
    """Fine-tuning job checkpoint."""
    id: str = Field(description="Checkpoint ID")
    object: Literal["fine_tuning.job.checkpoint"] = Field(
        default="fine_tuning.job.checkpoint",
        description="Object type"
    )
    created_at: int = Field(description="Unix timestamp")
    fine_tuning_job_id: str = Field(description="Parent job ID")
    fine_tuned_model_checkpoint: str = Field(
        description="Checkpoint model ID"
    )
    step_number: int = Field(description="Training step")
    metrics: CheckpointMetrics = Field(description="Training metrics")

class CheckpointListResponse(BaseModel):
    """List of checkpoints."""
    object: Literal["list"] = Field(
        default="list",
        description="Object type"
    )
    data: list[FineTuningCheckpoint] = Field(description="Checkpoint objects")
    has_more: bool = Field(description="Whether there are more results")
```

---

## 9. Cost and Pricing Models

### 9.1 OpenAI Pricing (2025)

#### 9.1.1 Training Costs

**Supervised Fine-Tuning (SFT) and DPO:**

| Model | Training Price per 1M Tokens |
|-------|------------------------------|
| GPT-3.5-turbo | $8.00 |
| GPT-4o-mini | $3.00 |
| GPT-4o | $25.00 |

**Formula:**
```
Cost = (# training tokens × # epochs × price per 1M tokens) / 1,000,000
```

**Example:**
- Training file: 100,000 tokens
- Epochs: 3
- Model: GPT-4o-mini
- Cost: (100,000 × 3 × $3.00) / 1,000,000 = **$0.90**

**Reinforcement Fine-Tuning (RFT):**

| Model | Price per Hour |
|-------|----------------|
| o4-mini-2025-04-16 | $100.00 |

**Not Billed:**
- Queue time
- Failed jobs (before training starts)
- Cancelled jobs (before training starts)
- Data safety checks

#### 9.1.2 Inference Costs (Fine-Tuned Models)

**Fine-tuned models cost more than base models:**

| Base Model | Base Input | Base Output | Fine-Tuned Input | Fine-Tuned Output |
|------------|------------|-------------|------------------|-------------------|
| GPT-3.5-turbo | $0.50 | $1.50 | $3.00 | $6.00 |
| GPT-4o-mini | $0.15 | $0.60 | $0.30 | $1.20 |
| GPT-4o | $2.50 | $10.00 | $5.00 | $15.00 |

*Prices per 1M tokens*

#### 9.1.3 Grader Costs (RFT)

If using OpenAI model as grader:
- Grader inference billed at standard API rates
- Charged after training completes
- Example: GPT-4o grader @ $2.50 per 1M input tokens

### 9.2 Azure OpenAI Pricing

#### 9.2.1 Training Costs

**Token-Based Billing (Introduced 2024):**

Similar to OpenAI, but with regional variations.

**Serverless Fine-Tuning:**
- Base: $1.70 per 1M tokens
- No infrastructure costs
- Consumption-based pricing

#### 9.2.2 Deployment Costs

**Hourly Hosting:**
- Fine-tuned models incur hourly hosting cost when deployed
- Cost depends on model size and region
- Typical: $0.50-$2.00 per hour per deployment
- Inactive deployments don't affect model (can redeploy anytime)

### 9.3 Cost Optimization Strategies

#### 9.3.1 Training Data Optimization

**Reduce Training Tokens:**
- Use fewer, higher-quality examples
- Remove redundant data
- Recommended: 50-500 examples (not thousands)

**Reduce Epochs:**
- Start with 1-2 epochs
- Monitor validation loss
- Add epochs only if needed

**Example Savings:**
```
Original: 10,000 tokens × 10 epochs = 100,000 token-epochs
Optimized: 500 tokens × 3 epochs = 1,500 token-epochs
Savings: 98.5%
```

#### 9.3.2 Model Selection

**Start Small:**
- Use GPT-4o-mini instead of GPT-4o for testing
- Training: $3 vs $25 per 1M tokens
- Inference: $0.30 vs $5.00 per 1M input tokens

**Upgrade Only If Needed:**
- Test with smaller model first
- Upgrade to larger model if quality insufficient
- Most use cases work well with mini models

#### 9.3.3 Validation File Usage

**Optional but Valuable:**
- Validation file helps detect overfitting
- Prevents wasted epochs
- Small cost (same as training data)
- Worth it for production models

**Recommendation:**
- Include validation file (10-20% of training size)
- Monitor `full_valid_loss`
- Stop early if validation loss increases

---

## 10. Appendix: Code Examples

### 10.1 Creating a Fine-Tuning Job

#### 10.1.1 Python (openai library)

```python
from openai import OpenAI

client = OpenAI(api_key="your-api-key")

# Create fine-tuning job
job = client.fine_tuning.jobs.create(
    training_file="file-abc123",
    validation_file="file-xyz789",
    model="openai/gpt-oss-20b-2024-07-18",
    hyperparameters={
        "n_epochs": 3,
        "batch_size": 1,
        "learning_rate_multiplier": 1.8
    },
    suffix="customer-support"
)

print(f"Job created: {job.id}")
print(f"Status: {job.status}")
```

#### 10.1.2 cURL

```bash
curl https://api.openai.com/v1/fine_tuning/jobs \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "training_file": "file-abc123",
    "validation_file": "file-xyz789",
    "model": "openai/gpt-oss-20b-2024-07-18",
    "hyperparameters": {
      "n_epochs": 3
    },
    "suffix": "customer-support"
  }'
```

### 10.2 Listing Jobs and Monitoring Progress

```python
# List all jobs
jobs = client.fine_tuning.jobs.list(limit=10)
for job in jobs.data:
    print(f"{job.id}: {job.status}")

# Get specific job
job = client.fine_tuning.jobs.retrieve("ftjob-abc123")
print(f"Status: {job.status}")
print(f"Trained tokens: {job.trained_tokens}")

# List events
events = client.fine_tuning.jobs.list_events(
    fine_tuning_job_id="ftjob-abc123",
    limit=20
)
for event in events.data:
    print(f"[{event.level}] {event.message}")
```

### 10.3 Streaming Events

```python
# Stream events in real-time
for event in client.fine_tuning.jobs.events(
    fine_tuning_job_id="ftjob-abc123",
    stream=True
):
    print(event.message)
```

### 10.4 Listing Checkpoints

```python
# Get checkpoints
checkpoints = client.fine_tuning.jobs.checkpoints.list(
    fine_tuning_job_id="ftjob-abc123"
)

for checkpoint in checkpoints.data:
    print(f"Step {checkpoint.step_number}:")
    print(f"  Model: {checkpoint.fine_tuned_model_checkpoint}")
    print(f"  Train loss: {checkpoint.metrics.train_loss:.4f}")
    print(f"  Valid loss: {checkpoint.metrics.full_valid_loss:.4f}")
```

### 10.5 Using Fine-Tuned Model

```python
# After job succeeds, use the fine-tuned model
response = client.chat.completions.create(
    model="ft:openai/gpt-oss-20b-2024-07-18:my-org:customer-support:abc123",
    messages=[
        {"role": "user", "content": "How do I return an item?"}
    ]
)

print(response.choices[0].message.content)
```

### 10.6 Cancelling a Job

```python
# Cancel running job
job = client.fine_tuning.jobs.cancel("ftjob-abc123")
print(f"Job cancelled: {job.status}")
```

### 10.7 Preparing Training Data

```python
import json

# Create training data
training_data = [
    {
        "messages": [
            {"role": "system", "content": "You are a helpful customer support agent."},
            {"role": "user", "content": "What is your return policy?"},
            {"role": "assistant", "content": "Our return policy allows returns within 30 days..."}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": "You are a helpful customer support agent."},
            {"role": "user", "content": "How do I track my order?"},
            {"role": "assistant", "content": "You can track your order using the tracking number..."}
        ]
    }
]

# Write to JSONL file
with open("training_data.jsonl", "w") as f:
    for example in training_data:
        f.write(json.dumps(example) + "\n")

# Upload file
with open("training_data.jsonl", "rb") as f:
    file = client.files.create(
        file=f,
        purpose="fine-tune"
    )

print(f"File uploaded: {file.id}")
```

### 10.8 DPO Training Data Example

```python
# DPO requires preference pairs
dpo_training_data = [
    {
        "messages": [
            {"role": "user", "content": "Write a poem about coding."}
        ],
        "chosen": {
            "role": "assistant",
            "content": "Code flows like poetry, elegant and bright,\nSolving problems through the night..."
        },
        "rejected": {
            "role": "assistant",
            "content": "Writing code is boring and repetitive."
        }
    }
]

# Write to JSONL
with open("dpo_training_data.jsonl", "w") as f:
    for example in dpo_training_data:
        f.write(json.dumps(example) + "\n")
```

---

## Conclusion

This research provides comprehensive technical details for implementing fine-tuning API simulation in FakeAI. The OpenAI fine-tuning API is well-documented and follows consistent patterns, making it an ideal candidate for simulation.

**Key Takeaways:**

1. **Six API Endpoints:** Jobs CRUD + Events + Checkpoints
2. **Six Job States:** validating_files → queued → running → succeeded/failed/cancelled
3. **Three Fine-Tuning Methods:** SFT, DPO, RFT (focus on SFT first)
4. **JSONL Training Format:** Conversational messages with roles
5. **Event Streaming:** SSE support for real-time progress
6. **Epoch-Based Checkpoints:** Automatic model snapshots
7. **Realistic Metrics:** Decreasing loss curves, increasing accuracy
8. **Model Registration:** Auto-create fine-tuned models for use in completions

**Implementation Priority:**

1. **High Priority:** SFT with basic job lifecycle, events, checkpoints
2. **Medium Priority:** DPO support, event streaming, validation metrics
3. **Low Priority:** RFT support (complex, less common)

**Next Steps:**

1. Review schemas and implementation strategy
2. Create Pydantic models in `/home/anthony/projects/fakeai/fakeai/models.py`
3. Implement service methods in `/home/anthony/projects/fakeai/fakeai/fakeai_service.py`
4. Add FastAPI routes in `/home/anthony/projects/fakeai/fakeai/app.py`
5. Write comprehensive tests
6. Update documentation

---

**Document Version:** 1.0
**Last Updated:** 2025-10-04
**Author:** AI Research Assistant (Claude)
**Status:** Complete
