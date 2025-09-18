from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import os
from clients.whatsapp import send_and_validate
from dotenv import load_dotenv

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

load_dotenv()

class SendTextRequest(BaseModel):
	chat: str = Field(..., description="Alias de chat: traspasos | pedidos | pruebas | atm")
	message: str = Field(..., description="Texto a enviar (siempre se valida envío)")


class SendTextResponse(BaseModel):
	status: str
	detail: str


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

@router.post("/send-text", response_model=SendTextResponse)
def send_text(req: SendTextRequest):
	try:
		jid = _resolve_chat(req.chat)
		result = send_and_validate(jid, req.message)
		if result == "Mensaje enviado y validado":
			return SendTextResponse(status="ok", detail=result)
		# cualquier otra cadena la tratamos como error
		raise HTTPException(status_code=400, detail=result)
	except HTTPException:
		raise
	except Exception as e:  # noqa: BLE001
		raise HTTPException(status_code=500, detail=str(e))

