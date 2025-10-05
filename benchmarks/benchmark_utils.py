#!/usr/bin/env python3
"""
Benchmark Utilities for FakeAI Server

Common utilities for benchmarking, reporting, and visualization.
"""
#  SPDX-License-Identifier: Apache-2.0

import json
import time
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any

import httpx


@dataclass
class ServerInfo:
    """Information about the FakeAI server being benchmarked."""

    base_url: str
    version: str | None
    models: list[str]
    timestamp: str
    reachable: bool


class BenchmarkReporter:
    """Generate comprehensive benchmark reports with optional charts."""

    def __init__(self, output_dir: str = "/home/anthony/projects/fakeai/benchmarks"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_results(self, results: Any, filename: str):
        """
        Save benchmark results to JSON file.

        Args:
            results: Results object (dataclass or dict)
            filename: Output filename
        """
        output_path = self.output_dir / filename

        # Convert dataclass to dict if needed
        if is_dataclass(results):
            data = self._dataclass_to_dict(results)
        elif isinstance(results, list) and all(is_dataclass(r) for r in results):
            data = [self._dataclass_to_dict(r) for r in results]
        else:
            data = results

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        print(f"Results saved to: {output_path}")

    def _dataclass_to_dict(self, obj: Any) -> dict[str, Any]:
        """Convert dataclass to dictionary recursively."""
        if is_dataclass(obj):
            result = {}
            for key, value in asdict(obj).items():
                if is_dataclass(value):
                    result[key] = self._dataclass_to_dict(value)
                elif isinstance(value, list):
                    result[key] = [
                        self._dataclass_to_dict(item) if is_dataclass(item) else item
                        for item in value
                    ]
                else:
                    result[key] = value
            return result
        return obj

    def generate_html_report(self, markdown_content: str, title: str) -> str:
        """
        Convert markdown report to HTML with styling.

        Args:
            markdown_content: Markdown content
            title: HTML page title

        Returns:
            HTML string
        """
        # Simple markdown-like HTML conversion
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 8px;
            margin-top: 30px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 20px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        code {{
            background-color: #f5f5f5;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-style: italic;
        }}
        .metric {{
            font-weight: bold;
            color: #27ae60;
        }}
        .warning {{
            color: #e74c3c;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="content">
        {self._markdown_to_html_simple(markdown_content)}
    </div>
</body>
</html>
"""
        return html

    def _markdown_to_html_simple(self, markdown: str) -> str:
        """Simple markdown to HTML converter."""
        html = markdown

        # Convert headers
        html = html.replace("# ", "<h1>").replace("\n\n", "</h1>\n\n")
        html = html.replace("## ", "<h2>").replace("\n\n", "</h2>\n\n")
        html = html.replace("### ", "<h3>").replace("\n\n", "</h3>\n\n")

        # Convert bold
        while "**" in html:
            html = html.replace("**", "<strong>", 1)
            html = html.replace("**", "</strong>", 1)

        # Convert italic
        while "*" in html and not html.count("*") % 2:
            html = html.replace("*", "<em>", 1)
            html = html.replace("*", "</em>", 1)

        # Convert lists
        lines = html.split("\n")
        in_list = False
        result = []

        for line in lines:
            if line.strip().startswith("- "):
                if not in_list:
                    result.append("<ul>")
                    in_list = True
                result.append(f"<li>{line.strip()[2:]}</li>")
            else:
                if in_list:
                    result.append("</ul>")
                    in_list = False
                result.append(line)

        if in_list:
            result.append("</ul>")

        html = "\n".join(result)

        # Wrap paragraphs
        html = html.replace("\n\n", "</p>\n<p>")
        html = "<p>" + html + "</p>"

        return html

    def create_comparison_report(
        self,
        results_files: list[str],
        output_filename: str = "comparison_report.md",
    ) -> str:
        """
        Create a comparison report from multiple benchmark runs.

        Args:
            results_files: List of JSON result files
            output_filename: Output markdown filename

        Returns:
            Markdown content
        """
        report = "# Benchmark Comparison Report\n\n"
        report += f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        all_results = []
        for filename in results_files:
            filepath = self.output_dir / filename
            if filepath.exists():
                with open(filepath, "r") as f:
                    data = json.load(f)
                    all_results.append({"filename": filename, "data": data})

        if not all_results:
            report += "No results files found for comparison.\n"
            return report

        report += f"## Comparing {len(all_results)} Benchmark Runs\n\n"

        # Add comparison tables based on result type
        report += "### Results\n\n"
        report += "| File | Timestamp | Key Metrics |\n"
        report += "|------|-----------|-------------|\n"

        for result in all_results:
            filename = result["filename"]
            data = result["data"]

            # Extract key metrics (this is generic and could be improved)
            if isinstance(data, dict):
                metrics = ", ".join(f"{k}: {v}" for k, v in list(data.items())[:3])
            else:
                metrics = f"{len(data)} results"

            report += f"| {filename} | - | {metrics} |\n"

        # Save report
        output_path = self.output_dir / output_filename
        with open(output_path, "w") as f:
            f.write(report)

        print(f"Comparison report saved to: {output_path}")
        return report


async def check_server(base_url: str, api_key: str = "test") -> ServerInfo:
    """
    Check if FakeAI server is reachable and get info.

    Args:
        base_url: Server base URL
        api_key: API key for authentication

    Returns:
        ServerInfo object
    """
    print(f"Checking server at {base_url}...")

    try:
        async with httpx.AsyncClient() as client:
            # Try health endpoint
            response = await client.get(f"{base_url}/health", timeout=10.0)
            response.raise_for_status()

            # Try models endpoint
            response = await client.get(
                f"{base_url}/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10.0,
            )
            response.raise_for_status()
            models_data = response.json()
            models = [model["id"] for model in models_data.get("data", [])]

            return ServerInfo(
                base_url=base_url,
                version=None,  # FakeAI doesn't expose version yet
                models=models,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                reachable=True,
            )

    except Exception as e:
        print(f"Server check failed: {e}")
        return ServerInfo(
            base_url=base_url,
            version=None,
            models=[],
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            reachable=False,
        )


def percentile(data: list[float], p: float) -> float:
    """
    Calculate percentile of a sorted list.

    Args:
        data: Sorted list of values
        p: Percentile (0.0 to 1.0)

    Returns:
        Percentile value
    """
    if not data:
        return 0.0

    k = (len(data) - 1) * p
    f = int(k)
    c = k - f

    if f + 1 < len(data):
        return data[f] + (data[f + 1] - data[f]) * c
    return data[f]


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1h 23m 45s")
    """
    if seconds < 60:
        return f"{seconds:.2f}s"

    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60

    if minutes < 60:
        return f"{minutes}m {remaining_seconds:.0f}s"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    return f"{hours}h {remaining_minutes}m {remaining_seconds:.0f}s"


def format_bytes(bytes_count: int) -> str:
    """
    Format bytes in human-readable format.

    Args:
        bytes_count: Number of bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_count < 1024.0:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.2f} PB"


class ProgressTracker:
    """Track and display benchmark progress."""

    def __init__(self, total: int, description: str = "Progress"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.perf_counter()

    def update(self, increment: int = 1):
        """Update progress."""
        self.current += increment
        self._print_progress()

    def _print_progress(self):
        """Print progress bar."""
        if self.total == 0:
            return

        percent = (self.current / self.total) * 100
        elapsed = time.perf_counter() - self.start_time
        rate = self.current / elapsed if elapsed > 0 else 0

        bar_length = 40
        filled = int(bar_length * self.current / self.total)
        bar = "=" * filled + "-" * (bar_length - filled)

        print(
            f"\r{self.description}: [{bar}] {percent:.1f}% ({self.current}/{self.total}) "
            f"@ {rate:.2f}/s",
            end="",
            flush=True,
        )

        if self.current >= self.total:
            print()  # New line when complete

    def finish(self):
        """Mark as complete."""
        self.current = self.total
        self._print_progress()


# Optional: Chart generation with matplotlib
def try_import_matplotlib():
    """Try to import matplotlib."""
    try:
        import matplotlib
        import matplotlib.pyplot as plt

        matplotlib.use("Agg")  # Non-interactive backend
        return plt
    except ImportError:
        return None


def generate_latency_chart(
    latencies: list[float],
    title: str,
    output_path: str,
) -> bool:
    """
    Generate latency distribution chart.

    Args:
        latencies: List of latency values in seconds
        title: Chart title
        output_path: Output file path

    Returns:
        True if chart was generated, False if matplotlib not available
    """
    plt = try_import_matplotlib()
    if not plt:
        return False

    try:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Histogram
        ax1.hist([l * 1000 for l in latencies], bins=50, edgecolor="black")
        ax1.set_xlabel("Latency (ms)")
        ax1.set_ylabel("Frequency")
        ax1.set_title(f"{title} - Distribution")
        ax1.grid(True, alpha=0.3)

        # Box plot
        ax2.boxplot([l * 1000 for l in latencies], vert=True)
        ax2.set_ylabel("Latency (ms)")
        ax2.set_title(f"{title} - Box Plot")
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        print(f"Chart saved to: {output_path}")
        return True

    except Exception as e:
        print(f"Failed to generate chart: {e}")
        return False


def generate_memory_chart(
    snapshots: list[tuple[float, float]],
    title: str,
    output_path: str,
) -> bool:
    """
    Generate memory usage over time chart.

    Args:
        snapshots: List of (timestamp, memory_mb) tuples
        title: Chart title
        output_path: Output file path

    Returns:
        True if chart was generated, False if matplotlib not available
    """
    plt = try_import_matplotlib()
    if not plt:
        return False

    try:
        times = [s[0] for s in snapshots]
        memories = [s[1] for s in snapshots]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(times, memories, marker="o", linewidth=2, markersize=4)
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Memory (MB)")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        print(f"Chart saved to: {output_path}")
        return True

    except Exception as e:
        print(f"Failed to generate chart: {e}")
        return False
