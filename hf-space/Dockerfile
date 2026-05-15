# Hugging Face Space Dockerfile.
#
# IMPORTANT: this file is committed in this repo at hf-space/Dockerfile,
# but is meant to be COPIED to the ROOT of your HF Space repo (not this
# repo). The HF Space repo layout should be:
#
#   <space-repo>/
#   ├── Dockerfile             ← copy this file here
#   ├── .dockerignore          ← copy hf-space/.dockerignore here
#   ├── README.md              ← HF requires this at root
#   ├── backend/               ← copy from this repo
#   ├── src/                   ← copy from this repo
#   └── models/gp2/            ← copy from this repo (tracked via Git LFS)
#
# Unlike backend/Dockerfile (which omits models because the local Docker
# stack mounts them as a volume), this Dockerfile COPIES models/ into the
# image so the Space is self-contained.

FROM python:3.11-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc g++ curl \
 && rm -rf /var/lib/apt/lists/*

# HF Spaces require the running user to have UID 1000 and HOME=/home/user.
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /app

COPY --chown=user backend/requirements.txt /app/backend/requirements.txt
USER user
RUN pip install --no-cache-dir --user -r /app/backend/requirements.txt
USER root

COPY --chown=user backend/ /app/backend/
COPY --chown=user src/ /app/src/
COPY --chown=user models/ /app/models/

RUN chown -R user:user /app
USER user
WORKDIR /app/backend

ENV PORT=7860 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=120s \
    CMD curl -fsS http://localhost:${PORT}/api/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
