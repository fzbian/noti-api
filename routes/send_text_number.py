from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from clients.whatsapp import check_number_exists, send_and_validate
router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

class SendTextNumberRequest(BaseModel):
    numero: str = Field(..., min_length=10, max_length=10, pattern=r"^\d{10}$", description="Número celular colombiano de 10 dígitos (sin prefijo)")
    mensaje: str = Field(..., description="Mensaje de texto a enviar")

class SendTextNumberResponse(BaseModel):
    status: str
    detail: str
    name: Optional[str] = None

@router.post("/send-text-number", response_model=SendTextNumberResponse)
def send_text_number(req: SendTextNumberRequest):
    formatted = f"+57{req.numero}"
    try:
        data = check_number_exists(formatted)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error validando número: {e}")
    if not data or not data.get("exists"):
        raise HTTPException(status_code=404, detail="El número no existe en WhatsApp")
    jid = data.get("jid")
    name = data.get("name") or "No disponible"
    result = send_and_validate(jid, req.mensaje)
    if result == "Mensaje enviado y validado":
        return SendTextNumberResponse(status="ok", detail=result, name=name)
    raise HTTPException(status_code=400, detail=result)
