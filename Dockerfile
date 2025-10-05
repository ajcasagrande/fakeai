# Multi-stage Dockerfile for FakeAI
# Stage 1: Builder - Install dependencies
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file
COPY pyproject.toml ./

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Extract and install just the dependencies (not the package itself)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    "fastapi>=0.103.0" \
    "uvicorn>=0.23.0" \
    "hypercorn>=0.16.0" \
    "pydantic>=2.0.0" \
    "pydantic-settings>=2.0.0" \
    "numpy>=1.24.0" \
    "faker>=13.0.0" \
    "python-multipart>=0.0.9" \
    "cyclopts>=3.0.0"

# Stage 2: Runtime - Create minimal production image
FROM python:3.12-slim

# Set metadata
LABEL maintainer="Anthony Casagrande"
LABEL description="FakeAI - OpenAI Compatible API Server"
LABEL version="0.0.4"

# Create non-root user for security
RUN groupadd -r fakeai && useradd -r -g fakeai fakeai

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY fakeai/ ./fakeai/

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    FAKEAI_HOST=0.0.0.0 \
    FAKEAI_PORT=8000

# Change ownership to non-root user
RUN chown -R fakeai:fakeai /app

# Switch to non-root user
USER fakeai

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command (can be overridden)
CMD ["python", "-m", "fakeai.cli"]
