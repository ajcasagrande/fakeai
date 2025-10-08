/**
 * Benchmark Dashboard Types
 *
 * Type definitions for AIPerf benchmark data
 */

export interface BenchmarkMetric {
  tag: string;
  unit: string;
  header: string;
  avg: number;
  min: number | null;
  max: number | null;
  p1: number | null;
  p5: number | null;
  p25: number | null;
  p50: number | null;
  p75: number | null;
  p90: number | null;
  p95: number | null;
  p99: number | null;
  std: number | null;
  count: number;
}

export interface BenchmarkRecords {
  input_sequence_length: BenchmarkMetric;
  ttft: BenchmarkMetric;
  request_count: BenchmarkMetric;
  request_latency: BenchmarkMetric;
  min_request_timestamp: BenchmarkMetric;
  output_token_count: BenchmarkMetric;
  ttst: BenchmarkMetric;
  inter_chunk_latency: BenchmarkMetric;
  output_sequence_length: BenchmarkMetric;
  max_response_timestamp: BenchmarkMetric;
  inter_token_latency: BenchmarkMetric;
  output_token_throughput_per_user: BenchmarkMetric;
  total_isl: BenchmarkMetric;
  benchmark_duration: BenchmarkMetric;
  total_output_tokens: BenchmarkMetric;
  total_osl: BenchmarkMetric;
  request_throughput: BenchmarkMetric;
  output_token_throughput: BenchmarkMetric;
}

export interface EndpointConfig {
  model_names: string[];
  type: string;
  streaming: boolean;
  url: string;
}

export interface LoadgenConfig {
  concurrency: number;
  request_rate_mode: string;
  request_count: number;
}

export interface InputConfig {
  endpoint: EndpointConfig;
  loadgen: LoadgenConfig;
  cli_command: string;
}

export interface BenchmarkData {
  records: BenchmarkRecords;
  input_config: InputConfig;
  was_cancelled: boolean;
  error_summary: string[];
  start_time: string;
  end_time: string;
}

export interface BenchmarkFile {
  name: string;
  path: string;
  concurrency: number;
  model: string;
}
