FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p \
    var/input/traces \
    var/data/normalized_events \
    var/data/chunks \
    var/data/vector_db \
    var/output/ai_summaries/similarity_results \
    var/output/root_cause_reports \
    var/output/campaign_health \
    var/log

EXPOSE 8501

CMD ["streamlit", "run", "globalroamer_ai/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
