FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml README.md ./

RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install --no-cache -e .

FROM python:3.12-slim AS runtime

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY app/ ./app/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8085

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8085"]
