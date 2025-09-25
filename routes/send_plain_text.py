from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import os
from clients.whatsapp import send_and_validate
from dotenv import load_dotenv

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

load_dotenv()

class SendTextRequest(BaseModel):
	chat: str = Field(..., description="Alias de chat: traspasos | pedidos | pruebas | atm | cierres | retiradas")
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
	  atm       -> WHATSAPP_ATM
	  cierres   -> CHAT_CIERRES (o WHATSAPP_CIERRES)
	"""
	alias_l = alias.lower()
	mapping = {
		"traspasos": ["WHATSAPP_TRASPASOS"],
		"pedidos": ["WHATSAPP_PEDIDOS"],
		"pruebas": ["WHATSAPP_PRUEBAS"],
		"atm": ["WHATSAPP_ATM"],
		"cierres": ["CHAT_CIERRES", "WHATSAPP_CIERRES"],
		"retiradas": ["WHATSAPP_RETIRADAS"],
	}
	env_keys = mapping.get(alias_l)
	if not env_keys:
		raise HTTPException(status_code=400, detail=f"Alias desconocido: {alias}. Use: traspasos|pedidos|pruebas|atm|cierres|retiradas")
	for key in env_keys:
		value = os.getenv(key)
		if value:
			return value
	raise HTTPException(status_code=500, detail=f"Variables de entorno no definidas: {', '.join(env_keys)}")

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

