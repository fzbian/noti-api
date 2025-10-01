from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import os
from dotenv import load_dotenv
from services.pdf_service import generate_pdf, SessionNotFoundError, PDFGenerationError
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

class SendPDFRequest(BaseModel):
    chat: str = Field(..., description=f"Alias de chat: {', '.join(_CHAT_MAPPING.keys())}")
    pos_name: str = Field(..., description="Nombre de la sesión POS (ej: POS/00025)")
    caption: Optional[str] = Field(None, description="Caption opcional. Si no se envía no se agrega caption.")

class SendPDFResponse(BaseModel):
    status: str
    detail: str
    pdf_file: Optional[str] = None

@router.post("/send-pdf", response_model=SendPDFResponse)
def send_pdf(req: SendPDFRequest):
    try:
        jid = resolve_chat(req.chat)
        try:
            filename = generate_pdf(req.pos_name)
        except (SessionNotFoundError, PDFGenerationError) as e:
            raise HTTPException(status_code=500 if isinstance(e, PDFGenerationError) else 404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error inesperado generando PDF: {e}")

        abs_path = os.path.abspath(filename)
        result = send_and_validate(
            jid,
            None,
            file_path=abs_path,
            file_name=filename,
            caption=req.caption,
            attempts=6,
            delay_seconds=1.5,
            auto_caption=False,
        )
        if result == "Mensaje enviado y validado":
            try:
                if os.path.exists(abs_path):
                    os.remove(abs_path)
            except Exception:
                pass
            return SendPDFResponse(status="ok", detail=result, pdf_file=abs_path)
        raise HTTPException(status_code=400, detail=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
