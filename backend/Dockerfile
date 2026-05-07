# Backend für G&G und kompatible Präzisionswaagen — FastAPI + pyserial
# Build:  docker build -t waage-backend ./backend
# Run:    docker run --rm -p 8200:8200 --device=/dev/ttyUSB0 -v $PWD/data:/data waage-backend
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
COPY VERSION ./
COPY README.md* ./
RUN pip install -e .

# Daten-Volume — alle SQLite-DBs und config.json landen hier
RUN mkdir -p /data
ENV WAAGE_DATA_DIR=/data \
    WAAGE_SAMPLES_DB=/data/samples.db \
    WAAGE_MESSLOG_DB=/data/messlog.db \
    WAAGE_CONTAINERS_DB=/data/containers.db \
    WAAGE_COUNT_TEMPLATES_DB=/data/count_templates.db

EXPOSE 8200

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8200/scale/health || exit 1

CMD ["python", "-m", "waage.api"]
