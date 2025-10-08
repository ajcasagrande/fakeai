/**
 * Benchmark Data API
 *
 * Functions for fetching benchmark data from the artifacts directory
 */

import { BenchmarkData, BenchmarkFile } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9002';

/**
 * List all available benchmark runs
 */
export async function fetchBenchmarkList(): Promise<BenchmarkFile[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/benchmarks/list`);
    if (!response.ok) {
      throw new Error(`Failed to fetch benchmark list: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching benchmark list:', error);
    throw error;
  }
}

/**
 * Fetch a specific benchmark result
 */
export async function fetchBenchmarkData(benchmarkPath: string): Promise<BenchmarkData> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/benchmarks/data?path=${encodeURIComponent(benchmarkPath)}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch benchmark data: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching benchmark data:', error);
    throw error;
  }
}

/**
 * Fetch the latest benchmark result
 */
export async function fetchLatestBenchmark(): Promise<BenchmarkData> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/benchmarks/latest`);
    if (!response.ok) {
      throw new Error(`Failed to fetch latest benchmark: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching latest benchmark:', error);
    throw error;
  }
}
