#!/usr/bin/env python3
"""
CLI entry point for the FakeAI OpenAI compatible server.
"""
#  SPDX-License-Identifier: Apache-2.0

import json
import sys
from pathlib import Path
from typing import Annotated

import cyclopts
import uvicorn
from pydantic import Field

from fakeai.config import AppConfig


def parse_latency_spec(spec: str) -> tuple[float, float]:
    """
    Parse latency specification in 'value:variance' format.

    Args:
        spec: Latency specification
            - Simple number: "20" → (20.0, 10.0)  # 10% default variance
            - With variance: "20:5" → (20.0, 5.0)  # 5% variance
            - No variance: "20:0" → (20.0, 0.0)  # No jitter

    Returns:
        Tuple of (value_ms, variance_percent)

    Examples:
        "20" → (20.0, 10.0)  # 20ms with 10% variance
        "50:15" → (50.0, 15.0)  # 50ms with 15% variance
        "10:0" → (10.0, 0.0)  # Exactly 10ms, no jitter
    """
    if ":" in spec:
        # Format: "value:variance"
        parts = spec.split(":")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid latency spec '{spec}'. Use format: 'value:variance' or 'value'")

        try:
            value = float(parts[0])
            variance = float(parts[1])
        except ValueError:
            raise ValueError(
                f"Invalid latency spec '{spec}'. Both value and variance must be numbers")

        if value < 0:
            raise ValueError(f"Latency value must be >= 0, got {value}")
        if variance < 0 or variance > 100:
            raise ValueError(f"Variance must be 0-100%, got {variance}")

        return (value, variance)
    else:
        # Simple number, use default 10% variance
        try:
            value = float(spec)
        except ValueError:
            raise ValueError(
                f"Invalid latency value '{spec}'. Must be a number or 'value:variance'")

        if value < 0:
            raise ValueError(f"Latency value must be >= 0, got {value}")

        return (value, 10.0)  # Default 10% variance


def parse_api_keys(api_key_sources: list[str]) -> list[str]:
    """
    Parse API keys from sources that can be either direct keys or file paths.

    Args:
        api_key_sources: List of strings that are either API keys or file paths

    Returns:
        List of parsed API keys

    File format:
        - One key per line
        - Blank lines are ignored
        - Lines starting with # are treated as comments and ignored
    """
    all_keys = []

    for source in api_key_sources:
        # Check if this looks like a file path
        path = Path(source)
        if path.exists() and path.is_file():
            # Parse file
            try:
                with open(path, "r") as f:
                    for line in f:
                        line = line.strip()
                        # Skip blank lines and comments
                        if line and not line.startswith("#"):
                            all_keys.append(line)
            except Exception as e:
                print(
                    f"Warning: Failed to read API key file '{source}': {e}",
                    file=sys.stderr,
                )
        else:
            # Treat as direct API key
            all_keys.append(source)

    return all_keys


def load_config_file(config_path: str | None) -> dict:
    """
    Load configuration from a file (YAML or JSON).

    Args:
        config_path: Path to config file, or None to auto-detect

    Returns:
        Dictionary of configuration values
    """
    # Auto-detect config files if not specified
    if config_path is None:
        for candidate in ["fakeai.yaml", "fakeai.yml", "fakeai.json"]:
            if Path(candidate).exists():
                config_path = candidate
                break

    if config_path is None:
        return {}

    path = Path(config_path)
    if not path.exists():
        print(
            f"Warning: Config file '{config_path}' not found",
            file=sys.stderr)
        return {}

    try:
        with open(path, "r") as f:
            if path.suffix in [".yaml", ".yml"]:
                try:
                    import yaml

                    return yaml.safe_load(f) or {}
                except ImportError:
                    print(
                        "Warning: PyYAML not installed. Install with: pip install pyyaml",
                        file=sys.stderr,
                    )
                    return {}
            elif path.suffix == ".json":
                return json.load(f)
            else:
                print(
                    f"Warning: Unsupported config file format: {path.suffix}",
                    file=sys.stderr,
                )
                return {}
    except Exception as e:
        print(
            f"Warning: Failed to load config file '{config_path}': {e}",
            file=sys.stderr)
        return {}


# Create the main Cyclopts app
app = cyclopts.App(
    name="fakeai",
    help="FakeAI - OpenAI Compatible API Server for Testing and Development",
    version="0.0.5",
)


@app.command
def server(
    *,
    config_file: Annotated[
        str | None,
        Field(
            description="Path to config file (YAML or JSON). Auto-detects fakeai.yaml, fakeai.yml, or fakeai.json if not specified."
        ),
    ] = None,
    host: Annotated[
        str | None,
        Field(description="Host address to bind the server to"),
    ] = None,
    port: Annotated[
        int | None,
        Field(description="Port number to bind the server to", ge=1, le=65535),
    ] = None,
    http2: Annotated[
        bool,
        Field(
            description="Enable HTTP/2 support using Hypercorn (requires SSL in production)"
        ),
    ] = False,
    ssl_certfile: Annotated[
        str | None,
        Field(description="Path to SSL certificate file (for HTTP/2)"),
    ] = None,
    ssl_keyfile: Annotated[
        str | None,
        Field(description="Path to SSL private key file (for HTTP/2)"),
    ] = None,
    debug: Annotated[
        bool | None,
        Field(description="Enable debug mode with auto-reload"),
    ] = None,
    response_delay: Annotated[
        float | None,
        Field(description="Base delay for responses in seconds", ge=0),
    ] = None,
    random_delay: Annotated[
        bool | None,
        Field(description="Add random variation to response delays"),
    ] = None,
    max_variance: Annotated[
        float | None,
        Field(description="Maximum variance for random delays (as a factor)", ge=0),
    ] = None,
    api_key: Annotated[
        list[str],
        Field(
            description="API key or path to file with keys (one per line). Can be specified multiple times. If not specified, authentication is disabled."
        ),
    ] = [],
    enable_rate_limiting: Annotated[
        bool | None,
        Field(
            description="Enable rate limiting (also controlled via --rate-limit-enabled)"
        ),
    ] = None,
    rate_limit_enabled: Annotated[
        bool | None,
        Field(description="Enable rate limiting"),
    ] = None,
    rate_limit_tier: Annotated[
        str | None,
        Field(
            description="Rate limit tier: free, tier-1, tier-2, tier-3, tier-4, tier-5 (default: tier-1)"
        ),
    ] = None,
    rate_limit_rpm: Annotated[
        int | None,
        Field(description="Custom requests per minute limit (overrides tier)", ge=1),
    ] = None,
    rate_limit_tpm: Annotated[
        int | None,
        Field(description="Custom tokens per minute limit (overrides tier)", ge=1),
    ] = None,
    # KV Cache settings
    enable_kv_cache: Annotated[
        bool | None,
        Field(
            description="Enable KV cache simulation (also controlled via --kv-cache-enabled)"
        ),
    ] = None,
    kv_cache_enabled: Annotated[
        bool | None,
        Field(description="Enable KV cache simulation"),
    ] = None,
    kv_cache_block_size: Annotated[
        int | None,
        Field(description="Block size for KV cache (default: 16)", ge=1, le=128),
    ] = None,
    kv_cache_workers: Annotated[
        int | None,
        Field(
            description="Number of parallel workers for cache processing (also --kv-cache-num-workers)",
            ge=1,
            le=64,
        ),
    ] = None,
    kv_cache_num_workers: Annotated[
        int | None,
        Field(
            description="Number of parallel workers for cache processing", ge=1, le=64
        ),
    ] = None,
    kv_overlap_weight: Annotated[
        float | None,
        Field(
            description="Weight for overlap scoring in KV cache (0.0-2.0)",
            ge=0.0,
            le=2.0,
        ),
    ] = None,
    # Safety settings
    enable_moderation: Annotated[
        bool | None,
        Field(description="Enable content moderation API"),
    ] = None,
    moderation_threshold: Annotated[
        float | None,
        Field(
            description="Threshold for content moderation (0.0-1.0)",
            ge=0.0,
            le=1.0),
    ] = None,
    enable_refusals: Annotated[
        bool | None,
        Field(description="Enable refusal responses for harmful content"),
    ] = None,
    enable_safety: Annotated[
        bool | None,
        Field(
            description="Enable safety refusal mechanism (also --enable-safety-features)"
        ),
    ] = None,
    enable_safety_features: Annotated[
        bool | None,
        Field(description="Enable safety refusal mechanism for harmful content"),
    ] = None,
    enable_jailbreak_detection: Annotated[
        bool | None,
        Field(description="Enable jailbreak/prompt injection detection"),
    ] = None,
    # Security settings (master flag)
    enable_security: Annotated[
        bool | None,
        Field(
            description="Master flag to enable ALL security features (overrides individual flags)"
        ),
    ] = None,
    security: Annotated[
        bool | None,
        Field(description="Alias for --enable-security"),
    ] = None,
    # Individual security settings
    hash_api_keys: Annotated[
        bool | None,
        Field(description="Hash API keys for secure storage"),
    ] = None,
    enable_input_validation: Annotated[
        bool | None,
        Field(description="Enable input validation and sanitization"),
    ] = None,
    enable_injection_detection: Annotated[
        bool | None,
        Field(description="Enable injection attack detection"),
    ] = None,
    enable_abuse_detection: Annotated[
        bool | None,
        Field(description="Enable IP-based abuse detection and banning"),
    ] = None,
    max_request_size: Annotated[
        int | None,
        Field(description="Maximum request size in bytes (default: 10 MB)", ge=1024),
    ] = None,
    cors_allowed_origins: Annotated[
        str | None,
        Field(
            description="CORS allowed origins (JSON array, e.g. '[\"http://localhost:3000\"]')"
        ),
    ] = None,
    # Audio settings
    enable_audio: Annotated[
        bool | None,
        Field(description="Enable audio input/output in chat completions"),
    ] = None,
    default_voice: Annotated[
        str | None,
        Field(
            description="Default voice for audio output (alloy, echo, fable, onyx, nova, shimmer, etc.)"
        ),
    ] = None,
    default_audio_format: Annotated[
        str | None,
        Field(description="Default audio format (mp3, opus, aac, flac, wav, pcm16)"),
    ] = None,
    # Performance settings
    enable_context_validation: Annotated[
        bool | None,
        Field(description="Enable context window validation and warnings"),
    ] = None,
    strict_token_counting: Annotated[
        bool | None,
        Field(description="Use strict token counting (slower but more accurate)"),
    ] = None,
    # Latency simulation settings
    ttft: Annotated[
        str | None,
        Field(
            description="Time to first token: 'ms' or 'ms:variance%'. Example: '20' (20ms±10%), '30:5' (30ms±5%), '10:0' (exactly 10ms)"
        ),
    ] = None,
    itl: Annotated[
        str | None,
        Field(
            description="Inter-token latency: 'ms' or 'ms:variance%'. Example: '5' (5ms±10%), '10:15' (10ms±15%), '3:0' (exactly 3ms)"
        ),
    ] = None,
) -> None:
    """
    Start the FakeAI server.

    The server provides an OpenAI-compatible API for testing and development,
    simulating responses without performing actual inference.

    Configuration Priority (highest to lowest):
        1. CLI arguments
        2. Config file (fakeai.yaml, fakeai.yml, or fakeai.json)
        3. Environment variables (FAKEAI_* prefix)
        4. Default values

    Examples:
        # Start with default settings (no authentication)
        $ fakeai server

        # Start with config file
        $ fakeai server --config-file myconfig.yaml

        # Start on a different host and port
        $ fakeai server --host 0.0.0.0 --port 9000

        # Enable authentication with direct API keys
        $ fakeai server --api-key sk-test-key1 --api-key sk-test-key2

        # Load API keys from a file
        $ fakeai server --api-key /path/to/keys.txt

        # Enable rate limiting with tier
        $ fakeai server --enable-rate-limiting --rate-limit-tier tier-3

        # Custom rate limits
        $ fakeai server --enable-rate-limiting --rate-limit-rpm 1000 --rate-limit-tpm 50000

        # Configure KV cache
        $ fakeai server --enable-kv-cache --kv-cache-workers 8

        # Disable safety features
        $ fakeai server --no-enable-safety --no-enable-moderation

        # Customize response timing
        $ fakeai server --response-delay 1.0 --max-variance 0.5
    """
    # Load config file (if specified or auto-detected)
    file_config = load_config_file(config_file)

    # Parse API keys from all sources (direct keys and files)
    parsed_keys = parse_api_keys(api_key)

    # Build config dictionary with priority: CLI > File > Env > Default
    # Start with file config
    config_dict = dict(file_config)

    # Helper to update config_dict only if CLI arg is provided
    def set_if_not_none(key: str, value):
        if value is not None:
            config_dict[key] = value

    # Apply CLI arguments (these override config file and env vars)
    set_if_not_none("host", host)
    set_if_not_none("port", port)
    set_if_not_none("debug", debug)
    set_if_not_none("response_delay", response_delay)
    set_if_not_none("random_delay", random_delay)
    set_if_not_none("max_variance", max_variance)

    # Handle rate limiting (support both parameter names)
    rate_limit_flag = (
        enable_rate_limiting if enable_rate_limiting is not None else rate_limit_enabled)
    set_if_not_none("rate_limit_enabled", rate_limit_flag)
    set_if_not_none("rate_limit_tier", rate_limit_tier)
    set_if_not_none("rate_limit_rpm", rate_limit_rpm)
    set_if_not_none("rate_limit_tpm", rate_limit_tpm)

    # Handle KV cache (support both parameter names)
    kv_cache_flag = enable_kv_cache if enable_kv_cache is not None else kv_cache_enabled
    set_if_not_none("kv_cache_enabled", kv_cache_flag)
    set_if_not_none("kv_cache_block_size", kv_cache_block_size)

    # Handle workers parameter (support both names)
    workers = kv_cache_workers if kv_cache_workers is not None else kv_cache_num_workers
    set_if_not_none("kv_cache_num_workers", workers)
    set_if_not_none("kv_overlap_weight", kv_overlap_weight)

    # Handle safety features (support both parameter names)
    safety_flag = enable_safety if enable_safety is not None else enable_safety_features
    set_if_not_none("enable_safety_features", safety_flag)
    set_if_not_none("enable_moderation", enable_moderation)
    set_if_not_none("moderation_threshold", moderation_threshold)
    set_if_not_none("enable_refusals", enable_refusals)
    set_if_not_none("enable_jailbreak_detection", enable_jailbreak_detection)

    # Audio settings
    set_if_not_none("enable_audio", enable_audio)
    set_if_not_none("default_voice", default_voice)
    set_if_not_none("default_audio_format", default_audio_format)

    # Security settings (handle master flag)
    security_flag = enable_security if enable_security is not None else security
    set_if_not_none("enable_security", security_flag)
    set_if_not_none("hash_api_keys", hash_api_keys)
    set_if_not_none("enable_input_validation", enable_input_validation)
    set_if_not_none("enable_injection_detection", enable_injection_detection)
    set_if_not_none("enable_abuse_detection", enable_abuse_detection)
    set_if_not_none("max_request_size", max_request_size)

    # Parse CORS origins if provided
    if cors_allowed_origins:
        try:
            cors_list = json.loads(cors_allowed_origins)
            config_dict["cors_allowed_origins"] = cors_list
        except json.JSONDecodeError:
            print(
                f"Warning: Invalid JSON for cors_allowed_origins, ignoring: {cors_allowed_origins}",
                file=sys.stderr,
            )

    # Performance settings
    set_if_not_none("enable_context_validation", enable_context_validation)
    set_if_not_none("strict_token_counting", strict_token_counting)

    # Parse latency settings (TTFT and ITL)
    if ttft is not None:
        try:
            ttft_value, ttft_var = parse_latency_spec(ttft)
            config_dict["ttft_ms"] = ttft_value
            config_dict["ttft_variance_percent"] = ttft_var
        except ValueError as e:
            print(f"Error parsing --ttft: {e}", file=sys.stderr)
            sys.exit(1)

    if itl is not None:
        try:
            itl_value, itl_var = parse_latency_spec(itl)
            config_dict["itl_ms"] = itl_value
            config_dict["itl_variance_percent"] = itl_var
        except ValueError as e:
            print(f"Error parsing --itl: {e}", file=sys.stderr)
            sys.exit(1)

    # Set API keys and automatically enable authentication if keys are provided
    if parsed_keys:
        config_dict["api_keys"] = parsed_keys
        config_dict["require_api_key"] = True
    elif "api_keys" not in config_dict:
        config_dict["require_api_key"] = False

    # Create config (this will also load from environment variables)
    # Priority: CLI args > Config file > Environment variables > Defaults
    config = AppConfig(**config_dict)

    # Determine protocol and server
    protocol = "https" if (http2 and ssl_certfile and ssl_keyfile) else "http"
    server_type = "Hypercorn (HTTP/2)" if http2 else "Uvicorn (HTTP/1.1)"

    # Display startup information
    print("=" * 70)
    print("FakeAI - OpenAI Compatible API Server")
    print("=" * 70)
    print(f"Server URL: {protocol}://{config.host}:{config.port}")
    print(f"API documentation: {protocol}://{config.host}:{config.port}/docs")
    print(
        f"Metrics endpoint: {protocol}://{config.host}:{config.port}/metrics")
    print(f"Health check: {protocol}://{config.host}:{config.port}/health")
    print()
    print(f"Server Configuration:")
    print(f"  - Server type: {server_type}")
    print(f"  - Protocol: {protocol.upper()}")
    if http2:
        print(f"  - HTTP/2: ENABLED")
        print(f"  - ALPN fallback: HTTP/1.1")
    print(f"  - Debug mode: {config.debug}")
    print(f"  - Response delay: {config.response_delay}s")
    print(f"  - Random delay: {config.random_delay}")
    print(f"  - Rate limiting: {config.rate_limit_enabled}")
    if config.require_api_key:
        key_type = "hashed" if config.is_api_key_hashing_enabled() else "plaintext"
        print(
            f"  - Authentication: ENABLED ({len(config.api_keys)} {key_type} keys)")
    else:
        print(f"  - Authentication: DISABLED (no API keys required)")
    if config.enable_security:
        print(f"  - Security features: ENABLED (all enabled via master flag)")
    else:
        print(f"  - Security features: DISABLED (testing mode)")
        if (
            config.enable_input_validation or
            config.enable_injection_detection or
            config.enable_abuse_detection
        ):
            print(f"    - Input validation: {config.enable_input_validation}")
            print(
                f"    - Injection detection: {config.enable_injection_detection}")
            print(f"    - Abuse detection: {config.enable_abuse_detection}")
    print("=" * 70)
    print()

    # Run the server
    module_path = "fakeai.app:app"

    if http2:
        # Use Hypercorn for HTTP/2 support
        try:
            import asyncio

            from hypercorn.asyncio import serve
            from hypercorn.config import Config as HypercornConfig

            h_config = HypercornConfig()
            h_config.bind = [f"{config.host}:{config.port}"]

            # SSL configuration for HTTP/2
            if ssl_certfile and ssl_keyfile:
                h_config.certfile = ssl_certfile
                h_config.keyfile = ssl_keyfile
                print(f"SSL enabled with certificate: {ssl_certfile}")
            else:
                print("WARNING: HTTP/2 without SSL (browsers require SSL for HTTP/2)")
                print("         Use --ssl-certfile and --ssl-keyfile for production")

            h_config.loglevel = "info" if not config.debug else "debug"
            h_config.accesslog = "-" if config.debug else None
            h_config.keep_alive_timeout = 5

            # Import app and run with Hypercorn
            from fakeai.app import app as fastapi_app

            print("Starting Hypercorn with HTTP/2 support...")
            asyncio.run(serve(fastapi_app, h_config))

        except ImportError:
            print("ERROR: Hypercorn not installed. Install with: pip install hypercorn")
            print("       Or run without --http2 flag to use Uvicorn")
            sys.exit(1)
    else:
        # Use Uvicorn for HTTP/1.1 (default)
        uvicorn.run(
            module_path,
            host=config.host,
            port=config.port,
            reload=config.debug,
            log_level="info" if not config.debug else "debug",
            access_log=config.debug,
        )


@app.command
def status(
    *,
    host: Annotated[
        str,
        Field(description="Host address of the FakeAI server"),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        Field(description="Port number of the FakeAI server", ge=1, le=65535),
    ] = 8000,
) -> None:
    """
    Check the status of a running FakeAI server.

    This command checks if the server is running and displays basic health information.

    Examples:
        # Check local server status
        $ fakeai status

        # Check remote server status
        $ fakeai status --host 192.168.1.100 --port 9000
    """
    import asyncio

    import aiohttp

    async def check_status():
        base_url = f"http://{host}:{port}"

        try:
            # Check health endpoint
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/health", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response.raise_for_status()
                    health_data = await response.json()

                    print("=" * 70)
                    print("FakeAI Server Status")
                    print("=" * 70)
                    print(f"Server URL: {base_url}")
                    print(f"Status: RUNNING ✓")
                    print(f"Timestamp: {health_data.get('timestamp', 'N/A')}")

                    if "status" in health_data:
                        status_text = health_data["status"].upper()
                        if health_data["status"] == "healthy":
                            print(f"Health: {status_text} ✓")
                        elif health_data["status"] == "degraded":
                            print(f"Health: {status_text} ⚠")
                        else:
                            print(f"Health: {status_text} ✗")

                    if "metrics_summary" in health_data:
                        metrics = health_data["metrics_summary"]
                        print(f"\nMetrics Summary:")
                        print(
                            f"  - Requests/sec: {metrics.get('total_requests_per_second', 0):.2f}"
                        )
                        print(
                            f"  - Errors/sec: {metrics.get('total_errors_per_second', 0):.2f}"
                        )
                        print(
                            f"  - Error rate: {metrics.get('error_rate_percentage', 0):.2f}%"
                        )
                        print(
                            f"  - Avg latency: {metrics.get('average_latency_seconds', 0) * 1000:.2f}ms"
                        )
                        print(
                            f"  - Active streams: {metrics.get('active_streams', 0)}")

                    print("=" * 70)

        except aiohttp.ClientConnectorError:
            print(
                f"ERROR: Cannot connect to FakeAI server at {base_url}",
                file=sys.stderr)
            print(f"       Make sure the server is running.", file=sys.stderr)
            sys.exit(1)
        except asyncio.TimeoutError:
            print(
                f"ERROR: Connection to {base_url} timed out",
                file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

    asyncio.run(check_status())


@app.command
def metrics(*,
            host: Annotated[str,
                            Field(description="Host address of the FakeAI server"),
                            ] = "127.0.0.1",
            port: Annotated[int,
                            Field(description="Port number of the FakeAI server",
                                  ge=1,
                                  le=65535),
                            ] = 8000,
            format: Annotated[str,
                              Field(description="Output format: json, prometheus, csv, or pretty"),
                              ] = "pretty",
            watch: Annotated[bool,
                             Field(description="Continuously watch metrics (refresh every 5 seconds)"),
                             ] = False,
            ) -> None:
    """
    Display metrics from a running FakeAI server.

    This command fetches and displays server metrics including request rates,
    response times, token counts, and streaming statistics.

    Examples:
        # Display metrics in pretty format
        $ fakeai metrics

        # Display metrics in JSON format
        $ fakeai metrics --format json

        # Export metrics in Prometheus format
        $ fakeai metrics --format prometheus > metrics.prom

        # Export metrics in CSV format
        $ fakeai metrics --format csv > metrics.csv

        # Continuously watch metrics
        $ fakeai metrics --watch
    """
    import asyncio
    import time as time_module

    import aiohttp

    base_url = f"http://{host}:{port}"

    async def fetch_and_display():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/metrics", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response.raise_for_status()
                    metrics_data = await response.json()

                    if format == "json":
                        print(json.dumps(metrics_data, indent=2))
                    elif format == "prometheus":
                        # Fetch Prometheus format
                        async with session.get(
                            f"{base_url}/metrics?format=prometheus",
                            timeout=aiohttp.ClientTimeout(total=5),
                        ) as prom_response:
                            if prom_response.status == 200:
                                print(await prom_response.text())
                            else:
                                print(
                                    "ERROR: Prometheus format not supported by this server version",
                                    file=sys.stderr,
                                )
                                sys.exit(1)
                    elif format == "csv":
                        # Fetch CSV format
                        async with session.get(
                            f"{base_url}/metrics?format=csv",
                            timeout=aiohttp.ClientTimeout(total=5),
                        ) as csv_response:
                            if csv_response.status == 200:
                                print(await csv_response.text())
                            else:
                                print(
                                    "ERROR: CSV format not supported by this server version", file=sys.stderr, )
                                sys.exit(1)
                    else:  # pretty format
                        print("=" * 70)
                        print("FakeAI Server Metrics")
                        print("=" * 70)

                        # Requests
                        if "requests" in metrics_data and metrics_data["requests"]:
                            print("\nRequests per second:")
                            for endpoint, stats in metrics_data["requests"].items(
                            ):
                                if stats["rate"] > 0:
                                    print(f"  {endpoint}: {stats['rate']:.2f}")

                        # Responses
                        if "responses" in metrics_data and metrics_data["responses"]:
                            print("\nResponses per second (with latency):")
                            for endpoint, stats in metrics_data["responses"].items(
                            ):
                                if stats["rate"] > 0:
                                    print(
                                        f"  {endpoint}: {
                                            stats['rate']:.2f} (avg: {
                                            stats['avg'] *
                                            1000:.2f}ms, p99: {
                                            stats['p99'] *
                                            1000:.2f}ms)")

                        # Tokens
                        if "tokens" in metrics_data and metrics_data["tokens"]:
                            print("\nTokens per second:")
                            for endpoint, stats in metrics_data["tokens"].items(
                            ):
                                if stats["rate"] > 0:
                                    print(f"  {endpoint}: {stats['rate']:.2f}")

                        # Errors
                        if "errors" in metrics_data and metrics_data["errors"]:
                            has_errors = any(
                                stats["rate"] > 0
                                for stats in metrics_data["errors"].values()
                            )
                            if has_errors:
                                print("\nErrors per second:")
                                for endpoint, stats in metrics_data["errors"].items(
                                ):
                                    if stats["rate"] > 0:
                                        print(
                                            f"  {endpoint}: {
                                                stats['rate']:.2f}")

                        # Streaming stats
                        if "streaming_stats" in metrics_data:
                            stream_stats = metrics_data["streaming_stats"]
                            if (
                                stream_stats.get("active_streams", 0) > 0 or
                                stream_stats.get("completed_streams", 0) > 0
                            ):
                                print("\nStreaming Statistics:")
                                print(
                                    f"  Active streams: {
                                        stream_stats.get(
                                            'active_streams', 0)}")
                                print(
                                    f"  Completed streams: {
                                        stream_stats.get(
                                            'completed_streams', 0)}")
                                print(
                                    f"  Failed streams: {
                                        stream_stats.get(
                                            'failed_streams', 0)}")

                                if stream_stats.get("ttft"):
                                    ttft = stream_stats["ttft"]
                                    print(
                                        f"  TTFT: avg={
                                            ttft['avg'] *
                                            1000:.2f}ms, p50={
                                            ttft['p50'] *
                                            1000:.2f}ms, p99={
                                            ttft['p99'] *
                                            1000:.2f}ms")

                                if stream_stats.get("tokens_per_second"):
                                    tps = stream_stats["tokens_per_second"]
                                    print(
                                        f"  Tokens/sec: avg={
                                            tps['avg']:.2f}, p50={
                                            tps['p50']:.2f}, p99={
                                            tps['p99']:.2f}")

                        print("=" * 70)

        except aiohttp.ClientConnectorError:
            print(
                f"ERROR: Cannot connect to FakeAI server at {base_url}",
                file=sys.stderr)
            print(f"       Make sure the server is running.", file=sys.stderr)
            sys.exit(1)
        except asyncio.TimeoutError:
            print(
                f"ERROR: Connection to {base_url} timed out",
                file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

    if watch:
        try:
            while True:
                # Clear screen (cross-platform)
                print("\033[2J\033[H", end="")
                asyncio.run(fetch_and_display())
                print("\n(Press Ctrl+C to stop)")
                time_module.sleep(5)
        except KeyboardInterrupt:
            print("\n\nStopped watching metrics")
    else:
        asyncio.run(fetch_and_display())


@app.command(name="cache-stats")
def cache_stats(
    *,
    host: Annotated[
        str,
        Field(description="Host address of the FakeAI server"),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        Field(description="Port number of the FakeAI server", ge=1, le=65535),
    ] = 8000,
) -> None:
    """
    Display KV cache statistics from a running FakeAI server.

    This command shows detailed information about the KV cache performance,
    including hit rates, block usage, and efficiency metrics.

    Examples:
        # Display cache stats
        $ fakeai cache-stats

        # Display cache stats from remote server
        $ fakeai cache-stats --host 192.168.1.100 --port 9000
    """
    import asyncio

    import aiohttp

    async def fetch_cache_stats():
        base_url = f"http://{host}:{port}"

        try:
            # Check if cache stats endpoint exists
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/cache-stats", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response.raise_for_status()
                    cache_data = await response.json()

                    print("=" * 70)
                    print("FakeAI KV Cache Statistics")
                    print("=" * 70)

                    if "enabled" in cache_data and not cache_data["enabled"]:
                        print("\nKV Cache: DISABLED")
                        print("\nTo enable KV cache, start the server with:")
                        print("  $ fakeai server --enable-kv-cache")
                        print("=" * 70)
                        return

                    print(f"\nCache Configuration:")
                    print(f"  - Enabled: {cache_data.get('enabled', False)}")
                    print(
                        f"  - Block size: {cache_data.get('block_size', 'N/A')} tokens"
                    )
                    print(
                        f"  - Workers: {cache_data.get('num_workers', 'N/A')}")
                    print(
                        f"  - Overlap weight: {cache_data.get('overlap_weight', 'N/A')}"
                    )

                    if "stats" in cache_data:
                        stats = cache_data["stats"]
                        print(f"\nCache Performance:")
                        print(
                            f"  - Total requests: {stats.get('total_requests', 0)}")
                        print(f"  - Cache hits: {stats.get('cache_hits', 0)}")
                        print(
                            f"  - Cache misses: {stats.get('cache_misses', 0)}")
                        hit_rate = stats.get("hit_rate", 0) * 100
                        print(f"  - Hit rate: {hit_rate:.2f}%")
                        print(
                            f"  - Cached blocks: {stats.get('cached_blocks', 0)}")
                        print(
                            f"  - Tokens saved: {stats.get('tokens_saved', 0)}")
                        print(
                            f"  - Avg speedup: {stats.get('avg_speedup', 0):.2f}x")

                    print("=" * 70)

        except aiohttp.ClientConnectorError:
            print(
                f"ERROR: Cannot connect to FakeAI server at {base_url}",
                file=sys.stderr)
            print(f"       Make sure the server is running.", file=sys.stderr)
            sys.exit(1)
        except asyncio.TimeoutError:
            print(
                f"ERROR: Connection to {base_url} timed out",
                file=sys.stderr)
            sys.exit(1)
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                print(
                    "ERROR: Cache stats endpoint not found.",
                    file=sys.stderr)
                print(
                    "       This feature may not be available in your server version.",
                    file=sys.stderr,
                )
            else:
                print(f"ERROR: HTTP {e.status}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

    asyncio.run(fetch_cache_stats())


@app.command
def interactive(
    *,
    host: Annotated[
        str,
        Field(description="Host address of the FakeAI server"),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        Field(description="Port number of the FakeAI server", ge=1, le=65535),
    ] = 8000,
    api_key: Annotated[
        str | None,
        Field(description="API key for authentication"),
    ] = None,
) -> None:
    """
    Start an interactive REPL for testing the FakeAI server.

    This command provides a REPL (Read-Eval-Print Loop) for sending requests
    to the FakeAI server and viewing responses interactively.

    Commands in REPL:
        /help              - Show help
        /models            - List available models
        /metrics           - Show current metrics
        /exit or /quit     - Exit the REPL
        /set model <name>  - Set the current model
        /set stream on|off - Enable/disable streaming
        <message>          - Send a chat completion request

    Examples:
        # Start interactive mode
        $ fakeai interactive

        # Connect to remote server with API key
        $ fakeai interactive --host 192.168.1.100 --api-key sk-test-key
    """
    import asyncio

    import aiohttp

    base_url = f"http://{host}:{port}"
    current_model = "openai/gpt-oss-120b"
    streaming = False
    conversation_history = []

    # Test connection
    async def test_connection():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/health", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response.raise_for_status()
        except Exception as e:
            print(
                f"ERROR: Cannot connect to FakeAI server at {base_url}",
                file=sys.stderr)
            print(f"       {e}", file=sys.stderr)
            sys.exit(1)

    asyncio.run(test_connection())

    print("=" * 70)
    print("FakeAI Interactive REPL")
    print("=" * 70)
    print(f"Connected to: {base_url}")
    print(f"Type /help for commands, /exit to quit")
    print("=" * 70)
    print()

    def show_help():
        print("\nAvailable commands:")
        print("  /help              - Show this help message")
        print("  /models            - List available models")
        print("  /metrics           - Show current metrics")
        print("  /clear             - Clear conversation history")
        print("  /history           - Show conversation history")
        print("  /set model <name>  - Set the current model")
        print("  /set stream on|off - Enable/disable streaming")
        print("  /exit or /quit     - Exit the REPL")
        print("  <message>          - Send a chat completion request")
        print()

    async def handle_models_command():
        try:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/v1/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    response.raise_for_status()
                    models_data = await response.json()
                    print("\nAvailable models:")
                    for model in models_data.get("data", []):
                        print(f"  - {model['id']}")
                    print()
        except Exception as e:
            print(f"ERROR: {e}")

    async def handle_metrics_command():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/metrics", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response.raise_for_status()
                    metrics_data = await response.json()
                    print(json.dumps(metrics_data, indent=2))
        except Exception as e:
            print(f"ERROR: {e}")

    async def handle_chat_completion(user_input):
        nonlocal conversation_history

        conversation_history.append({"role": "user", "content": user_input})

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        request_data = {
            "model": current_model,
            "messages": conversation_history,
            "stream": streaming,
        }

        try:
            async with aiohttp.ClientSession() as session:
                if streaming:
                    # Handle streaming response
                    async with session.post(
                        f"{base_url}/v1/chat/completions",
                        headers=headers,
                        json=request_data,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        response.raise_for_status()

                        print("\nAssistant: ", end="", flush=True)
                        full_content = ""
                        async for line in response.content:
                            if line:
                                line_str = line.decode("utf-8").strip()
                                if line_str.startswith("data: "):
                                    data_str = line_str[6:]
                                    if data_str.strip() == "[DONE]":
                                        break
                                    try:
                                        chunk_data = json.loads(data_str)
                                        if chunk_data["choices"][0]["delta"].get(
                                                "content"):
                                            content = chunk_data["choices"][0]["delta"][
                                                "content"
                                            ]
                                            print(content, end="", flush=True)
                                            full_content += content
                                    except json.JSONDecodeError:
                                        pass
                        print("\n")

                        # Add assistant response to history
                        conversation_history.append(
                            {"role": "assistant", "content": full_content}
                        )

                else:
                    # Handle non-streaming response
                    async with session.post(
                        f"{base_url}/v1/chat/completions",
                        headers=headers,
                        json=request_data,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        response.raise_for_status()
                        result = await response.json()

                        assistant_message = result["choices"][0]["message"]["content"]
                        print(f"\nAssistant: {assistant_message}\n")

                        # Add assistant response to history
                        conversation_history.append(
                            {"role": "assistant", "content": assistant_message}
                        )

        except aiohttp.ClientResponseError as e:
            print(f"\nERROR: HTTP {e.status}")
            try:
                error_data = json.loads(e.message)
                print(
                    f"       {
                        error_data.get(
                            'error',
                            {}).get(
                            'message',
                            str(e))}")
            except BaseException:
                print(f"       {e}")
            print()
            # Remove the failed user message from history
            conversation_history.pop()

        except Exception as e:
            print(f"\nERROR: {e}\n")
            # Remove the failed user message from history
            conversation_history.pop()

    while True:
        try:
            user_input = input(f"[{current_model}]> ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                cmd_parts = user_input[1:].split()
                cmd = cmd_parts[0].lower()

                if cmd in ["exit", "quit"]:
                    print("Goodbye!")
                    break

                elif cmd == "help":
                    show_help()

                elif cmd == "models":
                    asyncio.run(handle_models_command())

                elif cmd == "metrics":
                    asyncio.run(handle_metrics_command())

                elif cmd == "clear":
                    conversation_history = []
                    print("Conversation history cleared.")

                elif cmd == "history":
                    if not conversation_history:
                        print("No conversation history.")
                    else:
                        print("\nConversation history:")
                        for msg in conversation_history:
                            role = msg["role"]
                            content = msg.get("content", "")
                            print(f"  [{role}]: {content}")
                        print()

                elif cmd == "set" and len(cmd_parts) >= 3:
                    setting = cmd_parts[1].lower()
                    value = " ".join(cmd_parts[2:])

                    if setting == "model":
                        current_model = value
                        print(f"Model set to: {current_model}")
                    elif setting == "stream":
                        if value.lower() in ["on", "true", "yes", "1"]:
                            streaming = True
                            print("Streaming enabled")
                        else:
                            streaming = False
                            print("Streaming disabled")
                    else:
                        print(f"Unknown setting: {setting}")

                else:
                    print(f"Unknown command: {cmd}")
                    print("Type /help for available commands")

                continue

            # Send chat completion request
            asyncio.run(handle_chat_completion(user_input))

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


def main() -> int:
    """Entry point for the CLI."""
    try:
        app()
        return 0
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        return 0
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
