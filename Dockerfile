# Etapa base para instalar dependencias
FROM python:3.12-slim AS base

# Variables de entorno recomendadas
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos requirements antes (para cache)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Crear usuario no root
RUN useradd -u 1001 -ms /bin/bash appuser && \
    chmod +x /app/start.sh && \
    chown -R appuser:appuser /app

USER appuser

# Puerto lógico (Coolify puede sobrescribir mapping)
EXPOSE 8000

# Healthcheck simple usando el endpoint /health
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["/app/start.sh"]
