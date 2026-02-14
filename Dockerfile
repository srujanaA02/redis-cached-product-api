# Multi-stage Dockerfile for optimized image size
# Stage 1: Builder - Install dependencies
FROM python:3.9-slim-bullseye AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runner - Final lightweight image
FROM python:3.9-slim-bullseye

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application source code
COPY src/ ./

# Copy tests for running test suite
COPY tests/ ./tests/

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Create writable data directory
RUN mkdir -p /app/data && chmod -R 777 /app/data

# Expose the application port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "main.py"]
