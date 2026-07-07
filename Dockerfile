# ── Stage 1: Build dependencies ────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install compilation headers (needed for some python packages like greenlet, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies into user space to avoid root permission conflicts
COPY pyproject.toml .
RUN pip install --no-cache-dir --user -e ".[frontend]"

# Install greenlet explicitly in user space
RUN pip install --no-cache-dir --user greenlet

# ── Stage 2: Production runtime image ──────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local
COPY . .

# Expose python bin path
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Expose default ports
EXPOSE 8000
EXPOSE 8501

# Default entry point (can be overridden in docker-compose)
CMD ["python", "main.py"]
