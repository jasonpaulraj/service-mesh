FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

COPY . .

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT:-8000} --reload
