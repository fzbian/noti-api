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

# HEALTHCHECK: usa curl si está disponible o python stdlib como fallback
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD bash -c 'curl -fsS http://127.0.0.1:${PORT:-8000}/health || python - <<"PY"\nimport urllib.request,sys\nurl=f"http://127.0.0.1:{int(__import__("os").environ.get("PORT","8000"))}/health"\ntry:\n  with urllib.request.urlopen(url,timeout=3) as r:\n    import json; data=json.loads(r.read().decode());\n    sys.exit(0 if data.get("status")=="ok" else 1)\nexcept Exception as e:\n  print(e); sys.exit(1)\nPY'

# Variables de entorno ejemplo (sobrescribir en despliegue / Coolify)
# ENV ODOO_URL= ODOO_DB= ODOO_USERNAME= ODOO_PASSWORD= \
#     WHATSAPP_URL= WHATSAPP_INSTANCE= WHATSAPP_APIKEY= \
#     WHATSAPP_TRASPASOS= WHATSAPP_PEDIDOS= WHATSAPP_PRUEBAS= WHATSAPP_ATM=

# Comando: usar gunicorn con workers uvicorn
# Ajusta --workers según CPU disponibles (2*CPU+1). Coolify define WEB_CONCURRENCY a veces.
ENV PORT=8000

# Forma JSON evita problemas de signal handling y warnings (Docker best practice)
CMD ["bash","-c","exec gunicorn app:app --bind 0.0.0.0:${PORT} --workers ${WEB_CONCURRENCY:-2} --worker-class uvicorn.workers.UvicornWorker --timeout 60 --graceful-timeout 30 --log-level info"]
