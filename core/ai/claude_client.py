"""
Cliente de Claude AI — el cerebro del chatbot.
Usa Claude Opus 4.7 con:
- Prompt caching para el sistema (ahorra hasta 90% en costos)
- Streaming para respuestas en tiempo real
- Memoria de conversación
"""

import anthropic
from typing import List, Dict, AsyncGenerator
from config.settings import settings


class ClaudeClient:
    """
    Interfaz con la API de Claude.
    El prompt del sistema se cachea automáticamente para reducir costos.
    """

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-opus-4-7"
        self._cached_system_prompt = None

    async def generate_response(
        self,
        messages: List[Dict],
        system_prompt: str,
        context_message: str = None,
        max_tokens: int = 1024,
    ) -> str:
        """
        Genera una respuesta completa (sin streaming).
        Ideal para webhooks donde necesitas la respuesta completa antes de enviarla.
        """
        prepared_messages = self._prepare_messages(messages, context_message)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    # Cachear el sistema — se reutiliza en cada mensaje del mismo cliente
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=prepared_messages,
        )

        return response.content[0].text if response.content else ""

    async def generate_response_stream(
        self,
        messages: List[Dict],
        system_prompt: str,
        context_message: str = None,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        """
        Genera una respuesta en streaming (token por token).
        Ideal para mostrar respuestas en tiempo real.
        """
        prepared_messages = self._prepare_messages(messages, context_message)

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=prepared_messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def _prepare_messages(
        self,
        messages: List[Dict],
        context_message: str = None,
    ) -> List[Dict]:
        """
        Prepara los mensajes para la API de Claude.
        Agrega contexto del cliente si existe.
        """
        prepared = []

        # Si hay contexto del cliente, agrégralo al primer mensaje del usuario
        if context_message and messages:
            first_user_msg = None
            for i, msg in enumerate(messages):
                if msg["role"] == "user":
                    first_user_msg = i
                    break

            if first_user_msg is not None:
                messages = list(messages)  # copia
                messages[first_user_msg] = {
                    "role": "user",
                    "content": f"{context_message}\n\n---\n\nMensaje del cliente: {messages[first_user_msg]['content']}",
                }

        # Convertir al formato de Claude
        for msg in messages:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                prepared.append({
                    "role": msg["role"],
                    "content": str(msg["content"]),
                })

        # Claude requiere que el primer mensaje sea del usuario
        if not prepared or prepared[0]["role"] != "user":
            prepared.insert(0, {"role": "user", "content": "Hola"})

        return prepared

    async def analyze_message(self, message: str, system: str) -> str:
        """
        Análisis rápido de un mensaje (para extraer intención, tema, etc.)
        Usa Haiku para ser más económico en tareas simples de análisis.
        """
        response = await self.client.messages.create(
            model="claude-haiku-4-5-20251001",  # Más rápido y económico para análisis
            max_tokens=256,
            system=system,
            messages=[{"role": "user", "content": message}],
        )
        return response.content[0].text if response.content else ""
