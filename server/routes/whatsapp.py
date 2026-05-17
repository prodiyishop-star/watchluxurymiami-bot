"""
Rutas del webhook de WhatsApp Business.
"""

from fastapi import APIRouter, Request, Response, Query
from platforms.whatsapp import WhatsAppHandler

router = APIRouter()
handler = WhatsAppHandler()


@router.get("")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Verificación del webhook de WhatsApp (mismo mecanismo que Facebook)."""
    challenge = handler.verify_webhook(
        mode=hub_mode or "",
        token=hub_verify_token or "",
        challenge=hub_challenge or "",
    )
    if challenge:
        return Response(content=challenge, media_type="text/plain")
    return Response(content="Forbidden", status_code=403)


@router.post("")
async def receive_message(request: Request):
    """Recibe mensajes de WhatsApp y responde automáticamente."""
    data = await request.json()
    result = await handler.process_webhook(data)
    return {"status": "ok", **result}
