FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only what's needed for dependency installation first
COPY pyproject.toml requirements.txt ./

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create the app directory structure before copying code
# This ensures the directory exists for the editable install
RUN mkdir -p app

# Copy the application code
COPY . .

# Now install the package in editable mode
RUN pip install --no-cache-dir -e .

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT:-8000} --reload
