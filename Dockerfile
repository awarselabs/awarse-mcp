# Production Dockerfile for Glama MCP Server Inspection & Container Deployment
FROM python:3.11-slim

WORKDIR /app

# Install base build & system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy repository source code
COPY . /app/

# Install SeatPrune and Healwright packages in system Python environment
RUN uv pip install --system -e ./seatprune -e ./healwright

ENV PYTHONUNBUFFERED=1

# Default command launches SeatPrune MCP Server via stdio
CMD ["python", "-m", "seatprune.server"]
