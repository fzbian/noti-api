from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import base64
import tempfile
import os
from dotenv import load_dotenv

from clients.whatsapp import check_number_exists, send_and_validate

load_dotenv()

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

class SendToNumberRequest(BaseModel):
    numero: str = Field(..., min_length=10, max_length=10, pattern=r"^\d{10}$", description="Número celular colombiano de 10 dígitos (sin prefijo)")
    mensaje: Optional[str] = Field(None, description="Mensaje de texto a enviar")
    pdf_base64: Optional[str] = Field(None, description="PDF en base64 (opcional)")
    pdf_nombre: Optional[str] = Field(None, description="Nombre del PDF (opcional)")
    caption: Optional[str] = Field(None, description="Caption para el PDF (opcional)")

class SendToNumberResponse(BaseModel):
    status: str
    detail: str
    name: Optional[str] = None
    pdf_file: Optional[str] = None

@router.post("/enviar", response_model=SendToNumberResponse)
def send_to_number(req: SendToNumberRequest):
    # 1. Validar número y obtener JID
    formatted = f"+57{req.numero}"
    try:
        data = check_number_exists(formatted)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error validando número: {e}")
    if not data or not data.get("exists"):
        raise HTTPException(status_code=404, detail="El número no existe en WhatsApp")
    jid = data.get("jid")
    name = data.get("name") or "No disponible"

    # 2. Enviar mensaje o PDF
    if req.pdf_base64:
        # Guardar PDF temporalmente
        try:
            pdf_bytes = base64.b64decode(req.pdf_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="PDF base64 inválido")
        pdf_nombre = req.pdf_nombre or "archivo.pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            pdf_path = tmp.name
        try:
            result = send_and_validate(
                jid,
                req.mensaje,
                file_path=pdf_path,
                file_name=pdf_nombre,
                caption=req.caption,
                attempts=6,
                delay_seconds=1.5,
                auto_caption=True,
            )
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        if result == "Mensaje enviado y validado":
            return SendToNumberResponse(status="ok", detail=result, name=name, pdf_file=pdf_nombre)
        raise HTTPException(status_code=400, detail=result)
    else:
        # Solo mensaje de texto
        if not req.mensaje:
            raise HTTPException(status_code=400, detail="Debes enviar un mensaje o un PDF")
        result = send_and_validate(jid, req.mensaje)
        if result == "Mensaje enviado y validado":
            return SendToNumberResponse(status="ok", detail=result, name=name)
        raise HTTPException(status_code=400, detail=result)
