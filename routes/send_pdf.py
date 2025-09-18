from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
from typing import Optional
from services.pdf_service import generate_pdf, SessionNotFoundError, PDFGenerationError
from clients.whatsapp import send_and_validate

load_dotenv()

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

def _resolve_chat(alias: str) -> str:
    """Resuelve el alias a su número/JID usando variables de entorno.

    Alias soportados:
      traspasos -> WHATSAPP_TRASPASOS
      pedidos   -> WHATSAPP_PEDIDOS
      pruebas   -> WHATSAPP_PRUEBAS
    """
    alias_l = alias.lower()
    mapping = {
        "traspasos": "WHATSAPP_TRASPASOS",
        "pedidos": "WHATSAPP_PEDIDOS",
        "pruebas": "WHATSAPP_PRUEBAS",
        "atm": "WHATSAPP_ATM",
    }
    env_key = mapping.get(alias_l)
    if not env_key:
        raise HTTPException(status_code=400, detail=f"Alias desconocido: {alias}. Use: traspasos|pedidos|pruebas")
    value = os.getenv(env_key)
    if not value:
        raise HTTPException(status_code=500, detail=f"Variable de entorno {env_key} no definida")
    return value

class SendPDFRequest(BaseModel):
    chat: str = Field(..., description="Alias de chat: traspasos | pedidos | pruebas | atm")
    pos_name: str = Field(..., description="Nombre de la sesión POS (ej: POS/00025)")
    caption: Optional[str] = Field(None, description="Caption opcional. Si no se envía no se agrega caption.")

class SendPDFResponse(BaseModel):
    status: str
    detail: str
    pdf_file: Optional[str] = None

@router.post("/send-pdf", response_model=SendPDFResponse)
def send_pdf(req: SendPDFRequest):
    """Genera un PDF de cierre (usando generate_pdf) y lo envía a WhatsApp.

    Flujo:
      1. Resolver alias de chat a JID.
      2. Generar PDF con generate_pdf(req.pos_name) -> filename local.
      3. Construir ruta absoluta al PDF.
      4. Llamar send_and_validate con file_path y parámetros solicitados.

    Retorna status ok si el mensaje se validó correctamente.
    """
    try:
        jid = _resolve_chat(req.chat)
        try:
            filename = generate_pdf(req.pos_name)
        except SessionNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PDFGenerationError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Error inesperado generando PDF: {e}")

        abs_path = os.path.abspath(filename)
        caption = req.caption  # usar solo si viene

        result = send_and_validate(
            jid,
            None,
            file_path=abs_path,
            file_name=filename,
            caption=caption,
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
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))
