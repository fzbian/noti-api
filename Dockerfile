FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_PORT=8084 \
    PORT=8084

WORKDIR /app

# Instalar curl para healthcheck (imagen slim no lo trae por defecto)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd -ms /bin/bash appuser

COPY . .
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8084

# Healthcheck simple para Coolify (usa /health). Si falla => container unhealthy.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD sh -c 'curl -fsS http://127.0.0.1:${PORT:-8084}/health || exit 1'

# Arranque simple con uvicorn
CMD ["sh","-c","python -m uvicorn app:app --host 0.0.0.0 --port ${PORT:-8084}"]
