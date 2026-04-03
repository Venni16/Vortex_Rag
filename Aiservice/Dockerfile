# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools needed for some wheels (tokenizers, hiredis, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install deps into /app/wheels so runtime stage can copy them cleanly
RUN pip install --upgrade pip \
    && pip install --no-cache-dir torch==2.3.0+cpu \
       --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime OS deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

# Model cache dir (HuggingFace will download here on first start)
RUN mkdir -p /app/model_cache && chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1 \
    TRANSFORMERS_CACHE=/app/model_cache \
    HF_HOME=/app/model_cache

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
