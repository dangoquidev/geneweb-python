# Multi-stage Dockerfile for GenEWeb Python project
# Builds both frontend and backend in an optimized container

# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Install pnpm
RUN npm install -g pnpm

# Copy frontend package files
COPY src/frontend/package.json src/frontend/pnpm-lock.yaml ./

# Install frontend dependencies
RUN pnpm install --frozen-lockfile

# Copy frontend source
COPY src/frontend/ ./

# Build frontend (skip type checking for Docker build)
RUN pnpm build-docker

# Stage 2: Python Backend
FROM python:3.11-slim AS backend

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/src

# Create app user
RUN groupadd -r geneweb && useradd --no-log-init -r -g geneweb geneweb

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

# Copy backend source code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY run_api.py ./
COPY Makefile ./

# Copy data directory (create if empty)
COPY data/ ./data/

# Create demo database if showcase.pickle doesn't exist
RUN if [ ! -f ./data/showcase.pickle ]; then \
        echo "Creating demo database..."; \
        python3 scripts/create_demo_database.py; \
    fi

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist ./src/frontend/dist

# Create directories and set permissions
RUN mkdir -p /app/logs /app/tmp && \
    chown -R geneweb:geneweb /app

# Install tmux for fullstack mode
RUN apt-get update && apt-get install -y tmux && rm -rf /var/lib/apt/lists/*

# Switch to non-root user
USER geneweb

# Expose ports
EXPOSE 8000 5173 2316 2317

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Default command (can be overridden)
CMD ["python", "run_api.py", "--host", "0.0.0.0", "--port", "8000", "--debug"]
