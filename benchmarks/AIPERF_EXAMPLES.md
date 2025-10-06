# AIPerf Benchmark Examples for FakeAI

Quick reference guide for running benchmarks with aiperf against FakeAI server.

## Prerequisites

```bash
# Install aiperf
pip install aiperf

# Start FakeAI server (in separate terminal)
fakeai-server --host 0.0.0.0 --port 9001 --ttft 20 --itl 5
```

---

## Basic Examples

### 1. Single Chat Completion Benchmark

```bash
aiperf profile \
  --model openai/gpt-oss-120b \
  --url http://localhost:9001 \
  --endpoint-type chat \
  --service-kind openai \
  --streaming \
  --concurrency 50 \
  --request-count 100
```

**Expected Output:**
- Request throughput: ~500-1000 rps
- TTFT: ~20-30ms (depending on configuration)
- Output token throughput: ~50,000-200,000 tokens/sec

---

### 2. High Concurrency Test

```bash
aiperf profile \
  --model deepseek-ai/DeepSeek-R1 \
  --url http://localhost:9001 \
  --endpoint-type chat \
  --service-kind openai \
  --streaming \
  --concurrency 500 \
  --request-count 1000 \
  --synthetic-tokens-mean 300 \
  --output-tokens-mean 1000
```

**Use Case:** Stress testing under high load

---

### 3. Embeddings Benchmark

```bash
aiperf profile \
  --model sentence-transformers/all-mpnet-base-v2 \
  --url http://localhost:9001 \
  --endpoint-type embeddings \
  --service-kind openai \
  --concurrency 100 \
  --request-count 500
```

**Use Case:** Test embedding generation performance

---

### 4. Non-Streaming Comparison

```bash
# Without streaming
aiperf profile \
  --model openai/gpt-oss-120b \
  --url http://localhost:9001 \
  --endpoint-type chat \
  --service-kind openai \
  --concurrency 50 \
  --request-count 500

# With streaming
aiperf profile \
  --model openai/gpt-oss-120b \
  --url http://localhost:9001 \
  --endpoint-type chat \
  --service-kind openai \
  --streaming \
  --concurrency 50 \
  --request-count 500
```

**Use Case:** Compare streaming vs non-streaming performance

---

### 5. Custom Token Configuration

```bash
aiperf profile \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --url http://localhost:9001 \
  --endpoint-type chat \
  --service-kind openai \
  --streaming \
  --concurrency 100 \
  --request-count 500 \
  --synthetic-tokens-mean 512 \
  --synthetic-tokens-stddev 50 \
  --output-tokens-mean 2000 \
  --output-tokens-stddev 200
```

**Use Case:** Test with realistic token distributions (mean ± stddev)

---

## Automated Benchmark Runner Examples

### Quick Test (All Models)

```bash
cd /home/anthony/projects/fakeai/benchmarks
python run_aiperf_benchmarks.py --quick
```

**What it does:**
- Tests 3 models: gpt-oss-120b, Llama-3.1-8B, DeepSeek-R1
- Concurrency: 50
- Requests: 100 per model
- Total time: ~5-10 minutes

---

### Full Benchmark Suite

```bash
python run_aiperf_benchmarks.py
```

**What it does:**
- Tests 3 models
- Concurrency levels: 10, 50, 100, 250, 500
- Both streaming and non-streaming
- Total benchmarks: 18 (15 streaming + 3 non-streaming)
- Total time: ~1-2 hours

---

### Single Model Deep Test

```bash
python run_aiperf_benchmarks.py \
  --models openai/gpt-oss-120b \
  --concurrency 10 25 50 100 200 400
```

**What it does:**
- Tests only gpt-oss-120b
- 6 concurrency levels
- Streaming mode
- Total time: ~30 minutes

---

### Custom Server URL

```bash
python run_aiperf_benchmarks.py \
  --url http://192.168.1.100:8000 \
  --quick
```

**Use Case:** Benchmark remote FakeAI instance

---

### Multiple Models Comparison

```bash
python run_aiperf_benchmarks.py \
  --models openai/gpt-oss-120b deepseek-ai/DeepSeek-R1 \
  --concurrency 50 100 200
```

**What it does:**
- Compare 2 models
- 3 concurrency levels each
- 6 total benchmarks
- Generates comparison report

---

## Real-World Scenarios

### Scenario 1: Production Readiness Test

**Goal:** Verify server can handle production load

```bash
# Step 1: Start server with production-like settings
fakeai-server --host 0.0.0.0 --port 9001 --ttft 50:20 --itl 10:20

# Step 2: Run benchmark at expected load
aiperf profile \
  --model openai/gpt-oss-120b \
  --url http://localhost:9001 \
  --endpoint-type chat \
  --service-kind openai \
  --streaming \
  --concurrency 200 \
  --request-count 2000 \
  --synthetic-tokens-mean 500 \
  --output-tokens-mean 1500
```

**Success Criteria:**
- Request throughput > 100 rps
- P99 latency < 1000ms
- Zero errors

---

### Scenario 2: Latency Optimization

**Goal:** Find optimal TTFT/ITL settings

```bash
# Test 1: Minimal latency
fakeai-server --host 0.0.0.0 --port 9001 --ttft 5 --itl 1
python run_aiperf_benchmarks.py --quick

# Test 2: Moderate latency
fakeai-server --host 0.0.0.0 --port 9001 --ttft 20 --itl 5
python run_aiperf_benchmarks.py --quick

# Test 3: High latency
fakeai-server --host 0.0.0.0 --port 9001 --ttft 100 --itl 20
python run_aiperf_benchmarks.py --quick

# Compare results in artifacts/BENCHMARK_REPORT.md
```

---

### Scenario 3: Model Performance Comparison

**Goal:** Compare different model sizes

```bash
python run_aiperf_benchmarks.py \
  --models \
    TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
    meta-llama/Llama-3.1-8B-Instruct \
    openai/gpt-oss-120b \
  --concurrency 50 100 200
```

**Analysis:** Check `artifacts/BENCHMARK_REPORT.md` for throughput comparison

---

### Scenario 4: Concurrency Limit Discovery

**Goal:** Find maximum safe concurrency level

```bash
for c in 10 50 100 200 400 800 1000; do
  echo "Testing concurrency: $c"
  aiperf profile \
    --model openai/gpt-oss-120b \
    --url http://localhost:9001 \
    --endpoint-type chat \
    --service-kind openai \
    --streaming \
    --concurrency $c \
    --request-count $(($c * 2))
done
```

**Look for:** Point where throughput plateaus or errors increase

---

## Output Analysis Examples

### Example 1: Good Performance

```json
{
  "request_throughput": {"avg": 930.01},
  "request_latency": {
    "avg": 491.93,
    "p50": 511.32,
    "p99": 636.32
  },
  "time_to_first_token": {
    "avg": 491.93,
    "p99": 636.32
  },
  "output_token_throughput": {"avg": 198909.67}
}
```

**Indicators:**
-  High request throughput
-  Low P99 latency (< 1000ms)
-  Consistent TTFT
-  High token throughput

---

### Example 2: Warning Signs

```json
{
  "request_throughput": {"avg": 50.5},
  "request_latency": {
    "avg": 500.0,
    "p50": 450.0,
    "p99": 2500.0
  },
  "time_to_first_token": {
    "avg": 480.0,
    "p99": 2400.0
  }
}
```

**Issues:**
-  Low throughput (< 100 rps)
-  High P99 (> 5x avg)
-  Possible bottleneck

**Solutions:**
1. Reduce concurrency
2. Check server CPU/memory
3. Optimize TTFT/ITL settings

---

### Example 3: Configuration Issue

```json
{
  "request_throughput": {"avg": 0.0},
  "output_token_throughput": {"avg": 0.0}
}
```

**Problem:** Zero metrics = benchmark failed

**Common Causes:**
1. Wrong URL (missing `http://`)
2. Server not running
3. Incorrect endpoint-type
4. Authentication failure

**Fix:**
```bash
# Verify server
curl http://localhost:9001/health

# Check URL in command
aiperf profile --url http://localhost:9001 ...  # Must include http://
```

---

## Tips & Best Practices

### 1. Always Start with Quick Test

```bash
# First run
python run_aiperf_benchmarks.py --quick

# If successful, run full suite
python run_aiperf_benchmarks.py
```

### 2. Monitor Server During Benchmarks

```bash
# Terminal 1: Start server with debug
fakeai-server --debug --port 9001

# Terminal 2: Run benchmark
python run_aiperf_benchmarks.py --quick

# Terminal 3: Monitor metrics
watch -n 2 "curl -s http://localhost:9001/metrics | jq"
```

### 3. Progressive Concurrency Testing

```bash
# Start low
python run_aiperf_benchmarks.py --concurrency 10

# Increase gradually
python run_aiperf_benchmarks.py --concurrency 10 25 50 100

# Push limits
python run_aiperf_benchmarks.py --concurrency 100 200 400 800
```

### 4. Baseline Before Changes

```bash
# Before code changes
python run_aiperf_benchmarks.py
mv artifacts artifacts_baseline

# After code changes
python run_aiperf_benchmarks.py
mv artifacts artifacts_new

# Compare
diff artifacts_baseline/benchmark_summary.json artifacts_new/benchmark_summary.json
```

---

## Troubleshooting

### Problem: Port Exhaustion

```
ERROR: Cannot assign requested address
```

**Solution:**
```bash
# Increase port range (Linux)
sudo sysctl -w net.ipv4.ip_local_port_range="1024 65535"
sudo sysctl -w net.ipv4.tcp_tw_reuse=1

# Or reduce concurrency
python run_aiperf_benchmarks.py --concurrency 50 100
```

### Problem: Timeout

```
 TIMEOUT after 10 minutes
```

**Solution:**
```bash
# Reduce load
python run_aiperf_benchmarks.py --quick

# Or edit run_aiperf_benchmarks.py line 165:
# timeout=1200,  # 20 minutes
```

### Problem: Inconsistent Results

**Solution:**
```bash
# Run multiple times and average
for i in {1..3}; do
  python run_aiperf_benchmarks.py --quick
  mv artifacts/benchmark_summary.json artifacts/run_${i}.json
done
```

---

## Additional Resources

- **AIPerf GitHub:** https://github.com/ai-dynamo/aiperf
- **FakeAI Documentation:** /home/anthony/projects/fakeai/README.md
- **Benchmark Guide:** /home/anthony/projects/fakeai/benchmarks/BENCHMARK_GUIDE.md

---

**Last Updated:** 2025-10-04
**Version:** 0.0.5
