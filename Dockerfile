# =============================================================================
# Enterprise IT Support Assistant — Dockerfile
# Multi-stage build for Google Cloud Run deployment.
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: dependency builder
# Installs production dependencies into a clean layer.
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools needed for some native packages (chromadb, httpx)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: runtime image
# Lean image with only what's needed to run the app.
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Non-root user for security (Cloud Run best practice)
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Copy application source
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser knowledge_base/documents/ ./knowledge_base/documents/

# Cloud Run injects PORT env var; default to 8080
ENV PORT=8080
EXPOSE 8080

# Health check for Cloud Run readiness probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health').raise_for_status()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
