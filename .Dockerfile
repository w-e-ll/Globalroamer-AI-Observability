# =========================================================
# GlobalRoamer AI Observability
# Dockerfile
# =========================================================

FROM python:3.11-slim

# =========================================================
# Environment
# =========================================================

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# =========================================================
# System packages
# =========================================================

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# =========================================================
# Application directory
# =========================================================

WORKDIR /app

# =========================================================
# Dependencies
# =========================================================

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# =========================================================
# Application files
# =========================================================

COPY . .

# =========================================================
# Runtime directories
# =========================================================

RUN mkdir -p /app/var/input/traces
RUN mkdir -p /app/var/input/results
RUN mkdir -p /app/var/input/campaign_metadata

RUN mkdir -p /app/var/data/normalized_events
RUN mkdir -p /app/var/data/chunks
RUN mkdir -p /app/var/data/embeddings
RUN mkdir -p /app/var/data/vector_db

RUN mkdir -p /app/var/output/ai_summaries
RUN mkdir -p /app/var/output/root_cause_reports
RUN mkdir -p /app/var/output/campaign_health

RUN mkdir -p /app/var/log

# =========================================================
# PYTHONPATH
# =========================================================

ENV PYTHONPATH=/app

# =========================================================
# Default command
# =========================================================

CMD ["bash"]
