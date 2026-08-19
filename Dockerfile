# ==============================================================================
# Production Dockerfile for ChemPulse Backend & Celery Worker
# ==============================================================================
# FROM python:3.11-slim
FROM python:3.12-slim-bookworm

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    TOKENIZERS_PARALLELISM=false \
    PORT=8000

WORKDIR /app

# System dependencies are not needed since we use pre-compiled wheels (e.g. psycopg2-binary, bcrypt)

# Copy and install python dependencies first for layer caching
COPY requirements.txt .

# Install CPU PyTorch and Python packages
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application source code
COPY alembic.ini .
COPY migrations/ migrations/
COPY src/ src/
COPY frontend/ frontend/

# Create persistent storage directories
RUN mkdir -p /app/storage/chroma /app/storage/uploads /app/logs

# Expose default port (Render will override $PORT at runtime)
EXPOSE 8000

# Default command for the Web service (can be overridden by render.yaml or Celery worker)
CMD ["sh", "-c", "alembic upgrade head && uvicorn src:app --host 0.0.0.0 --port ${PORT:-8000}"]
