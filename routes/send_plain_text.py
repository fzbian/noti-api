from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import os
from dotenv import load_dotenv
from clients.whatsapp import send_and_validate

load_dotenv()

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

_CHAT_MAPPING = {
    "traspasos": ["WHATSAPP_TRASPASOS"],
    "pedidos": ["WHATSAPP_PEDIDOS"],
    "pruebas": ["WHATSAPP_PRUEBAS"],
    "atm": ["WHATSAPP_ATM"],
    "cierres": ["CHAT_CIERRES", "WHATSAPP_CIERRES"],
    "retiradas": ["WHATSAPP_RETIRADAS"],
}

def resolve_chat(alias: str) -> str:
    env_keys = _CHAT_MAPPING.get(alias.lower())
    if not env_keys:
        raise HTTPException(status_code=400, detail=f"Alias desconocido: {alias}. Use: {', '.join(_CHAT_MAPPING.keys())}")
    for key in env_keys:
        value = os.getenv(key)
        if value:
            return value
    raise HTTPException(status_code=500, detail=f"Variables de entorno no definidas: {', '.join(env_keys)}")

class SendTextRequest(BaseModel):
    chat: str = Field(..., description=f"Alias de chat: {', '.join(_CHAT_MAPPING.keys())}")
    message: str = Field(..., description="Texto a enviar (siempre se valida envío)")

class SendTextResponse(BaseModel):
    status: str
    detail: str

@router.post("/send-text", response_model=SendTextResponse)
def send_text(req: SendTextRequest):
    try:
        jid = resolve_chat(req.chat)
        result = send_and_validate(jid, req.message)
        if result == "Mensaje enviado y validado":
            return SendTextResponse(status="ok", detail=result)
        raise HTTPException(status_code=400, detail=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

