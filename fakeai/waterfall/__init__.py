"""
Waterfall Chart Visualization System for FakeAI.

Provides real-time waterfall charts showing request timing:
- Request start time
- Time to first token (TTFT)
- Token generation timeline
- Request completion time

Decoupled, event-driven architecture integrating seamlessly with FakeAI's
metrics and monitoring systems.
"""

#  SPDX-License-Identifier: Apache-2.0

from .collector import RequestTimingCollector, RequestTiming
from .generator import WaterfallChartGenerator, WaterfallData
from .api import get_waterfall_data, get_waterfall_chart_html

__all__ = [
    "RequestTimingCollector",
    "RequestTiming",
    "WaterfallChartGenerator",
    "WaterfallData",
    "get_waterfall_data",
    "get_waterfall_chart_html",
]
