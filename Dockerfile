# ==========================================
# Stage 1: Build stage (builder)
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip build && \
    python -m build --wheel

# ==========================================
# Stage 2: Final runtime stage (runner)
# ==========================================
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    DATABASE_URL=sqlite:////app/data/hotel.db \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# Create non-root user and prepare persistent storage directory
RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

# Copy wheel artifact from builder stage and install
COPY --from=builder /build/dist/*.whl /tmp/
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir /tmp/*.whl && \
    rm -rf /tmp/*.whl

USER appuser

EXPOSE 8000

# Container healthcheck using standard library urllib
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "hotel_booking.api:app", "--host", "0.0.0.0", "--port", "8000"]
