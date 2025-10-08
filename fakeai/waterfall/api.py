"""
API endpoints for waterfall chart access.

Provides both data API (JSON) and visualization API (HTML/SVG).
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from fastapi import Query
from fastapi.responses import HTMLResponse, JSONResponse

from .collector import get_timing_collector
from .generator import get_chart_generator


def get_waterfall_data(
    limit: int = Query(100, ge=1, le=1000),
    endpoint: str | None = Query(None),
    model: str | None = Query(None),
) -> dict[str, Any]:
    """
    Get waterfall timing data as JSON.

    Query Parameters:
        limit: Maximum number of requests to return (1-1000)
        endpoint: Filter by endpoint (e.g., /v1/chat/completions)
        model: Filter by model name

    Returns:
        JSON with request timing data and statistics
    """
    collector = get_timing_collector()
    requests = collector.get_recent_requests(
        limit=limit, endpoint=endpoint, model=model
    )

    # Convert to JSON-serializable format
    data = {
        "requests": [
            {
                "request_id": req.request_id,
                "endpoint": req.endpoint,
                "model": req.model,
                "start_time": req.start_time,
                "end_time": req.end_time,
                "duration_ms": req.duration_ms,
                "ttft_ms": req.ttft_ms,
                "is_streaming": req.is_streaming,
                "input_tokens": req.input_tokens,
                "output_tokens": req.output_tokens,
                "tokens": [
                    {
                        "index": t.token_index,
                        "timestamp_ms": t.timestamp_ms,
                        "latency_ms": t.latency_ms,
                    }
                    for t in req.tokens
                ],
                "is_complete": req.is_complete,
            }
            for req in requests
        ],
        "stats": collector.get_stats(),
        "active_requests": len(collector.get_active_requests()),
    }

    return data


def get_waterfall_chart_html(
    limit: int = Query(100, ge=1, le=1000),
    endpoint: str | None = Query(None),
    model: str | None = Query(None),
    width: int = Query(1200, ge=800, le=3000),
    height: int = Query(600, ge=400, le=2000),
) -> HTMLResponse:
    """
    Get waterfall chart as interactive HTML page.

    Query Parameters:
        limit: Maximum number of requests to display (1-1000)
        endpoint: Filter by endpoint
        model: Filter by model name
        width: Chart width in pixels (800-3000)
        height: Chart height in pixels (400-2000)

    Returns:
        HTML page with SVG waterfall chart
    """
    collector = get_timing_collector()
    generator = get_chart_generator()

    requests = collector.get_recent_requests(
        limit=limit, endpoint=endpoint, model=model
    )
    waterfall_data = generator.prepare_data(requests)
    html = generator.generate_html(waterfall_data, width=width, height=height)

    return HTMLResponse(content=html)
