#!/usr/bin/env python3
"""
Automated AIPerf Benchmark Runner for FakeAI

This script runs comprehensive benchmarks using aiperf with multiple models,
concurrency levels, and configurations.

Usage:
    python run_aiperf_benchmarks.py                          # Full benchmark suite
    python run_aiperf_benchmarks.py --quick                  # Quick test
    python run_aiperf_benchmarks.py --url http://localhost:8000  # Custom URL
    python run_aiperf_benchmarks.py --models openai/gpt-oss-120b  # Specific model
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class BenchmarkConfig:
    """Configuration for a single benchmark run."""

    def __init__(
        self,
        model: str,
        concurrency: int,
        request_count: int,
        streaming: bool = True,
        synthetic_tokens: int = 300,
        output_tokens: int = 1000,
        endpoint_type: str = "chat",
    ):
        self.model = model
        self.concurrency = concurrency
        self.request_count = request_count
        self.streaming = streaming
        self.synthetic_tokens = synthetic_tokens
        self.output_tokens = output_tokens
        self.endpoint_type = endpoint_type

    @property
    def name(self) -> str:
        """Generate a descriptive name for this benchmark."""
        model_short = self.model.split("/")[-1]
        streaming_str = "streaming" if self.streaming else "non-streaming"
        return f"{model_short}-{self.endpoint_type}-concurrency{self.concurrency}-{streaming_str}"

    def to_command(self, url: str, artifact_dir: str) -> list[str]:
        """Generate aiperf command for this configuration."""
        cmd = [
            "aiperf",
            "profile",
            "--model",
            self.model,
            "--url",
            url,
            "--endpoint-type",
            self.endpoint_type,
            "--service-kind",
            "openai",
            "--concurrency",
            str(self.concurrency),
            "--request-count",
            str(self.request_count),
            "--synthetic-tokens-mean",
            str(self.synthetic_tokens),
            "--output-tokens-mean",
            str(self.output_tokens),
            "--artifact-directory",
            artifact_dir,
        ]

        if self.streaming:
            cmd.append("--streaming")

        return cmd


class BenchmarkRunner:
    """Automated benchmark runner for AIPerf."""

    def __init__(
        self,
        url: str = "http://localhost:9001",
        artifact_base_dir: str = "artifacts",
        verbose: bool = True,
    ):
        self.url = url
        self.artifact_base_dir = Path(artifact_base_dir)
        self.verbose = verbose
        self.results: list[dict[str, Any]] = []

        # Create base artifact directory
        self.artifact_base_dir.mkdir(exist_ok=True)

    def run_benchmark(self, config: BenchmarkConfig) -> dict[str, Any]:
        """Run a single benchmark configuration."""
        print(f"\n{'=' * 80}")
        print(f"Running: {config.name}")
        print(f"{'=' * 80}")

        # Create artifact directory for this benchmark
        artifact_dir = self.artifact_base_dir / config.name
        artifact_dir.mkdir(exist_ok=True)

        # Generate command
        cmd = config.to_command(self.url, str(artifact_dir))

        if self.verbose:
            print(f"Command: {' '.join(cmd)}")

        # Run benchmark
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            elapsed_time = time.time() - start_time

            if result.returncode != 0:
                print(f"❌ FAILED (exit code {result.returncode})")
                print(f"STDERR: {result.stderr}")
                return {
                    "name": config.name,
                    "config": vars(config),
                    "success": False,
                    "error": result.stderr,
                    "elapsed_time": elapsed_time,
                }

            # Parse results
            export_file = artifact_dir / "profile_export_genai_perf.json"
            if export_file.exists():
                with open(export_file) as f:
                    metrics = json.load(f)

                # Extract key metrics
                summary = {
                    "name": config.name,
                    "config": vars(config),
                    "success": True,
                    "elapsed_time": elapsed_time,
                    "metrics": {
                        "request_throughput": metrics.get("request_throughput", {}).get(
                            "avg", 0
                        ),
                        "request_latency_avg": metrics.get("request_latency", {}).get(
                            "avg", 0
                        ),
                        "request_latency_p99": metrics.get("request_latency", {}).get(
                            "p99", 0
                        ),
                        "ttft_avg": metrics.get("time_to_first_token", {}).get(
                            "avg", 0
                        ),
                        "ttft_p99": metrics.get("time_to_first_token", {}).get(
                            "p99", 0
                        ),
                        "output_token_throughput": metrics.get(
                            "output_token_throughput", {}
                        ).get("avg", 0),
                        "input_tokens_avg": metrics.get(
                            "input_sequence_length", {}
                        ).get("avg", 0),
                        "output_tokens_avg": metrics.get(
                            "output_sequence_length", {}
                        ).get("avg", 0),
                    },
                    "full_metrics_path": str(export_file),
                }

                print(f"✅ SUCCESS")
                print(
                    f"   Request Throughput: {summary['metrics']['request_throughput']:.2f} req/s"
                )
                print(
                    f"   Output Token Throughput: {summary['metrics']['output_token_throughput']:.2f} tokens/s"
                )
                print(
                    f"   Avg Latency: {summary['metrics']['request_latency_avg']:.2f} ms"
                )
                print(
                    f"   P99 Latency: {summary['metrics']['request_latency_p99']:.2f} ms"
                )
                print(f"   TTFT (avg): {summary['metrics']['ttft_avg']:.2f} ms")
                print(f"   Elapsed Time: {elapsed_time:.2f}s")

                return summary
            else:
                print(f"❌ FAILED - No results file found")
                return {
                    "name": config.name,
                    "config": vars(config),
                    "success": False,
                    "error": "No results file generated",
                    "elapsed_time": elapsed_time,
                }

        except subprocess.TimeoutExpired:
            print(f"❌ TIMEOUT after 10 minutes")
            return {
                "name": config.name,
                "config": vars(config),
                "success": False,
                "error": "Timeout after 600 seconds",
                "elapsed_time": 600,
            }
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"❌ ERROR: {e}")
            return {
                "name": config.name,
                "config": vars(config),
                "success": False,
                "error": str(e),
                "elapsed_time": elapsed_time,
            }

    def run_all(self, configs: list[BenchmarkConfig]) -> None:
        """Run all benchmark configurations."""
        print(f"\n{'#' * 80}")
        print(f"# AIPerf Benchmark Suite - FakeAI")
        print(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"# Server URL: {self.url}")
        print(f"# Total Benchmarks: {len(configs)}")
        print(f"{'#' * 80}\n")

        for i, config in enumerate(configs, 1):
            print(f"\n[{i}/{len(configs)}] Starting benchmark: {config.name}")
            result = self.run_benchmark(config)
            self.results.append(result)

        # Generate summary report
        self.generate_summary()

    def generate_summary(self) -> None:
        """Generate summary report of all benchmarks."""
        print(f"\n{'#' * 80}")
        print(f"# Benchmark Summary")
        print(f"{'#' * 80}\n")

        successful = [r for r in self.results if r["success"]]
        failed = [r for r in self.results if not r["success"]]

        print(f"Total Benchmarks: {len(self.results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")

        if successful:
            print(f"\n## Successful Benchmarks\n")
            print(
                f"{'Name':<60} {'Throughput':>15} {'P99 Latency':>15} {'TTFT P99':>15}"
            )
            print(f"{'-' * 60} {'-' * 15} {'-' * 15} {'-' * 15}")
            for result in successful:
                metrics = result.get("metrics", {})
                print(
                    f"{result['name']:<60} "
                    f"{metrics.get('request_throughput', 0):>12.2f} rps "
                    f"{metrics.get('request_latency_p99', 0):>12.2f} ms "
                    f"{metrics.get('ttft_p99', 0):>12.2f} ms"
                )

        if failed:
            print(f"\n## Failed Benchmarks\n")
            for result in failed:
                print(f"  - {result['name']}: {result.get('error', 'Unknown error')}")

        # Save JSON summary
        summary_file = self.artifact_base_dir / "benchmark_summary.json"
        with open(summary_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "server_url": self.url,
                    "total": len(self.results),
                    "successful": len(successful),
                    "failed": len(failed),
                    "results": self.results,
                },
                f,
                indent=2,
            )

        print(f"\n✅ Summary saved to: {summary_file}")

        # Generate markdown report
        self.generate_markdown_report()

    def generate_markdown_report(self) -> None:
        """Generate markdown report."""
        report_file = self.artifact_base_dir / "BENCHMARK_REPORT.md"

        with open(report_file, "w") as f:
            f.write("# FakeAI AIPerf Benchmark Report\n\n")
            f.write(
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            f.write(f"**Server URL:** {self.url}\n\n")
            f.write(f"**Total Benchmarks:** {len(self.results)}\n\n")

            successful = [r for r in self.results if r["success"]]
            failed = [r for r in self.results if not r["success"]]

            f.write("## Summary\n\n")
            f.write(f"- **Successful:** {len(successful)}\n")
            f.write(f"- **Failed:** {len(failed)}\n\n")

            if successful:
                f.write("## Results\n\n")
                f.write(
                    "| Benchmark | Throughput (rps) | Token Throughput (t/s) | Avg Latency (ms) | P99 Latency (ms) | TTFT Avg (ms) | TTFT P99 (ms) |\n"
                )
                f.write(
                    "|-----------|------------------|------------------------|------------------|------------------|---------------|---------------|\n"
                )

                for result in successful:
                    metrics = result.get("metrics", {})
                    f.write(
                        f"| {result['name']} | "
                        f"{metrics.get('request_throughput', 0):.2f} | "
                        f"{metrics.get('output_token_throughput', 0):.2f} | "
                        f"{metrics.get('request_latency_avg', 0):.2f} | "
                        f"{metrics.get('request_latency_p99', 0):.2f} | "
                        f"{metrics.get('ttft_avg', 0):.2f} | "
                        f"{metrics.get('ttft_p99', 0):.2f} |\n"
                    )

            if failed:
                f.write("\n## Failed Benchmarks\n\n")
                for result in failed:
                    f.write(
                        f"- **{result['name']}**: {result.get('error', 'Unknown error')}\n"
                    )

            f.write("\n## Configuration Details\n\n")
            for result in self.results:
                f.write(f"### {result['name']}\n\n")
                f.write("```json\n")
                f.write(json.dumps(result.get("config", {}), indent=2))
                f.write("\n```\n\n")

        print(f"📝 Markdown report saved to: {report_file}")


def get_full_configs(models: list[str]) -> list[BenchmarkConfig]:
    """Get full benchmark configurations."""
    configs = []

    concurrency_levels = [10, 50, 100, 250, 500]

    for model in models:
        for concurrency in concurrency_levels:
            # Streaming test
            configs.append(
                BenchmarkConfig(
                    model=model,
                    concurrency=concurrency,
                    request_count=min(1000, concurrency * 10),
                    streaming=True,
                    synthetic_tokens=300,
                    output_tokens=1000,
                )
            )

        # Add one non-streaming test at concurrency 50
        configs.append(
            BenchmarkConfig(
                model=model,
                concurrency=50,
                request_count=500,
                streaming=False,
                synthetic_tokens=300,
                output_tokens=1000,
            )
        )

    return configs


def get_quick_configs(models: list[str]) -> list[BenchmarkConfig]:
    """Get quick test configurations."""
    configs = []

    for model in models:
        # Quick streaming test
        configs.append(
            BenchmarkConfig(
                model=model,
                concurrency=50,
                request_count=100,
                streaming=True,
                synthetic_tokens=128,
                output_tokens=100,
            )
        )

    return configs


def main():
    parser = argparse.ArgumentParser(
        description="Automated AIPerf benchmark runner for FakeAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--url",
        default="http://localhost:9001",
        help="FakeAI server URL (default: http://localhost:9001)",
    )

    parser.add_argument(
        "--models",
        nargs="+",
        default=[
            "openai/gpt-oss-120b",
            "meta-llama/Llama-3.1-8B-Instruct",
            "deepseek-ai/DeepSeek-R1",
        ],
        help="Models to benchmark (default: gpt-oss-120b, Llama-3.1-8B, DeepSeek-R1)",
    )

    parser.add_argument(
        "--concurrency",
        nargs="+",
        type=int,
        help="Custom concurrency levels (overrides defaults)",
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick tests only (1 config per model)",
    )

    parser.add_argument(
        "--artifact-dir",
        default="artifacts",
        help="Base directory for artifacts (default: artifacts)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Verbose output (default: True)",
    )

    args = parser.parse_args()

    # Validate aiperf is installed
    try:
        subprocess.run(
            ["aiperf", "--version"],
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ERROR: aiperf is not installed")
        print("Install with: pip install aiperf")
        sys.exit(1)

    # Create runner
    runner = BenchmarkRunner(
        url=args.url,
        artifact_base_dir=args.artifact_dir,
        verbose=args.verbose,
    )

    # Generate configurations
    if args.quick:
        configs = get_quick_configs(args.models)
    elif args.concurrency:
        # Custom concurrency levels
        configs = []
        for model in args.models:
            for concurrency in args.concurrency:
                configs.append(
                    BenchmarkConfig(
                        model=model,
                        concurrency=concurrency,
                        request_count=min(1000, concurrency * 10),
                        streaming=True,
                    )
                )
    else:
        configs = get_full_configs(args.models)

    # Run benchmarks
    runner.run_all(configs)


if __name__ == "__main__":
    main()
