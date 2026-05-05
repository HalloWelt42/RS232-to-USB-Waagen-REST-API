# Backend für G&G PLC Waage — FastAPI + pyserial
# Build:  docker build -t waage-backend ./backend
# Run:    docker run --rm -p 8200:8200 --device=/dev/ttyUSB0 waage-backend
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    WAAGE_HOST=0.0.0.0 \
    WAAGE_API_PORT=8200 \
    TZ=Europe/Berlin

WORKDIR /app

# System: tzdata für TZ, curl für Healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl tzdata \
    && rm -rf /var/lib/apt/lists/*

# Dependencies zuerst (Cache-freundlich)
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install \
    "pyserial>=3.5" \
    "fastapi>=0.110" \
    "uvicorn[standard]>=0.27"

# Quellen
COPY src/ ./src/
COPY README.md* ./
RUN pip install -e .

# Daten-Volume
RUN mkdir -p /data
ENV WAAGE_CSV=/data/waage.csv \
    WAAGE_SQLITE=/data/waage.db

EXPOSE 8200

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8200/health || exit 1

CMD ["python", "-m", "waage.api"]
