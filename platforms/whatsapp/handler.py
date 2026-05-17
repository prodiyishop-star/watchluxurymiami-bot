"""
Conector para WhatsApp Business API (Cloud API de Meta).
"""

import httpx
from typing import Optional
from config.settings import settings
from platforms.base_platform import BasePlatform


class WhatsAppHandler(BasePlatform):
    """Maneja mensajes de WhatsApp Business."""

    GRAPH_API_URL = "https://graph.facebook.com/v19.0"

    def __init__(self):
        super().__init__()
        self.access_token = settings.whatsapp_access_token
        self.phone_number_id = settings.whatsapp_phone_number_id

    async def send_message(self, recipient_phone: str, text: str) -> bool:
        """Envía un mensaje de texto via WhatsApp Cloud API."""
        if not self.access_token or not self.phone_number_id:
            print("⚠️  WhatsApp no configurado (access_token o phone_number_id faltante)")
            return False

        url = f"{self.GRAPH_API_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "text",
            "text": {"body": text},
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return True
            except httpx.HTTPError as e:
                print(f"❌ Error enviando mensaje WhatsApp: {e}")
                return False

    async def process_webhook(self, data: dict) -> dict:
        """Procesa el payload del webhook de WhatsApp."""
        results = []

        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                result = await self._handle_messages(value)
                if result:
                    results.extend(result)

        return {"processed": len(results), "results": results}

    async def _handle_messages(self, value: dict) -> list:
        """Extrae y procesa mensajes del payload de WhatsApp."""
        results = []
        messages = value.get("messages", [])
        contacts = {c["wa_id"]: c.get("profile", {}).get("name") for c in value.get("contacts", [])}

        for msg in messages:
            msg_type = msg.get("type", "")
            sender_phone = msg.get("from", "")

            if msg_type == "text":
                text = msg.get("text", {}).get("body", "").strip()
            elif msg_type == "image":
                text = "[Imagen recibida]"
            elif msg_type == "audio":
                text = "[Audio recibido]"
            else:
                continue

            if not text or not sender_phone:
                continue

            user_name = contacts.get(sender_phone)
            platform_message_id = msg.get("id")

            response = await self.handle_message(
                platform="whatsapp",
                platform_user_id=sender_phone,
                message_text=text,
                user_name=user_name,
                platform_message_id=platform_message_id,
            )

            results.append({
                "sender_phone": sender_phone,
                "message": text,
                "response": response,
            })

        return results

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verifica el webhook de WhatsApp (mismo mecanismo que Facebook)."""
        if mode == "subscribe" and token == settings.facebook_verify_token:
            return challenge
        return None
