# Despliegue Docker / Coolify

## Build local
```bash
docker build -t noti-api .
```

## Ejecutar local
```bash
docker run --rm -p 8000:8000 --env-file .env noti-api
```

Endpoint salud:
```bash
curl http://localhost:8000/health
```

## docker compose
```bash
docker compose up --build
```

## Variables de entorno necesarias
Copiar `example.env` a `.env` y completar.

| Variable | Descripción |
|----------|-------------|
| ODOO_URL | URL base Odoo |
| ODOO_DB | Base de datos Odoo |
| ODOO_USERNAME | Usuario Odoo |
| ODOO_PASSWORD | Password Odoo |
| WHATSAPP_URL | URL base API WhatsApp bridge |
| WHATSAPP_INSTANCE | Identificador instancia |
| WHATSAPP_APIKEY | API key |
| WHATSAPP_TRASPASOS | JID/Número chat traspasos |
| WHATSAPP_PEDIDOS | JID/Número chat pedidos |
| WHATSAPP_PRUEBAS | JID/Número chat pruebas |
| WHATSAPP_ATM | JID/Número chat ATM |

## Producción (Coolify)
1. Crear nuevo servicio "Dockerfile" apuntando al repo.
2. Definir puerto interno `8000` (Coolify detectará el `EXPOSE`).
3. Configurar dominio + certificado (Coolify gestiona HTTPS y hace reverse proxy -> no modificar código).
4. Establecer variables de entorno (o cargar `.env`). No subir `.env` al repo.
5. Ajustar `WEB_CONCURRENCY` si se necesita más (fórmula recomendada: `2 * CPU + 1`).

Ejemplo variables adicionales en Coolify:
```
PORT=8000
WEB_CONCURRENCY=3
PYTHONUNBUFFERED=1
```

## Señales / Shutdown
Gunicorn recibe SIGTERM de Coolify y hace shutdown gracioso (`--graceful-timeout 30`).

## Logs
Ver logs directamente desde Coolify o:
```bash
docker logs -f noti-api
```

## Healthcheck
La ruta `/health` responde `{"status":"ok"}`. Coolify puede configurarse para usarla.

## Actualizaciones
Tras push en main (o branch configurada), Coolify puede auto deploy.

## Notas de seguridad
- No ejecutar como root (usuario `appuser`).
- No incluir `.env` en la imagen.
- Mantener dependencias actualizadas.

## Troubleshooting
| Problema | Posible causa | Solución |
|----------|---------------|----------|
| 502 Gateway | Puerto incorrecto | Verificar que servicio escuche en 8000 |
| Timeout | Lentos los endpoints | Aumentar `--timeout` en CMD Gunicorn |
| Vars vacías | No cargó .env | Revisar configuración de variables en Coolify |

## Extender
Si se requiere librería del sistema (ej. wkhtmltopdf) agregar en la sección apt-get del Dockerfile.
