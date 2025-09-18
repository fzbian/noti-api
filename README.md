# Noti API (FastAPI)

API para envío de mensajes de texto y PDF vía WhatsApp.

## Endpoints
- `GET /health` -> status
- `POST /whatsapp/send-text` -> `{ chat, message }`
- `POST /whatsapp/send-pdf`  -> `{ chat, pos_name, caption? }`

## Variables de entorno
Ejemplo en `example.env` (copiar a `.env` para desarrollo):

| Variable | Descripción |
|----------|-------------|
| PORT | Puerto (Coolify la inyecta automáticamente). Default 8000 |
| DEBUG | `1` para activar autoreload en contenedor (no recomendado prod) |
| WORKERS | Número de workers Uvicorn (default 1) |
| Cualquier otra | Usada por tu lógica (tokens, credenciales, etc.) |

## Ejecución local sin Docker
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

## Ejecución con Docker
Build local:
```bash
docker build -t noti-api:latest .
```
Run:
```bash
docker run --rm -p 8000:8000 --env-file .env noti-api:latest
```

## docker-compose
```bash
docker compose up --build
```
Acceder: http://localhost:8000/health

## Despliegue en Coolify
1. Crear un nuevo servicio tipo `Dockerfile` apuntando a este repo.
2. Coolify detectará el `Dockerfile` automáticamente.
3. Variables de entorno: cargar las necesarias (no subir `.env`).
4. Puerto interno expuesto: `8000` (Coolify configura el mapping externo automáticamente).
5. Opcional: establecer `WORKERS=2` o más según recursos.

### Healthcheck
La imagen define un `HEALTHCHECK` interno que consulta `GET /health`.

### Logs
FastAPI/Uvicorn escribe a stdout. Verlos en Coolify directamente.

## Actualizaciones
Tras hacer push a la rama seguida por Coolify, se reconstruirá la imagen y actualizará el contenedor.

## Seguridad / Mejores prácticas
- No incluir secretos en el repositorio.
- Usar variables de entorno en Coolify.
- Mantener dependencias actualizadas.

## Licencia
MIT (o la que definas).
