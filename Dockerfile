# Production Dockerfile for Personal Live Quant Brain
FROM python:3.11-slim

WORKDIR /app

# Install system utilities and curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt pyproject.toml README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir fastapi uvicorn[standard] httpx python-telegram-bot aiosqlite pydantic-settings google-genai psutil pytest-asyncio

# Copy application code
COPY . .

# Install editable package
RUN pip install --no-cache-dir -e .

# Create persistent data directory
RUN mkdir -p /app/data

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    APP_ENV=production

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start persistent services (API + Telegram)
CMD ["python", "deployment/run_production.py"]
