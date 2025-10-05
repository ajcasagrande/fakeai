#!/bin/bash
set -e

# FakeAI Docker Entrypoint Script
# This script handles configuration validation and server startup

echo "========================================="
echo "FakeAI - OpenAI Compatible API Server"
echo "Version: 0.0.4"
echo "========================================="

# Function to print colored messages
log_info() {
    echo "[INFO] $1"
}

log_warn() {
    echo "[WARN] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

# Function to validate environment variables
validate_config() {
    log_info "Validating configuration..."

    # Check host
    if [ -z "$FAKEAI_HOST" ]; then
        export FAKEAI_HOST="0.0.0.0"
        log_warn "FAKEAI_HOST not set, using default: 0.0.0.0"
    fi

    # Check port
    if [ -z "$FAKEAI_PORT" ]; then
        export FAKEAI_PORT="8000"
        log_warn "FAKEAI_PORT not set, using default: 8000"
    fi

    # Validate port is a number and in valid range
    if ! [[ "$FAKEAI_PORT" =~ ^[0-9]+$ ]] || [ "$FAKEAI_PORT" -lt 1 ] || [ "$FAKEAI_PORT" -gt 65535 ]; then
        log_error "Invalid port: $FAKEAI_PORT (must be 1-65535)"
        exit 1
    fi

    # Check response delay
    if [ -n "$FAKEAI_RESPONSE_DELAY" ]; then
        if ! [[ "$FAKEAI_RESPONSE_DELAY" =~ ^[0-9]+\.?[0-9]*$ ]]; then
            log_error "Invalid FAKEAI_RESPONSE_DELAY: $FAKEAI_RESPONSE_DELAY (must be a number)"
            exit 1
        fi
    fi

    # Check max variance
    if [ -n "$FAKEAI_MAX_VARIANCE" ]; then
        if ! [[ "$FAKEAI_MAX_VARIANCE" =~ ^[0-9]+\.?[0-9]*$ ]]; then
            log_error "Invalid FAKEAI_MAX_VARIANCE: $FAKEAI_MAX_VARIANCE (must be a number)"
            exit 1
        fi
    fi

    # Check requests per minute
    if [ -n "$FAKEAI_REQUESTS_PER_MINUTE" ]; then
        if ! [[ "$FAKEAI_REQUESTS_PER_MINUTE" =~ ^[0-9]+$ ]]; then
            log_error "Invalid FAKEAI_REQUESTS_PER_MINUTE: $FAKEAI_REQUESTS_PER_MINUTE (must be an integer)"
            exit 1
        fi
    fi

    log_info "Configuration validated successfully"
}

# Function to print configuration
print_config() {
    echo ""
    log_info "Current Configuration:"
    echo "  Host: $FAKEAI_HOST"
    echo "  Port: $FAKEAI_PORT"
    echo "  Debug: ${FAKEAI_DEBUG:-false}"
    echo "  Response Delay: ${FAKEAI_RESPONSE_DELAY:-0.5}s"
    echo "  Random Delay: ${FAKEAI_RANDOM_DELAY:-true}"
    echo "  Max Variance: ${FAKEAI_MAX_VARIANCE:-0.3}"

    if [ "$FAKEAI_REQUIRE_API_KEY" = "true" ]; then
        echo "  API Key Required: true"
        if [ -n "$FAKEAI_API_KEYS" ]; then
            KEY_COUNT=$(echo "$FAKEAI_API_KEYS" | tr ',' '\n' | wc -l)
            echo "  API Keys Configured: $KEY_COUNT"
        else
            log_warn "API key required but none configured!"
        fi
    else
        echo "  API Key Required: false"
    fi

    if [ "$FAKEAI_RATE_LIMIT_ENABLED" = "true" ]; then
        echo "  Rate Limiting: enabled"
        echo "  Requests per Minute: ${FAKEAI_REQUESTS_PER_MINUTE:-10000}"
        if [ -n "$FAKEAI_REDIS_URL" ]; then
            echo "  Redis URL: ${FAKEAI_REDIS_URL}"
        fi
    else
        echo "  Rate Limiting: disabled"
    fi
    echo ""
}

# Function to wait for Redis
wait_for_redis() {
    if [ "$FAKEAI_RATE_LIMIT_ENABLED" = "true" ] && [ -n "$FAKEAI_REDIS_URL" ]; then
        log_info "Waiting for Redis to be ready..."

        # Extract host and port from Redis URL
        # Format: redis://host:port/db
        REDIS_HOST=$(echo "$FAKEAI_REDIS_URL" | sed -E 's|redis://([^:]+):([0-9]+).*|\1|')
        REDIS_PORT=$(echo "$FAKEAI_REDIS_URL" | sed -E 's|redis://([^:]+):([0-9]+).*|\2|')

        MAX_RETRIES=30
        RETRY_COUNT=0

        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
            if timeout 1 bash -c "cat < /dev/null > /dev/tcp/$REDIS_HOST/$REDIS_PORT" 2>/dev/null; then
                log_info "Redis is ready!"
                return 0
            fi

            RETRY_COUNT=$((RETRY_COUNT + 1))
            log_info "Redis not ready yet, attempt $RETRY_COUNT/$MAX_RETRIES..."
            sleep 1
        done

        log_error "Redis failed to become ready after $MAX_RETRIES attempts"
        log_warn "Starting without Redis, rate limiting may not work correctly"
    fi
}

# Function to handle graceful shutdown
graceful_shutdown() {
    log_info "Received shutdown signal, stopping server gracefully..."

    # Send SIGTERM to all child processes
    if [ -n "$SERVER_PID" ]; then
        kill -TERM "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi

    log_info "Server stopped"
    exit 0
}

# Set up signal handlers
trap graceful_shutdown SIGTERM SIGINT SIGQUIT

# Main execution
main() {
    # Validate configuration
    validate_config

    # Print configuration
    print_config

    # Wait for dependencies
    wait_for_redis

    # Start the server
    log_info "Starting FakeAI server..."
    echo "========================================="
    echo ""

    # Execute the command passed to the container
    exec "$@" &
    SERVER_PID=$!

    # Wait for the server process
    wait "$SERVER_PID"
}

# Run main function
main "$@"
