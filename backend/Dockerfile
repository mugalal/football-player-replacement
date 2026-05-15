# Backend Dockerfile for LOCAL docker-compose use.
# Build context is the PROJECT ROOT (see docker-compose.yml), so all COPY
# paths here are relative to the project root, not to backend/.
#
# models/ is NOT copied into this image. Local development mounts it via a
# docker-compose volume (./models:/app/models:ro). For Hugging Face Spaces,
# use hf-space/Dockerfile, which copies models/ in.

FROM python:3.11-slim

# Build tools required for some scientific-Python wheels on slim images,
# plus curl for the HEALTHCHECK.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc g++ curl \
 && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install Python deps first (cacheable layer).
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Application code.
COPY backend/ /app/backend/
COPY src/ /app/src/

RUN chown -R appuser:appuser /app

USER appuser
WORKDIR /app/backend

ENV PORT=7860 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:${PORT}/api/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
