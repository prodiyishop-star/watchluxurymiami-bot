"""
Clase base para todos los conectores de plataformas.
Cada plataforma hereda de aquí para tener una interfaz consistente.
"""

from abc import ABC, abstractmethod
from typing import Optional
from core.ai.response_engine import ResponseEngine


class BasePlatform(ABC):
    """Interfaz base que deben implementar todas las plataformas."""

    def __init__(self):
        self.engine = ResponseEngine()

    @abstractmethod
    async def send_message(self, recipient_id: str, text: str) -> bool:
        """Envía un mensaje al usuario en la plataforma."""
        pass

    @abstractmethod
    async def process_webhook(self, data: dict) -> dict:
        """Procesa el payload entrante del webhook."""
        pass

    async def handle_message(
        self,
        platform: str,
        platform_user_id: str,
        message_text: str,
        user_name: str = None,
        platform_message_id: str = None,
    ) -> str:
        """
        Flujo estándar: genera respuesta con el motor de IA y la envía.
        Las subclases pueden sobreescribir para comportamiento especial.
        """
        response = await self.engine.process_message(
            platform=platform,
            platform_user_id=platform_user_id,
            message_text=message_text,
            user_name=user_name,
            platform_message_id=platform_message_id,
        )

        await self.send_message(platform_user_id, response)
        return response
