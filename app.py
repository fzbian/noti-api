from fastapi import FastAPI
from dotenv import load_dotenv

# Cargar variables de entorno al iniciar (solo una vez)
load_dotenv()

from routes.send_plain_text import router as plain_text_router  # noqa: E402
from routes.send_pdf import router as pdf_router  # noqa: E402

app = FastAPI(title="Cierres API", version="0.1.0")

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

# Endpoints:
#  POST /whatsapp/send-text  {chat, message}
#  POST /whatsapp/send-pdf   {chat, pos_name, caption?}
# Ejecutar con:
# uvicorn app:app --reload --port 8000
