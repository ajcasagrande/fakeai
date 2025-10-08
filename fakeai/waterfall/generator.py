"""
Waterfall Chart Generator.

Generates beautiful HTML/SVG waterfall charts from request timing data.
"""

#  SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Any

from .collector import RequestTiming


@dataclass
class WaterfallData:
    """Processed data for waterfall visualization."""

    requests: list[RequestTiming]
    earliest_time: float
    latest_time: float
    total_duration_ms: float
    max_concurrent: int


class WaterfallChartGenerator:
    """
    Generates waterfall charts from request timing data.

    Creates interactive HTML/SVG visualizations showing:
    - Request timeline (horizontal bars)
    - TTFT markers (vertical lines)
    - Token generation progress
    - Concurrent request overlap
    - Color-coded by status/performance
    """

    def __init__(self):
        """Initialize the chart generator."""
        self.colors = {
            "waiting": "#FFA500",  # Orange - waiting for TTFT
            "generating": "#4CAF50",  # Green - token generation
            "complete": "#2196F3",  # Blue - completed
            "error": "#F44336",  # Red - errors
            "ttft_marker": "#FF5722",  # Deep orange - TTFT line
        }

    def prepare_data(self, requests: list[RequestTiming]) -> WaterfallData:
        """Prepare request data for visualization."""
        if not requests:
            return WaterfallData(
                requests=[],
                earliest_time=0,
                latest_time=0,
                total_duration_ms=0,
                max_concurrent=0,
            )

        # Find time bounds
        earliest = min(r.start_time for r in requests)
        latest = max(
            r.end_time if r.end_time else r.start_time for r in requests
        )

        # Calculate max concurrent requests
        time_points = []
        for req in requests:
            time_points.append((req.start_time, 1))  # Start
            if req.end_time:
                time_points.append((req.end_time, -1))  # End

        time_points.sort()
        max_concurrent = 0
        current_concurrent = 0
        for _, delta in time_points:
            current_concurrent += delta
            max_concurrent = max(max_concurrent, current_concurrent)

        return WaterfallData(
            requests=requests,
            earliest_time=earliest,
            latest_time=latest,
            total_duration_ms=(latest - earliest) * 1000,
            max_concurrent=max_concurrent,
        )

    def generate_svg(
        self, data: WaterfallData, width: int = 1200, height: int = 600
    ) -> str:
        """Generate SVG waterfall chart."""
        if not data.requests:
            return self._generate_empty_chart(width, height)

        # Calculate dimensions
        margin = {"top": 40, "right": 20, "bottom": 60, "left": 150}
        chart_width = width - margin["left"] - margin["right"]
        chart_height = height - margin["top"] - margin["bottom"]
        row_height = min(30, chart_height / len(data.requests))

        # Time scale (ms to pixels)
        time_scale = chart_width / data.total_duration_ms if data.total_duration_ms > 0 else 1

        svg_parts = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            '<style>',
            '  .request-bar { stroke: #333; stroke-width: 1; }',
            '  .ttft-line { stroke-width: 2; stroke-dasharray: 4,4; }',
            '  .label { font-family: monospace; font-size: 11px; fill: #333; }',
            '  .axis-label { font-family: sans-serif; font-size: 12px; fill: #666; }',
            '  .tooltip { font-family: monospace; font-size: 10px; }',
            '</style>',
            f'<g transform="translate({margin["left"]}, {margin["top"]})">',
        ]

        # Draw each request
        for i, req in enumerate(data.requests):
            y = i * row_height
            start_offset_ms = (req.start_time - data.earliest_time) * 1000
            x_start = start_offset_ms * time_scale

            # Draw request bar
            if req.is_complete:
                bar_width = req.duration_ms * time_scale
                color = self.colors["complete"]
            else:
                # Ongoing request
                bar_width = ((time.time() - req.start_time) * 1000) * time_scale
                color = self.colors["generating"]

            # Request background bar
            svg_parts.append(
                f'<rect class="request-bar" x="{x_start:.2f}" y="{y}" '
                f'width="{bar_width:.2f}" height="{row_height - 2}" '
                f'fill="{color}" opacity="0.6" rx="2"/>'
            )

            # Draw TTFT marker if available
            if req.ttft_ms is not None:
                ttft_x = x_start + (req.ttft_ms * time_scale)
                svg_parts.append(
                    f'<line class="ttft-line" '
                    f'x1="{ttft_x:.2f}" y1="{y}" '
                    f'x2="{ttft_x:.2f}" y2="{y + row_height - 2}" '
                    f'stroke="{self.colors["ttft_marker"]}"/>'
                )

            # Request label
            label_text = f"{req.model[:20]}... ({req.request_id[:8]})"
            svg_parts.append(
                f'<text class="label" x="-5" y="{y + row_height/2 + 4}" '
                f'text-anchor="end">{label_text}</text>'
            )

            # Duration label
            if req.is_complete:
                duration_label = f"{req.duration_ms:.0f}ms"
                svg_parts.append(
                    f'<text class="label" x="{x_start + bar_width + 5}" '
                    f'y="{y + row_height/2 + 4}">{duration_label}</text>'
                )

        # Draw time axis
        svg_parts.append(
            f'<line x1="0" y1="{chart_height}" x2="{chart_width}" '
            f'y2="{chart_height}" stroke="#999" stroke-width="1"/>'
        )

        # Time labels
        num_labels = 5
        for i in range(num_labels + 1):
            x = (chart_width / num_labels) * i
            time_ms = (data.total_duration_ms / num_labels) * i
            svg_parts.append(
                f'<text class="axis-label" x="{x}" y="{chart_height + 20}" '
                f'text-anchor="middle">{time_ms:.0f}ms</text>'
            )

        # Title
        svg_parts.append(
            f'<text class="axis-label" x="{chart_width/2}" y="-15" '
            f'text-anchor="middle" font-size="16px" font-weight="bold">'
            f'Request Waterfall - {len(data.requests)} requests</text>'
        )

        svg_parts.extend(["</g>", "</svg>"])

        return "\n".join(svg_parts)

    def _generate_empty_chart(self, width: int, height: int) -> str:
        """Generate empty chart when no data available."""
        return (
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
            f'<text x="{width/2}" y="{height/2}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="16px" fill="#999">'
            f'No request data available</text>'
            f'</svg>'
        )

    def generate_html(
        self, data: WaterfallData, width: int = 1200, height: int = 600
    ) -> str:
        """Generate complete HTML page with interactive chart."""
        svg = self.generate_svg(data, width, height)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FakeAI Request Waterfall</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-top: 0;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f9f9f9;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #2196F3;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2196F3;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        .chart-container {{
            margin: 20px 0;
            overflow-x: auto;
        }}
        .legend {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 FakeAI Request Waterfall</h1>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(data.requests)}</div>
                <div class="stat-label">Total Requests</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{data.max_concurrent}</div>
                <div class="stat-label">Max Concurrent</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{data.total_duration_ms:.0f}ms</div>
                <div class="stat-label">Time Window</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(r.output_tokens for r in data.requests)}</div>
                <div class="stat-label">Total Tokens</div>
            </div>
        </div>

        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #4CAF50; opacity: 0.6;"></div>
                <span>Request Duration</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #FF5722; width: 3px;"></div>
                <span>TTFT Marker</span>
            </div>
        </div>

        <div class="chart-container">
            {svg}
        </div>

        <div style="margin-top: 30px; padding: 15px; background: #f0f7ff; border-radius: 6px;">
            <strong>💡 Reading the Chart:</strong>
            <ul style="margin: 10px 0; padding-left: 20px;">
                <li><strong>Horizontal bars</strong> show request duration from start to completion</li>
                <li><strong>Orange dashed lines</strong> mark Time To First Token (TTFT)</li>
                <li><strong>Bar length</strong> indicates total request latency</li>
                <li><strong>Vertical position</strong> shows chronological order</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
        return html


# Singleton instance
_generator: WaterfallChartGenerator | None = None


def get_chart_generator() -> WaterfallChartGenerator:
    """Get the singleton chart generator instance."""
    global _generator
    if _generator is None:
        _generator = WaterfallChartGenerator()
    return _generator
