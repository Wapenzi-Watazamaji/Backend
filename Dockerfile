# ─── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency manifests first (layer-cache friendly)
# README.md is required because pyproject.toml references it
COPY pyproject.toml README.md ./

# Install dependencies into an isolated venv
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install --no-cache -e .

# ─── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Bring the pre-built venv from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY app/ ./app/

# Activate venv by updating PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Drop to non-root user
USER appuser

EXPOSE 8085

# Reload disabled in production; enable in dev via compose override
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8085"]
