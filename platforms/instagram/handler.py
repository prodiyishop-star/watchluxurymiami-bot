"""
Conector para Instagram Direct Messages.
Usa la misma API de Graph que Facebook pero con endpoint de Instagram.
"""

import httpx
from typing import Optional
from config.settings import settings
from platforms.base_platform import BasePlatform


class InstagramHandler(BasePlatform):
    """Maneja mensajes de Instagram Direct."""

    GRAPH_API_URL = "https://graph.facebook.com/v19.0"

    def __init__(self):
        super().__init__()
        self.access_token = settings.instagram_access_token

    async def send_message(self, recipient_id: str, text: str) -> bool:
        """Envía un mensaje via Instagram Messaging API."""
        if not self.access_token:
            print("⚠️  Instagram access token no configurado")
            return False

        url = f"{self.GRAPH_API_URL}/me/messages"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text},
        }
        params = {"access_token": self.access_token}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, params=params)
                response.raise_for_status()
                return True
            except httpx.HTTPError as e:
                print(f"❌ Error enviando mensaje Instagram: {e}")
                return False

    async def process_webhook(self, data: dict) -> dict:
        """Procesa el payload del webhook de Instagram."""
        results = []

        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                result = await self._handle_messaging_event(messaging)
                if result:
                    results.append(result)

        return {"processed": len(results), "results": results}

    async def _handle_messaging_event(self, messaging: dict) -> Optional[dict]:
        """Procesa un evento de mensaje de Instagram."""
        sender_id = messaging.get("sender", {}).get("id")
        if not sender_id:
            return None

        message = messaging.get("message", {})

        if message.get("is_echo"):
            return None

        text = message.get("text", "").strip()
        if not text:
            attachments = message.get("attachments", [])
            if attachments:
                text = f"[{attachments[0].get('type', 'archivo').capitalize()} recibido]"
            else:
                return None

        platform_message_id = message.get("mid")

        response = await self.handle_message(
            platform="instagram",
            platform_user_id=sender_id,
            message_text=text,
            platform_message_id=platform_message_id,
        )

        return {
            "sender_id": sender_id,
            "message": text,
            "response": response,
        }

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verifica el webhook de Instagram."""
        if mode == "subscribe" and token == settings.facebook_verify_token:
            return challenge
        return None
