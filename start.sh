#!/usr/bin/env sh
set -e
# Permitimos que Coolify pase el puerto en $PORT
PORT="${PORT:-8000}"
# Opcional: activar reload sólo si DEBUG=1
if [ "${DEBUG}" = "1" ]; then
  echo "[start] Modo desarrollo con --reload en puerto ${PORT}"
  exec uvicorn app:app --host 0.0.0.0 --port "${PORT}" --reload
else
  echo "[start] Modo producción en puerto ${PORT}"
  exec uvicorn app:app --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS:-1}"
fi
