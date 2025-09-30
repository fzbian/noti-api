"""Funciones mínimas para interactuar con la API WhatsApp.

Incluye:
        send_message(number, text) -> str (devuelve key.id)
        validate_message(remote_jid) -> str (devuelve key.id del último mensaje)
        send_and_validate(remote_jid, message) -> str (mensaje de estado)

Uso:
    from clients.whatsapp import send_message
    message_id = send_message("120363403555103807@g.us", "prueba")
    print(message_id)

Variables de entorno requeridas:
    WHATSAPP_APIKEY (o WHATSAPP_API_KEY) -> apikey (obligatoria)
    WHATSAPP_INSTANCE                   -> nombre de instancia (ej: daniela)
Opcional:
    WHATSAPP_URL (o WHATSAPP_API_BASE)  -> base URL (default https://wpp-api.chinatownlogistic.com)

Errores:
    ValueError si faltan datos
    httpx.HTTPStatusError si la API responde != 2xx
    RuntimeError si la respuesta no contiene key.id
"""

import os
import time
import httpx
from typing import Optional, Tuple

def _get_config() -> Tuple[str, str, str]:
    """Obtiene (api_key, instance, base_url) validando presencia requerida."""
    api_key = os.getenv("WHATSAPP_APIKEY") or os.getenv("WHATSAPP_API_KEY")
    instance = os.getenv("WHATSAPP_INSTANCE")
    base = os.getenv("WHATSAPP_URL") or os.getenv("WHATSAPP_API_BASE") or "https://wpp-api.chinatownlogistic.com"
    if not api_key:
        raise ValueError("Falta WHATSAPP_APIKEY / WHATSAPP_API_KEY en entorno")
    if not instance:
        raise ValueError("Falta WHATSAPP_INSTANCE en entorno")
    return api_key, instance, base.rstrip('/')

def check_number_exists(full_number: str) -> Optional[dict]:
    """Consulta si un número existe en WhatsApp usando la API oficial.

    Args:
        full_number: Número en formato internacional (+57...).

    Returns:
        Dict con los datos retornados por la API (jid, exists, number, name, etc)
        o None si la lista viene vacía.

    Raises:
        ValueError: Si no se proporcionó el número.
        RuntimeError: Si la API responde con error o formato inesperado.
    """
    if not full_number:
        raise ValueError("'full_number' es requerido")

    api_key, instance, base = _get_config()
    url = f"{base}/chat/whatsappNumbers/{instance}"
    payload = {"numbers": [full_number]}
    headers = {"Content-Type": "application/json", "apikey": api_key}

    resp = httpx.post(url, json=payload, headers=headers, timeout=10.0)
    if resp.status_code >= 400:
        detail = None
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(f"Error HTTP {resp.status_code} al validar número: {detail}")

    data = resp.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Formato inesperado en respuesta: {data}")
    if not data:
        return None
    return data[0]

def send_message(number: str, text: Optional[str], *, file_path: Optional[str] = None, file_name: Optional[str] = None, caption: Optional[str] = None, media_type: str = "document", debug: bool = False, auto_caption: bool = True) -> str:
    """Envía un mensaje de texto o un documento PDF.

    Modos:
      - Texto: POST /message/sendText/{instance} con payload {number, text}.
      - Media (PDF): POST /message/sendMedia/{instance} con payload plano
          {
            "number": ..., "mediatype": "document", "fileName": "archivo.pdf",
            "caption": "...", "media": "<base64>"
          }

    Parámetros:
      number: JID destino (ej: 1203...@g.us)
      text: Texto del mensaje (o usado como caption si no se pasa 'caption')
      file_path: Ruta local PDF. Si se provee activa modo media.
      file_name: Nombre visible (default: basename del PDF). Se fuerza la extensión .pdf.
      caption: Texto acompañante (default: text o file_name)
      media_type: Valor para 'mediatype' (default document)
      debug: Si True retorna JSON completo (str) en lugar de key.id

    Retorna:
      key.id del mensaje o JSON (str) si debug=True.
    """
    if not number:
        raise ValueError("'number' es requerido")
    if file_path is None and not text:
        raise ValueError("Para mensajes de texto se requiere 'text'")
    # Para media: se permite que no haya text ni caption; si auto_caption=True se generará fallback.

    api_key, instance, base = _get_config()
    headers = {"Content-Type": "application/json", "apikey": api_key}

    # Modo media (PDF)
    if file_path:
        import base64
        import pathlib

        p = pathlib.Path(file_path)
        if not p.exists() or not p.is_file():
            raise ValueError(f"Archivo no encontrado: {file_path}")
        if p.suffix.lower() != ".pdf":
            raise ValueError("Solo se soportan PDFs (.pdf)")
        file_name = file_name or p.name
        with p.open("rb") as f:
            raw_b64 = base64.b64encode(f.read()).decode("utf-8")
        # Algunas APIs requieren el prefijo data URI; probamos ambos: enviamos solo base64 sin prefijo por defecto.
        b64_data = raw_b64
        url = f"{base}/message/sendMedia/{instance}"
        filename_pdf = file_name if file_name.lower().endswith('.pdf') else f"{file_name}.pdf"
        payload = {
            "number": number,
            "mediatype": media_type,  # esperado según implementación anterior
            "fileName": filename_pdf,
            "media": b64_data,
        }
        # Solo agregar caption si usuario la dio o si auto_caption activa fallback
        effective_caption = caption if caption is not None else (filename_pdf if auto_caption and text is None else text)
        if effective_caption:
            payload["caption"] = effective_caption
    else:
        # Texto plano
        url = f"{base}/message/sendText/{instance}"
        payload = {"number": number, "text": text}

    resp = httpx.post(url, json=payload, headers=headers, timeout=20.0)
    if resp.status_code >= 400:
        detail = None
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(f"Error HTTP {resp.status_code} al enviar mensaje: {detail}")
    data = resp.json()
    if debug:
        # Retornar JSON completo (como string) si se requiere depurar
        return str(data)
    message_id = data.get("key", {}).get("id")
    if not message_id:
        raise RuntimeError(f"La respuesta no contiene key.id: {data}")
    return message_id

def validate_message(remote_jid: str) -> str:
    """Devuelve el ID (key.id) del último mensaje para un remoteJid.

    Realiza POST a /chat/findMessages/{instance} y toma el primer elemento de
    messages.records (la API parece ordenar descendente por timestamp).
    Lanza RuntimeError si no se encuentra al menos un registro o falta key.id.
    """
    if not remote_jid:
        raise ValueError("'remote_jid' es requerido")
    api_key, instance, base = _get_config()
    url = f"{base}/chat/findMessages/{instance}"
    payload = {"where": {"key": {"remoteJid": remote_jid}}}
    headers = {"Content-Type": "application/json", "apikey": api_key}
    resp = httpx.post(url, json=payload, headers=headers, timeout=10.0)
    resp.raise_for_status()
    data = resp.json()
    try:
        records = data["messages"]["records"]
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Formato inesperado en respuesta: {data}") from e
    if not records:
        raise RuntimeError("No hay mensajes en records")
    first = records[0]
    message_id = first.get("key", {}).get("id")
    if not message_id:
        raise RuntimeError(f"El primer registro no contiene key.id: {first}")
    return message_id

def send_and_validate(
    remote_jid: str,
    message: Optional[str],
    *,
    file_path: Optional[str] = None,
    file_name: Optional[str] = None,
    caption: Optional[str] = None,
    media_type: str = "document",
    attempts: int = 5,
    delay_seconds: float = 1.0,
    auto_caption: bool = True,
) -> str:
    """Envía un mensaje (texto o PDF) y valida que aparezca como el último.

    Proceso:
      1. Envío vía send_message (soporta file_path para PDF).
      2. Reintenta validate_message hasta 'attempts' veces, esperando 'delay_seconds' entre cada intento.
      3. Compara el id enviado con el recuperado.

    Parámetros adicionales:
      file_path/file_name/caption/media_type: mismos que en send_message.
      attempts: número máximo de verificaciones (>=1).
      delay_seconds: pausa entre verificaciones (>=0).

    Retorna:
      "Mensaje enviado y validado" si coincide el ID.
      Cadena de error descriptiva en caso contrario.
    """
    if attempts < 1:
        return "Valor inválido: attempts debe ser >= 1"
    try:
        sent_id = send_message(
            remote_jid,
            message,
            file_path=file_path,
            file_name=file_name,
            caption=caption,
            media_type=media_type,
            auto_caption=auto_caption,
        )
    except Exception as e:  # noqa: BLE001
        return f"Error al enviar: {e}"

    for attempt in range(1, attempts + 1):
        time.sleep(delay_seconds if attempt > 1 else delay_seconds)  # esperar también después del primer envío
        try:
            last_id = validate_message(remote_jid)
        except Exception as e:  # noqa: BLE001
            if attempt == attempts:
                return f"Error al validar (intento {attempt}/{attempts}): {e}"
            continue
        if sent_id == last_id:
            return "Mensaje enviado y validado"
    return f"IDs no coinciden tras {attempts} intentos: enviado={sent_id} ultimo={last_id}"

__all__ = ["send_message", "validate_message", "send_and_validate", "check_number_exists"]
