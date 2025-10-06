# FakeAI Performance Benchmark Suite - Complete Guide

**Version:** 0.0.4
**Last Updated:** 2025-10-04

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Benchmark Modules](#benchmark-modules)
6. [Results and Interpretation](#results-and-interpretation)
7. [Advanced Usage](#advanced-usage)
8. [Best Practices](#best-practices)

---

## Overview

The FakeAI Performance Benchmark Suite is a comprehensive testing framework designed to measure and validate the performance characteristics of the FakeAI server under various conditions.

### What It Tests

1. **Throughput Performance**
   - Requests per second (RPS)
   - Token generation rates
   - Streaming vs non-streaming performance
   - Payload size impact

2. **KV Cache Efficiency**
   - Cache hit rates
   - Prefix sharing effectiveness
   - Latency improvements from caching
   - Token reuse rates

3. **Concurrent Load Handling**
   - Performance under high concurrency (100+ connections)
   - Latency percentiles (P50, P90, P99)
   - Error rates and success rates
   - Load balancing effectiveness

4. **Memory Management**
   - Memory usage over time
   - Memory leak detection
   - Cache memory overhead
   - Per-request memory cost

### Key Features

- **Comprehensive Coverage:** Tests all critical performance aspects
- **Detailed Reporting:** Markdown reports with statistics and analysis
- **JSON Export:** Raw data for further analysis
- **Flexible Configuration:** Customizable test parameters
- **Quick Mode:** Fast tests for development
- **Continuous Monitoring:** Suitable for CI/CD integration

---

## Architecture

### Module Structure

```
benchmarks/
 __init__.py                   # Package initialization
 README.md                     # User guide
 BENCHMARK_GUIDE.md           # This file (detailed guide)
 requirements.txt              # Dependencies

 run_benchmarks.py            # Main runner (all benchmarks)

 benchmark_throughput.py      # Throughput tests
 benchmark_kv_cache.py        # KV cache tests
 benchmark_concurrent.py      # Concurrent connection tests
 benchmark_memory.py          # Memory usage tests

 benchmark_utils.py           # Shared utilities
```

### Data Flow

```

  run_benchmarks 
     (main)      

         
    
             
             
  
ThroughputCache  
  Test    Test  

             
             

  Benchmark      
   Utilities     
 (Reporting)     

         
         

  Markdown       
  Reports +      
  JSON Data      

```

### Design Principles

1. **Modularity:** Each benchmark is independent
2. **Reusability:** Shared utilities avoid duplication
3. **Simplicity:** Clear, readable code
4. **Extensibility:** Easy to add new benchmarks
5. **Reliability:** Robust error handling

---

## Installation

### Prerequisites

- Python 3.10+
- FakeAI server running (see main README)
- Network access to server

### Install Dependencies

#### Core Dependencies (Required)

```bash
cd /home/anthony/projects/fakeai/benchmarks
pip install -r requirements.txt
```

Or manually:

```bash
pip install httpx
```

#### Optional Dependencies

For memory benchmarks:

```bash
pip install psutil
```

For chart generation:

```bash
pip install matplotlib
```

### Verify Installation

```bash
python -c "import httpx; print('httpx:', httpx.__version__)"
python -c "import psutil; print('psutil:', psutil.__version__)"  # Optional
```

---

## Quick Start

### 1. Start FakeAI Server

In a separate terminal:

```bash
cd /home/anthony/projects/fakeai
python run_server.py
```

Wait for:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Run All Benchmarks

```bash
cd benchmarks
python run_benchmarks.py
```

Expected output:
```
======================================================================
FakeAI Performance Benchmark Suite
======================================================================

Server: http://localhost:8000
Models available: 15
Timestamp: 2025-10-04 18:50:00

======================================================================
1. THROUGHPUT BENCHMARKS
======================================================================
...
```

### 3. View Results

After completion, check:

```bash
ls -lh *.md
# throughput_results.md
# kv_cache_results.md
# concurrent_results.md
# memory_results.md
# BENCHMARK_SUMMARY.md
```

Open `BENCHMARK_SUMMARY.md` for overview.

---

## Benchmark Modules

### 1. Throughput Benchmark (`benchmark_throughput.py`)

**Purpose:** Measure requests per second and token generation rates.

**Tests Performed:**

| Test | Requests | Payload Size | Streaming |
|------|----------|--------------|-----------|
| Small - Non-streaming | 100 | 50 tokens | No |
| Small - Streaming | 100 | 50 tokens | Yes |
| Medium - Non-streaming | 50 | 200 tokens | No |
| Medium - Streaming | 50 | 200 tokens | Yes |
| Large - Non-streaming | 20 | 500 tokens | No |
| Large - Streaming | 20 | 500 tokens | Yes |
| High Concurrency | 200 | 50 tokens | No |

**Key Metrics:**

- **Requests per Second (RPS):** Total throughput
- **Tokens per Second:** Token generation rate
- **Average Latency:** Mean response time
- **P50/P90/P99 Latency:** Percentile latencies

**Run Individually:**

```bash
python benchmark_throughput.py
```

**Expected Results:**

- RPS: 50-200 depending on payload size
- P99 Latency: < 500ms for small payloads
- Streaming: Slightly higher latency, similar RPS

### 2. KV Cache Benchmark (`benchmark_kv_cache.py`)

**Purpose:** Test cache effectiveness and prefix sharing.

**Tests Performed:**

1. **Cache Hit Rate Test**
   - Multiple iterations with shared prefixes
   - Measures hit rate over time
   - Tests various prefix/suffix combinations

2. **Prefix Sharing Test**
   - Common system prompts
   - Various user queries
   - Measures reuse efficiency

3. **Smart Router Test**
   - Load distribution across workers
   - Cache-aware routing
   - Load balance scoring

**Key Metrics:**

- **Hit Rate (%):** Cache hits / total requests
- **Latency Improvement (%):** Speed gain from cache
- **Token Reuse Rate (%):** Cached tokens / total tokens
- **Average Prefix Length:** Matched tokens

**Run Individually:**

```bash
python benchmark_kv_cache.py
```

**Expected Results:**

- Hit Rate: > 60% after warmup
- Latency Improvement: 30-50%
- Token Reuse: > 40%

### 3. Concurrent Connections Benchmark (`benchmark_concurrent.py`)

**Purpose:** Test performance under high concurrent load.

**Tests Performed:**

| Test | Requests | Concurrent | Expected Outcome |
|------|----------|------------|------------------|
| 10 Concurrent | 100 | 10 | Baseline |
| 50 Concurrent | 200 | 50 | Moderate load |
| 100 Concurrent | 300 | 100 | High load |
| 200 Concurrent | 400 | 200 | Stress test |
| Sustained 10 RPS | 300 | 1 | Long duration |

**Key Metrics:**

- **Success Rate (%):** Successful requests / total
- **P50/P90/P95/P99 Latency:** Percentile distribution
- **Requests per Second:** Effective throughput
- **Error Rate (%):** Failed requests

**Run Individually:**

```bash
python benchmark_concurrent.py
```

**Expected Results:**

- Success Rate: 100% at reasonable concurrency
- P99 Latency: < 1000ms
- Handles 100+ concurrent connections

### 4. Memory Benchmark (`benchmark_memory.py`)

**Purpose:** Track memory usage and detect leaks.

**Requirements:** `psutil` package

**Tests Performed:**

1. **Low Load (5 RPS)** - 60 seconds
2. **Medium Load (20 RPS)** - 60 seconds
3. **Cache Overhead** - Fill cache test
4. **Long-Running (10 RPS)** - 120 seconds for leak detection

**Key Metrics:**

- **Initial/Final Memory (MB):** RSS memory
- **Peak Memory (MB):** Maximum usage
- **Memory Growth (MB):** Change over time
- **Leak Detected (Yes/No):** Statistical analysis
- **Growth Rate (MB/min):** Linear regression slope
- **Avg per Request (KB):** Memory cost per request

**Run Individually:**

```bash
python benchmark_memory.py
```

**Expected Results:**

- No leaks detected
- Growth: < 10 MB for test duration
- Per-request: < 10 KB

---

## Results and Interpretation

### Understanding Markdown Reports

Each benchmark generates a markdown report with:

1. **Summary Table:** Quick overview of all tests
2. **Detailed Results:** Per-test breakdowns
3. **Comparative Analysis:** Streaming vs non-streaming, etc.
4. **Performance Assessment:** Recommendations

### Example: Throughput Report

```markdown
# Throughput Benchmark Results

**Timestamp:** 2025-10-04 18:50:00

## Summary

| Test | Requests | RPS | Tokens/sec | Avg Latency | P90 | P99 |
|------|----------|-----|------------|-------------|-----|-----|
| Small - Non-streaming | 100 | 87.23 | 4361.5 | 114.67ms | 145.23ms | 178.45ms |
| Small - Streaming | 100 | 85.67 | 4283.5 | 116.75ms | 148.92ms | 182.11ms |
...
```

### Interpreting Metrics

#### Throughput

- **Good:** RPS > 50, P99 < 500ms
- **Acceptable:** RPS 20-50, P99 < 1000ms
- **Poor:** RPS < 20, P99 > 1000ms

#### KV Cache

- **Good:** Hit rate > 60%, improvement > 30%
- **Acceptable:** Hit rate 40-60%, improvement 20-30%
- **Poor:** Hit rate < 40%, improvement < 20%

#### Concurrent

- **Good:** 100% success at 100+ concurrent
- **Acceptable:** 95%+ success at 50+ concurrent
- **Poor:** < 95% success or < 50 concurrent

#### Memory

- **Good:** No leaks, < 10 MB growth
- **Acceptable:** < 1 MB/min growth
- **Poor:** Leaks detected, > 1 MB/min

### JSON Results

Raw data is saved to JSON files:

```json
{
  "test_name": "Small Payload - Non-Streaming",
  "total_requests": 100,
  "successful_requests": 100,
  "requests_per_second": 87.23,
  "avg_latency": 0.11467,
  "p99_latency": 0.17845,
  ...
}
```

Use for:
- Custom analysis
- Trend tracking
- Integration with monitoring tools

---

## Advanced Usage

### Custom Test Parameters

#### Modify Throughput Tests

Edit `benchmark_throughput.py`:

```python
# Custom payload
my_payload = {
    "model": "openai/gpt-oss-120b",
    "messages": [
        {"role": "system", "content": "You are an expert."},
        {"role": "user", "content": "Explain quantum computing."}
    ],
    "max_tokens": 1000,
    "temperature": 0.8,
}

# Run custom test
await benchmark.run_benchmark(
    "Custom Quantum Test",
    num_requests=50,
    payload=my_payload,
    payload_size="large",
    streaming=True,
    concurrent_limit=10,
)
```

#### Modify Concurrency Levels

Edit `benchmark_concurrent.py`:

```python
# Test specific concurrency levels
concurrency_levels = [5, 10, 25, 50, 75, 100, 150, 200, 300]

for level in concurrency_levels:
    await benchmark.run_concurrent_test(
        test_name=f"{level} Concurrent",
        num_requests=level * 3,
        concurrent_connections=level,
        payload=payload,
    )
```

#### Extend Memory Tests

Edit `benchmark_memory.py`:

```python
# Longer duration test
await benchmark.run_memory_test(
    test_name="Extended Leak Detection",
    duration_seconds=600,  # 10 minutes
    requests_per_second=20,
    payload=payload,
    snapshot_interval=30.0,
)
```

### Integration with CI/CD

#### GitHub Actions Example

```yaml
name: Performance Benchmarks

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  benchmark:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -e .
        cd benchmarks
        pip install -r requirements.txt

    - name: Start FakeAI Server
      run: |
        python run_server.py &
        sleep 5

    - name: Run benchmarks
      run: |
        cd benchmarks
        python run_benchmarks.py --quick

    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: benchmark-results
        path: benchmarks/*.md
```

### Continuous Monitoring

#### Automated Runs

```bash
#!/bin/bash
# benchmark_monitor.sh

while true; do
    echo "Starting benchmark run at $(date)"

    cd /home/anthony/projects/fakeai/benchmarks
    python run_benchmarks.py --quick

    # Archive results
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    mkdir -p archive/$TIMESTAMP
    cp *.md archive/$TIMESTAMP/

    # Wait 1 hour
    sleep 3600
done
```

#### Result Tracking

```python
# track_performance.py
import json
import glob
from datetime import datetime

results = []

for file in sorted(glob.glob("throughput_results_*.json")):
    with open(file) as f:
        data = json.load(f)
        timestamp = file.split("_")[-1].replace(".json", "")
        results.append({
            "timestamp": timestamp,
            "avg_rps": sum(r["requests_per_second"] for r in data) / len(data),
        })

# Plot trend
import matplotlib.pyplot as plt

timestamps = [r["timestamp"] for r in results]
rps = [r["avg_rps"] for r in results]

plt.plot(timestamps, rps)
plt.xlabel("Time")
plt.ylabel("Average RPS")
plt.title("FakeAI Performance Trend")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("performance_trend.png")
```

---

## Best Practices

### Before Running Benchmarks

1. **Close unnecessary applications** to free resources
2. **Disable CPU throttling** for consistent results
3. **Ensure stable network** if testing remote server
4. **Check disk space** for result files
5. **Review server logs** for any existing issues

### During Benchmarks

1. **Don't interrupt** - Let tests complete
2. **Monitor resources** - Check CPU/memory in separate terminal
3. **Watch for errors** - Check console output
4. **Avoid other load** - Don't run other heavy processes

### After Benchmarks

1. **Review all reports** - Check each markdown file
2. **Compare with baseline** - Track performance over time
3. **Investigate anomalies** - Look into unexpected results
4. **Archive results** - Keep historical data
5. **Share findings** - Document insights

### Optimization Tips

#### Server Configuration

```bash
# Optimal for benchmarking
export FAKEAI_RESPONSE_DELAY=0.1
export FAKEAI_RANDOM_DELAY=true
export FAKEAI_ENABLE_PROMPT_CACHING=true
export FAKEAI_CACHE_TTL_SECONDS=600

fakeai-server --host 0.0.0.0 --port 8000
```

#### System Tuning

```bash
# Increase file descriptor limits
ulimit -n 65536

# Disable swap for consistent memory behavior
sudo swapoff -a  # Re-enable after: sudo swapon -a

# Set CPU governor to performance
sudo cpupower frequency-set -g performance
```

#### Network Tuning

```bash
# Increase TCP buffer sizes
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.wmem_max=134217728
sudo sysctl -w net.ipv4.tcp_rmem="4096 87380 67108864"
sudo sysctl -w net.ipv4.tcp_wmem="4096 65536 67108864"
```

### Common Pitfalls

1. **Running on loaded system** - Results unreliable
2. **Not warming up** - First requests slower
3. **Wrong server URL** - Check host/port
4. **Missing dependencies** - Install all requirements
5. **Insufficient duration** - Memory tests need time
6. **Too high concurrency** - Start low, increase gradually

---

## Troubleshooting

### Server Connection Issues

**Problem:** `Server is not reachable`

**Solutions:**
```bash
# Check if server is running
ps aux | grep fakeai

# Check if port is open
netstat -tuln | grep 8000

# Try manual connection
curl http://localhost:8000/health

# Check firewall
sudo ufw status
```

### Memory Benchmark Fails

**Problem:** `psutil not available`

**Solution:**
```bash
pip install psutil

# Or skip memory tests
python run_benchmarks.py --skip-memory
```

### High Latencies

**Problem:** P99 > 1000ms consistently

**Possible Causes:**
- Server overloaded
- High response_delay config
- System resource constraints
- Network issues

**Solutions:**
```bash
# Reduce server delay
export FAKEAI_RESPONSE_DELAY=0.1

# Check system resources
top
free -h
df -h

# Reduce concurrency
# Edit benchmark files to lower concurrent_limit
```

### Memory Leaks Detected

**Problem:** Leak detection reports positive

**Investigation:**
```bash
# Check if server process memory growing
watch -n 1 'ps aux | grep fakeai'

# Review server logs
tail -f /path/to/fakeai.log

# Run isolated memory test
python benchmark_memory.py
```

### JSON Import Errors

**Problem:** Cannot load results JSON

**Solution:**
```python
# Validate JSON
import json

with open("throughput_results.json") as f:
    try:
        data = json.load(f)
        print("Valid JSON")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
```

---

## Appendix

### File Descriptions

| File | Purpose | Output |
|------|---------|--------|
| `run_benchmarks.py` | Main runner | All reports |
| `benchmark_throughput.py` | RPS testing | `throughput_results.md` |
| `benchmark_kv_cache.py` | Cache testing | `kv_cache_results.md` |
| `benchmark_concurrent.py` | Concurrency testing | `concurrent_results.md` |
| `benchmark_memory.py` | Memory testing | `memory_results.md` |
| `benchmark_utils.py` | Shared utilities | N/A |

### Metric Glossary

- **RPS:** Requests per second
- **TPS:** Tokens per second
- **P50/P90/P99:** 50th/90th/99th percentile latencies
- **TTFT:** Time to first token
- **ITL:** Inter-token latency
- **RSS:** Resident Set Size (actual physical memory)
- **VMS:** Virtual Memory Size
- **Hit Rate:** Cache hits / total requests
- **Reuse Rate:** Cached tokens / total tokens

### Performance Targets

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| RPS (small) | > 100 | 50-100 | < 50 |
| P99 Latency | < 300ms | 300-500ms | > 500ms |
| Cache Hit Rate | > 70% | 50-70% | < 50% |
| Success Rate | 100% | > 95% | < 95% |
| Memory Growth | 0 MB | < 10 MB | > 10 MB |

---

**End of FakeAI Benchmark Guide**

For questions or issues, refer to the main FakeAI documentation or open an issue on GitHub.

**Version:** 0.0.4
**Last Updated:** 2025-10-04
