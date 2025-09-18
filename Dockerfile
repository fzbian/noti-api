# Etapa base para instalar dependencias
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=0 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Instalar dependencias del sistema necesarias (si en el futuro se requiere, agregar aquí)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Etapa final runtime minimal
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Crear usuario no root
RUN useradd -ms /bin/bash appuser
WORKDIR /app

# Copiar dependencias instaladas desde base
COPY --from=base /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=base /usr/local/bin /usr/local/bin

# Copiar el código
COPY . .

# Ajustar permisos
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Variables de entorno ejemplo (sobrescribir en despliegue / Coolify)
# ENV ODOO_URL= ODOO_DB= ODOO_USERNAME= ODOO_PASSWORD= \
#     WHATSAPP_URL= WHATSAPP_INSTANCE= WHATSAPP_APIKEY= \
#     WHATSAPP_TRASPASOS= WHATSAPP_PEDIDOS= WHATSAPP_PRUEBAS= WHATSAPP_ATM=

# Comando: usar gunicorn con workers uvicorn
# Ajusta --workers según CPU disponibles (2*CPU+1). Coolify define WEB_CONCURRENCY a veces.
ENV PORT=8000
CMD exec gunicorn app:app \ 
    --bind 0.0.0.0:${PORT} \ 
    --workers ${WEB_CONCURRENCY:-2} \ 
    --worker-class uvicorn.workers.UvicornWorker \ 
    --timeout 60 \ 
    --graceful-timeout 30 \ 
    --log-level info
