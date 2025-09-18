from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi import Request
from fastapi.responses import JSONResponse
import os
from fastapi.middleware.cors import CORSMiddleware

# Cargar variables de entorno al iniciar (solo una vez)
load_dotenv()

from routes.send_plain_text import router as plain_text_router  # noqa: E402
from routes.send_pdf import router as pdf_router  # noqa: E402

app = FastAPI(title="Cierres API", version="0.1.0")

# CORS
_default_origins = ["http://localhost:3000"]
_env_origins = os.getenv("CORS_ORIGINS")  # separado por comas si se usa
if _env_origins:
    origins = [o.strip() for o in _env_origins.split(",") if o.strip()]
else:
    origins = _default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

APP_DEBUG = os.getenv("APP_DEBUG", "0") in {"1", "true", "True", "yes", "on"}

@app.middleware("http")
async def log_errors(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:  # noqa: BLE001
        if APP_DEBUG:
            # Log detallado a stdout (lo capta Coolify)
            import traceback
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={
                    "error": str(e),
                    "path": request.url.path,
                    "detail": "Exception interceptada por middleware",
                },
            )
        raise

app.include_router(plain_text_router)
app.include_router(pdf_router)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    """Endpoint raíz simple para verificar que el proxy llega a la app.

    Útil cuando el reverse proxy (Coolify/Traefik) devuelve mensajes como
    "No available server" o 502 y se necesita confirmar conectividad.
    """
    return {"service": app.title, "version": app.version, "status": "ok"}

@app.get("/_debug/env")
async def debug_env():
    if not APP_DEBUG:
        return JSONResponse(status_code=403, content={"detail": "Activar APP_DEBUG para ver esto"})
    keys = [
        "ODOO_URL","ODOO_DB","ODOO_USERNAME","WHATSAPP_URL","WHATSAPP_INSTANCE",
        "WHATSAPP_APIKEY","WHATSAPP_TRASPASOS","WHATSAPP_PEDIDOS","WHATSAPP_PRUEBAS","WHATSAPP_ATM"
    ]
    snapshot = {k: ("<set>" if os.getenv(k) else None) for k in keys}
    return {"env": snapshot, "debug": True}

# Endpoints:
#  POST /whatsapp/send-text  {chat, message}
#  POST /whatsapp/send-pdf   {chat, pos_name, caption?}
# Ejecutar con:
# uvicorn app:app --reload --port 8000
