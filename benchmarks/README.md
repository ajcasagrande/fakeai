# FakeAI Performance Benchmark Suite

Comprehensive benchmarking tools for measuring FakeAI server performance under various conditions.

## Overview

This benchmark suite provides two approaches:

### 1. **AIPerf (Recommended)** - Industry-Standard Benchmarking
Uses [ai-dynamo/aiperf](https://github.com/ai-dynamo/aiperf), the successor to NVIDIA GenAI-Perf, for comprehensive LLM inference benchmarking with:
- Multiprocess support for high concurrency
- Multiple benchmarking modes (concurrency, request-rate, trace replay)
- Public dataset support
- Industry-standard metrics (TTFT, ITL, TPOT, throughput)
- OpenAI-compatible API support

### 2. **Custom Python Benchmarks** - Internal Testing
Legacy Python scripts for specific FakeAI feature testing:
1. **Throughput** - Requests per second with various payload sizes
2. **KV Cache** - Cache hit rates, prefix sharing, and latency improvements
3. **Concurrent Connections** - Performance under high concurrency
4. **Memory Usage** - Memory tracking and leak detection

## Requirements

### For AIPerf (Recommended)

```bash
pip install aiperf
```

### For Custom Benchmarks

```bash
pip install httpx psutil matplotlib
```

## Quick Start

### 1. Start FakeAI Server

First, start the FakeAI server in a separate terminal:

```bash
cd /home/anthony/projects/fakeai
python run_server.py
```

Or with optimized settings for benchmarking:

```bash
fakeai-server --host 0.0.0.0 --port 9001 --ttft 20 --itl 5
```

---

## AIPerf Benchmarking (Recommended)

### Installation

```bash
pip install aiperf
```

### Basic Usage

```bash
aiperf profile \
  --model openai/gpt-oss-120b \
  --url http://localhost:9001 \
  --endpoint-type chat \
  --service-kind openai \
  --streaming
```

### Common Benchmark Scenarios

#### 1. Concurrency Test

Test performance under different concurrency levels:

```bash
aiperf profile \
  --model openai/gpt-oss-120b \
  --url http://localhost:9001 \
  --endpoint-type chat \
  --service-kind openai \
  --streaming \
  --concurrency 100 \
  --request-count 1000 \
  --synthetic-tokens-mean 300 \
  --output-tokens-mean 1000
```

#### 2. Request Rate Test

Test at a fixed request rate:

```bash
aiperf profile \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --url http://localhost:9001 \
  --endpoint-type chat \
  --service-kind openai \
  --streaming \
  --request-rate 50 \
  --request-count 500
```

#### 3. Multiple Models Test

Benchmark different models:

```bash
# Test gpt-oss-120b
aiperf profile \
  --model openai/gpt-oss-120b \
  --url http://localhost:9001 \
  --endpoint-type chat \
  --service-kind openai \
  --streaming \
  --concurrency 100 \
  --request-count 500

# Test DeepSeek-R1
aiperf profile \
  --model deepseek-ai/DeepSeek-R1 \
  --url http://localhost:9001 \
  --endpoint-type chat \
  --service-kind openai \
  --streaming \
  --concurrency 100 \
  --request-count 500
```

#### 4. Embeddings Benchmark

Test embedding generation:

```bash
aiperf profile \
  --model sentence-transformers/all-mpnet-base-v2 \
  --url http://localhost:9001 \
  --endpoint-type embeddings \
  --service-kind openai \
  --request-count 1000 \
  --concurrency 50
```

#### 5. Non-Streaming Test

Compare streaming vs non-streaming:

```bash
# Non-streaming
aiperf profile \
  --model openai/gpt-oss-120b \
  --url http://localhost:9001 \
  --endpoint-type chat \
  --service-kind openai \
  --concurrency 50 \
  --request-count 500

# Streaming
aiperf profile \
  --model openai/gpt-oss-120b \
  --url http://localhost:9001 \
  --endpoint-type chat \
  --service-kind openai \
  --streaming \
  --concurrency 50 \
  --request-count 500
```

### AIPerf Command Reference

**Required Arguments:**
- `--model MODEL_NAME` - Model identifier (e.g., openai/gpt-oss-120b)
- `--url URL` - Server URL (must include `http://` or `https://`)
- `--endpoint-type TYPE` - API endpoint type: `chat`, `completions`, `embeddings`

**Common Arguments:**
- `--service-kind openai` - Use OpenAI-compatible API format
- `--streaming` - Enable streaming mode
- `--concurrency N` - Number of concurrent requests (default: 1)
- `--request-count N` - Total number of requests (default: 100)
- `--request-rate N` - Requests per second (alternative to concurrency)

**Token Configuration:**
- `--synthetic-tokens-mean N` - Average input tokens (default: 128)
- `--synthetic-tokens-stddev N` - Input token variance (default: 0)
- `--output-tokens-mean N` - Average output tokens (default: 100)
- `--output-tokens-stddev N` - Output token variance (default: 0)

**Output Configuration:**
- `--artifact-directory DIR` - Output directory (default: `artifacts`)
- `--profile-export-file FILE` - JSON export filename

### Understanding AIPerf Output

AIPerf generates comprehensive metrics including:

**Latency Metrics:**
- **Time to First Token (TTFT)**: Time from request to first token (p50, p90, p99)
- **Inter-Token Latency (ITL)**: Time between tokens (p50, p90, p99)
- **Time Per Output Token (TPOT)**: Average time per generated token
- **Request Latency**: Total request duration (avg, p50, p90, p99)

**Throughput Metrics:**
- **Request Throughput**: Requests per second
- **Output Token Throughput**: Tokens generated per second
- **Input Token Throughput**: Tokens processed per second

**Token Metrics:**
- **Input Sequence Length**: Input token count (avg, min, max, p50, p90, p99)
- **Output Sequence Length**: Output token count (avg, min, max, p50, p90, p99)

**Example Output Structure:**
```json
{
  "request_throughput": {"unit": "requests/sec", "avg": 930.01},
  "request_latency": {
    "unit": "ms",
    "avg": 491.93,
    "p50": 511.32,
    "p90": 633.67,
    "p99": 636.32
  },
  "time_to_first_token": {
    "unit": "ms",
    "avg": 491.93,
    "p50": 511.32,
    "p99": 636.32
  },
  "output_token_throughput": {"unit": "tokens/sec", "avg": 198909.67}
}
```

### Automated Benchmark Runner

Use the provided benchmark runner script for comprehensive testing:

```bash
cd /home/anthony/projects/fakeai/benchmarks
python run_aiperf_benchmarks.py
```

This will automatically:
- Test multiple models (gpt-oss-120b, Llama-3.1-8B, DeepSeek-R1)
- Run various concurrency levels (10, 50, 100, 250, 500)
- Test both streaming and non-streaming modes
- Generate comprehensive reports and JSON exports
- Create a summary comparison

**Customize the runner:**
```bash
# Quick test (fewer configurations)
python run_aiperf_benchmarks.py --quick

# Specific models only
python run_aiperf_benchmarks.py --models openai/gpt-oss-120b deepseek-ai/DeepSeek-R1

# Custom server URL
python run_aiperf_benchmarks.py --url http://localhost:8000

# Custom concurrency levels
python run_aiperf_benchmarks.py --concurrency 50 100 200
```

**Runner Output:**
- Individual benchmark results in `artifacts/<benchmark-name>/`
- JSON summary in `artifacts/benchmark_summary.json`
- Markdown report in `artifacts/BENCHMARK_REPORT.md`

### AIPerf Best Practices

**Optimal FakeAI Configuration for Benchmarking:**
```bash
# Minimize latency simulation for throughput testing
fakeai-server --host 0.0.0.0 --port 9001 --ttft 5 --itl 1

# Realistic production-like latency
fakeai-server --host 0.0.0.0 --port 9001 --ttft 20 --itl 5

# High variance testing
fakeai-server --host 0.0.0.0 --port 9001 --ttft 50:30 --itl 10:30
```

**Performance Tips:**
1. **Always include `http://` in URL** - `localhost:9001` will fail
2. **Start with low concurrency** - Test 10-50 concurrent requests first
3. **Use `--quick` mode** for initial validation
4. **Monitor server logs** during benchmarks for errors
5. **Consistent environment** - Close other applications during testing

**Interpreting Results:**

Good performance indicators:
- **Request throughput** > 100 rps for concurrency 50
- **P99 latency** < 1000ms at reasonable concurrency
- **TTFT P99** < 200ms (depends on configuration)
- **Token throughput** > 10,000 tokens/sec

Warning signs:
- High P99 latency (> 2x avg latency)
- Low throughput despite high concurrency
- Missing or zero metrics in output

### Troubleshooting AIPerf

**Issue: "No results file found"**
```
 FAILED - No results file found
```
**Causes:**
- aiperf crashed during execution
- URL incorrect (missing `http://`)
- Server not reachable
- Permission issues writing artifacts

**Solution:**
```bash
# Verify server is running
curl http://localhost:9001/health

# Check URL format
aiperf profile --model openai/gpt-oss-120b --url http://localhost:9001 \
  --endpoint-type chat --service-kind openai

# Check aiperf logs for errors
```

**Issue: "High concurrency causes port exhaustion"**
```
ERROR: Cannot assign requested address
```
**Solution:**
```bash
# Reduce concurrency or increase system limits
python run_aiperf_benchmarks.py --concurrency 50 100

# Or adjust system TCP settings (Linux)
sudo sysctl -w net.ipv4.ip_local_port_range="1024 65535"
sudo sysctl -w net.ipv4.tcp_tw_reuse=1
```

**Issue: "All metrics are zero"**
```json
{
  "request_throughput": {"avg": 0.0},
  "request_latency": {"avg": 0.0}
}
```
**Causes:**
- Wrong URL (missing protocol)
- Incorrect endpoint-type
- Server returned errors
- Authentication failed

**Solution:**
```bash
# Verify endpoint manually
curl -X POST http://localhost:9001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "test"}]}'

# Check URL format in aiperf command
aiperf profile --model openai/gpt-oss-120b \
  --url http://localhost:9001 \  # Must include http://
  --endpoint-type chat \
  --service-kind openai
```

**Issue: "Benchmark timeout after 10 minutes"**
```
 TIMEOUT after 10 minutes
```
**Solution:**
```bash
# Reduce request count or concurrency
python run_aiperf_benchmarks.py --quick

# Or edit script to increase timeout (line 165)
```

**Issue: "aiperf command not found"**
```
 ERROR: aiperf is not installed
```
**Solution:**
```bash
pip install aiperf

# Verify installation
aiperf --version
```

---

## Custom Python Benchmarks (Legacy)

### 2. Run All Benchmarks

```bash
cd /home/anthony/projects/fakeai/benchmarks
python run_benchmarks.py
```

This will:
- Run all benchmark suites
- Generate markdown reports
- Save JSON results
- Create a summary report

### 3. Run Quick Tests

For faster testing during development:

```bash
python run_benchmarks.py --quick
```

### 4. Skip Memory Tests

If psutil is not installed:

```bash
python run_benchmarks.py --skip-memory
```

## Individual Benchmarks

You can run each benchmark individually:

### Throughput Benchmark

Measures requests per second with various payload sizes and streaming modes.

```bash
python benchmark_throughput.py
python benchmark_throughput.py http://localhost:8000 test-api-key
```

**Tests:**
- Small payload (non-streaming)
- Small payload (streaming)
- Medium payload (both modes)
- Large payload (both modes)
- High concurrency test

**Output:** `throughput_results.md`

### KV Cache Benchmark

Tests cache hit rates, prefix sharing, and latency improvements.

```bash
python benchmark_kv_cache.py
```

**Tests:**
- Cache hit rates with shared prefixes
- Prefix sharing efficiency
- Smart router load balancing

**Output:** `kv_cache_results.md`

### Concurrent Connections Benchmark

Tests performance under various concurrency levels.

```bash
python benchmark_concurrent.py
```

**Tests:**
- 10, 50, 100, 200 concurrent connections
- Sustained load test
- Optional ramp-up test

**Metrics:**
- P50, P90, P95, P99 latencies
- Requests per second
- Error rates
- Success rates

**Output:** `concurrent_results.md`

### Memory Benchmark

Tracks memory usage, detects leaks, and measures cache overhead.

```bash
python benchmark_memory.py
```

**Requirements:** psutil

**Tests:**
- Low load (5 RPS)
- Medium load (20 RPS)
- KV cache overhead
- Long-running leak detection (120s)

**Output:** `memory_results.md`

## Command-Line Options

### Main Runner

```bash
python run_benchmarks.py [options]

Options:
  --url URL          Server URL (default: http://localhost:8000)
  --api-key KEY      API key (default: test)
  --quick            Run quick tests only
  --skip-memory      Skip memory benchmarks
  -h, --help         Show help message
```

### Individual Benchmarks

All individual benchmarks accept:

```bash
python benchmark_NAME.py [base_url] [api_key]
```

Examples:

```bash
python benchmark_throughput.py http://localhost:9000 my-key
python benchmark_kv_cache.py http://192.168.1.100:8000
```

## Output Files

After running benchmarks, you'll find:

```
benchmarks/
 throughput_results.md       # Throughput report
 kv_cache_results.md         # KV cache report
 concurrent_results.md       # Concurrent connections report
 memory_results.md           # Memory usage report
 BENCHMARK_SUMMARY.md        # Overall summary
 throughput_results.json     # Raw throughput data
 kv_cache_results.json       # Raw cache data
 concurrent_results.json     # Raw concurrent data
 memory_results.json         # Raw memory data
```

## Understanding Results

### Throughput Metrics

- **RPS (Requests per Second):** Total successful requests divided by time
- **Tokens/sec:** Total tokens processed per second
- **P50/P90/P99 Latency:** Percentile latencies in milliseconds
- **Streaming vs Non-streaming:** Performance comparison

**Good Performance:**
- RPS > 50 for small payloads
- P99 latency < 500ms
- Consistent performance across payload sizes

### KV Cache Metrics

- **Hit Rate:** Percentage of requests that hit cache (target: > 60%)
- **Latency Improvement:** Speed increase from cache hits (target: > 30%)
- **Token Reuse Rate:** Percentage of tokens reused from cache
- **Avg Prefix Length:** Average matched prefix tokens

**Good Performance:**
- Hit rate > 60%
- Latency improvement > 30%
- Token reuse rate > 40%

### Concurrent Connection Metrics

- **Success Rate:** Percentage of successful requests (target: 100%)
- **P99 Latency:** 99th percentile latency (target: < 1000ms)
- **Max Concurrent:** Maximum concurrency without errors

**Good Performance:**
- Success rate: 100% at reasonable concurrency
- P99 latency stays stable as concurrency increases
- Handles 100+ concurrent connections

### Memory Metrics

- **Memory Growth:** Change in RSS memory (target: < 10 MB for tests)
- **Leak Detected:** Yes/No based on linear regression
- **Growth Rate:** MB per minute (target: < 1 MB/min)
- **Avg per Request:** Memory overhead per request (target: < 10 KB)

**Good Performance:**
- No leaks detected
- Stable memory usage over time
- Low per-request overhead

## Customizing Benchmarks

### Custom Payload

Edit individual benchmark files to customize payloads:

```python
# In benchmark_throughput.py
custom_payload = {
    "model": "openai/gpt-oss-120b",
    "messages": [
        {"role": "system", "content": "Your custom system prompt"},
        {"role": "user", "content": "Your custom user message"}
    ],
    "max_tokens": 500,
    "temperature": 0.7,
}

await benchmark.run_benchmark(
    "Custom Test",
    num_requests=100,
    payload=custom_payload,
    payload_size="custom",
    streaming=False,
    concurrent_limit=10,
)
```

### Custom Test Duration

```python
# In benchmark_memory.py
await benchmark.run_memory_test(
    test_name="Extended Memory Test",
    duration_seconds=300,  # 5 minutes
    requests_per_second=10,
    payload=payload,
    snapshot_interval=15.0,
)
```

### Custom Concurrency Levels

```python
# In benchmark_concurrent.py
for concurrency in [10, 25, 50, 100, 150, 200]:
    await benchmark.run_concurrent_test(
        test_name=f"{concurrency} Concurrent",
        num_requests=concurrency * 2,
        concurrent_connections=concurrency,
        payload=payload,
    )
```

## Continuous Benchmarking

### Running Periodically

Create a cron job to run benchmarks regularly:

```bash
# Run benchmarks daily at 2 AM
0 2 * * * cd /home/anthony/projects/fakeai/benchmarks && python run_benchmarks.py --quick
```

### Comparing Results

Use the reporting utilities to compare multiple runs:

```python
from benchmark_utils import BenchmarkReporter

reporter = BenchmarkReporter()
reporter.create_comparison_report(
    results_files=[
        "throughput_results_2024_01.json",
        "throughput_results_2024_02.json",
    ],
    output_filename="monthly_comparison.md"
)
```

## Troubleshooting

### Server Not Reachable

```
ERROR: Server is not reachable!
```

**Solution:** Ensure FakeAI server is running:

```bash
python run_server.py
# In another terminal:
curl http://localhost:8000/health
```

### Memory Benchmark Fails

```
Warning: psutil not available
```

**Solution:** Install psutil:

```bash
pip install psutil
```

Or skip memory tests:

```bash
python run_benchmarks.py --skip-memory
```

### Import Errors

```
ModuleNotFoundError: No module named 'httpx'
```

**Solution:** Install dependencies:

```bash
pip install httpx
```

### High Error Rates

If concurrent tests show high error rates:

1. Increase server resources
2. Reduce concurrency levels
3. Adjust response delays in server config
4. Check server logs for errors

### Memory Leaks Detected

If memory benchmarks detect leaks:

1. Review server memory management
2. Check for unclosed connections
3. Verify garbage collection is working
4. Monitor server logs during tests

## Performance Optimization Tips

### Server Configuration

For best benchmark results, configure FakeAI with:

```bash
export FAKEAI_RESPONSE_DELAY=0.1
export FAKEAI_RANDOM_DELAY=true
export FAKEAI_MAX_VARIANCE=0.2
export FAKEAI_ENABLE_PROMPT_CACHING=true

fakeai-server --host 0.0.0.0 --port 8000
```

### System Resources

- Close unnecessary applications
- Ensure sufficient RAM (4GB+ recommended)
- Use SSD storage for faster I/O
- Disable CPU throttling during tests

### Network

- Run benchmarks on localhost for best results
- Minimize network hops
- Ensure stable network connection

## Advanced Usage

### Generating Charts

If matplotlib is installed, enable chart generation:

```python
from benchmark_utils import generate_latency_chart

generate_latency_chart(
    latencies=result.latencies,
    title="Latency Distribution",
    output_path="latency_chart.png"
)
```

### Custom Metrics

Add custom metrics to benchmarks:

```python
# Track custom metrics
custom_metrics = {
    "cache_effectiveness": cache_hits / total_requests,
    "avg_tokens_per_request": total_tokens / total_requests,
}

# Include in report
report += f"## Custom Metrics\n\n"
for key, value in custom_metrics.items():
    report += f"- {key}: {value:.2f}\n"
```

### Load Testing

For extended load testing:

```python
await benchmark.run_sustained_load_test(
    duration_seconds=3600,  # 1 hour
    requests_per_second=50,
    payload=payload,
)
```

## Contributing

To add new benchmarks:

1. Create `benchmark_NAME.py` following existing patterns
2. Implement benchmark class with `run_benchmark()` method
3. Add markdown report generation
4. Update `run_benchmarks.py` to include new benchmark
5. Update this README

## License

Apache-2.0 License - See LICENSE file for details.

## Support

For issues or questions:
- Check existing documentation
- Review error messages and logs
- Test with `--quick` mode first
- Verify server is running and reachable

---

## Quick Reference

### AIPerf (Recommended)
```bash
# Install
pip install aiperf

# Single benchmark
aiperf profile --model openai/gpt-oss-120b --url http://localhost:9001 \
  --endpoint-type chat --service-kind openai --streaming

# Automated suite
python run_aiperf_benchmarks.py --quick

# Full suite
python run_aiperf_benchmarks.py
```

### Legacy Custom Benchmarks
```bash
# Install
pip install httpx psutil matplotlib

# Run all
python run_benchmarks.py --quick

# Individual
python benchmark_throughput.py
```

---

**Last Updated:** 2025-10-04
**Version:** 0.0.5
**Major Changes:** Added AIPerf support and automated benchmark runner
