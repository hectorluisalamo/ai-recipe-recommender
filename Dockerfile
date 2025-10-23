FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install -r requirements.txt

# App code
COPY . .

# Install minimal tool to drop privileges (use 'su' which is available)
# Keep default user as root so entrypoint can chown the volume
USER root

EXPOSE 8000
HEALTHCHECK CMD curl -fsS http://localhost:8000/health || exit 1

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD curl -fsS http://localhost:8000/health || exit 1

# Default CMD is API; UI service overrides command in render.yaml
CMD ["bash","-lc","/app/infra/entrypoint.sh"]