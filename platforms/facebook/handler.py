"""
Conector para Facebook Messenger y Marketplace.
Recibe mensajes del webhook de Facebook y responde vía Graph API.
"""

import httpx
from typing import Optional
from config.settings import settings
from platforms.base_platform import BasePlatform


class FacebookHandler(BasePlatform):
    """Maneja mensajes de Facebook Messenger y Marketplace."""

    GRAPH_API_URL = "https://graph.facebook.com/v19.0"

    def __init__(self):
        super().__init__()
        self.access_token = settings.facebook_page_access_token

    async def send_message(self, recipient_id: str, text: str) -> bool:
        """Envía un mensaje de texto via Messenger Send API."""
        if not self.access_token:
            print("⚠️  Facebook access token no configurado")
            return False

        url = f"{self.GRAPH_API_URL}/me/messages"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text},
            "messaging_type": "RESPONSE",
        }
        params = {"access_token": self.access_token}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, params=params)
                response.raise_for_status()
                return True
            except httpx.HTTPError as e:
                print(f"❌ Error enviando mensaje Facebook: {e}")
                return False

    async def process_webhook(self, data: dict) -> dict:
        """
        Procesa el payload del webhook de Facebook.
        Facebook envía un array de 'entry', cada uno con 'messaging'.
        """
        results = []

        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                result = await self._handle_messaging_event(messaging)
                if result:
                    results.append(result)

        return {"processed": len(results), "results": results}

    async def _handle_messaging_event(self, messaging: dict) -> Optional[dict]:
        """Procesa un evento individual de mensajería."""
        sender_id = messaging.get("sender", {}).get("id")
        if not sender_id:
            return None

        # Ignorar mensajes del propio bot (echo)
        if messaging.get("message", {}).get("is_echo"):
            return None

        # Mensaje de texto
        message = messaging.get("message", {})
        text = message.get("text", "").strip()

        if not text:
            # Puede ser imagen, sticker, etc. — responder genéricamente
            text = "[Imagen o archivo recibido]"

        # Obtener nombre del usuario si está disponible
        user_name = await self._get_user_name(sender_id)

        platform_message_id = message.get("mid")

        response = await self.handle_message(
            platform="facebook",
            platform_user_id=sender_id,
            message_text=text,
            user_name=user_name,
            platform_message_id=platform_message_id,
        )

        return {
            "sender_id": sender_id,
            "message": text,
            "response": response,
        }

    async def _get_user_name(self, user_id: str) -> Optional[str]:
        """Obtiene el nombre del usuario desde la Graph API."""
        if not self.access_token:
            return None

        url = f"{self.GRAPH_API_URL}/{user_id}"
        params = {
            "fields": "first_name,last_name",
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                data = response.json()
                first = data.get("first_name", "")
                last = data.get("last_name", "")
                name = f"{first} {last}".strip()
                return name if name else None
            except Exception:
                return None

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verifica el webhook de Facebook durante la configuración.
        Facebook envía mode=subscribe, verify_token, y challenge.
        Retorna el challenge si el token es correcto.
        """
        if mode == "subscribe" and token == settings.facebook_verify_token:
            return challenge
        return None
