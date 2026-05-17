"""
Motor de respuestas — orquesta todo el proceso de generación.
1. Recupera historial del cliente
2. Busca información relevante del negocio
3. Construye el contexto completo
4. Genera la respuesta con Claude
5. Guarda todo en la base de datos
"""

import json
from typing import Optional
from pathlib import Path

from .claude_client import ClaudeClient
from .prompts import build_system_prompt, build_context_message
from database.manager import DatabaseManager
from config.settings import settings


class ResponseEngine:
    """Motor principal de respuestas del chatbot."""

    def __init__(self):
        self.claude = ClaudeClient()
        self.db = DatabaseManager()
        self._system_prompt_cache = None
        self._knowledge_cache = None

    async def process_message(
        self,
        platform: str,
        platform_user_id: str,
        message_text: str,
        user_name: str = None,
        platform_message_id: str = None,
    ) -> str:
        """
        Proceso completo: recibe mensaje → genera respuesta → guarda todo.
        Este es el método principal que llaman los webhooks.
        """

        # 1. Obtener/crear cliente
        customer = await self.db.get_or_create_customer(
            platform=platform,
            platform_user_id=platform_user_id,
            name=user_name,
        )

        # 2. Obtener/crear conversación activa
        conversation = await self.db.get_or_create_conversation(
            customer_id=customer.id,
            platform=platform,
        )

        # 3. Guardar mensaje del cliente
        await self.db.save_message(
            conversation_id=conversation.id,
            customer_id=customer.id,
            platform=platform,
            sender="customer",
            content=message_text,
            platform_message_id=platform_message_id,
        )

        # 4. Obtener historial de la conversación actual
        history = await self.db.get_conversation_history(
            conversation_id=conversation.id,
            limit=20,
        )

        # 5. Obtener resumen del historial del cliente (todas las conversaciones)
        customer_summary = await self.db.get_customer_history_summary(customer.id)

        # 6. Buscar información relevante del negocio
        relevant_knowledge = await self._search_relevant_knowledge(message_text)

        # 7. Construir el system prompt (con cache)
        system_prompt = await self._get_system_prompt()

        # 8. Construir el contexto del cliente
        context = build_context_message(
            customer_name=customer.name if customer.name != "Cliente" else user_name,
            customer_history=customer_summary if customer_summary else None,
            platform=platform,
            relevant_knowledge=relevant_knowledge if relevant_knowledge else None,
        )

        # 9. Convertir historial al formato de Claude (sin el último mensaje que acabamos de guardar)
        messages = self._build_messages_for_claude(history, message_text)

        # 10. Generar respuesta con Claude
        response_text = await self.claude.generate_response(
            messages=messages,
            system_prompt=system_prompt,
            context_message=context if context else None,
            max_tokens=1024,
        )

        # 11. Guardar respuesta del bot
        await self.db.save_message(
            conversation_id=conversation.id,
            customer_id=customer.id,
            platform=platform,
            sender="bot",
            content=response_text,
        )

        # 12. Actualizar tema de la conversación (en segundo plano)
        await self._update_conversation_topic(conversation.id, message_text, response_text)

        return response_text

    async def _get_system_prompt(self) -> str:
        """Obtiene el system prompt, cargando el conocimiento del negocio."""
        if self._system_prompt_cache:
            return self._system_prompt_cache

        knowledge = await self._load_knowledge_files()

        self._system_prompt_cache = build_system_prompt(
            business_info=knowledge.get("business_info", ""),
            products_info=knowledge.get("products", ""),
            faqs_info=knowledge.get("faqs", ""),
            policies_info=knowledge.get("policies", ""),
            style_examples=knowledge.get("style", ""),
        )

        return self._system_prompt_cache

    async def _load_knowledge_files(self) -> dict:
        """Carga los archivos de conocimiento del negocio."""
        base_path = Path("knowledge")
        result = {}

        files = {
            "products": "products.json",
            "faqs": "faqs.json",
            "policies": "policies.json",
            "style": "style_examples.json",
        }

        for key, filename in files.items():
            filepath = base_path / filename
            if filepath.exists():
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        result[key] = self._format_knowledge(key, data)
                except Exception:
                    result[key] = ""
            else:
                result[key] = ""

        return result

    def _format_knowledge(self, category: str, data: dict) -> str:
        """Convierte los archivos JSON de conocimiento a texto para el prompt."""
        if category == "products":
            lines = []
            for product in data.get("products", []):
                name = product.get("name", "")
                price = product.get("price", "")
                description = product.get("description", "")
                availability = product.get("availability", "disponible")
                line = f"• {name}"
                if price:
                    line += f" — ${price}"
                if description:
                    line += f": {description}"
                if availability:
                    line += f" ({availability})"
                lines.append(line)
            return "\n".join(lines)

        elif category == "faqs":
            lines = []
            for faq in data.get("faqs", []):
                q = faq.get("question", "")
                a = faq.get("answer", "")
                if q and a:
                    lines.append(f"P: {q}\nR: {a}")
            return "\n\n".join(lines)

        elif category == "policies":
            parts = []
            for key, value in data.items():
                if isinstance(value, str):
                    parts.append(f"• {key}: {value}")
                elif isinstance(value, list):
                    parts.append(f"• {key}: {', '.join(value)}")
            return "\n".join(parts)

        elif category == "style":
            examples = data.get("examples", [])
            if examples:
                lines = ["EJEMPLOS DE CÓMO RESPONDER:", ""]
                for ex in examples[:10]:  # máximo 10 ejemplos
                    q = ex.get("customer", "")
                    a = ex.get("response", "")
                    if q and a:
                        lines.append(f"Cliente: {q}")
                        lines.append(f"Tú: {a}")
                        lines.append("")
                return "\n".join(lines)

        return str(data)

    async def _search_relevant_knowledge(self, message: str) -> str:
        """Busca información relevante del negocio para el mensaje recibido."""
        items = await self.db.search_knowledge(message, limit=3)
        if not items:
            return ""

        parts = []
        for item in items:
            parts.append(f"[{item.category.upper()}] {item.title}:\n{item.content}")

        return "\n\n".join(parts)

    def _build_messages_for_claude(self, history: list, current_message: str) -> list:
        """
        Construye el array de mensajes para Claude.
        El historial ya incluye el mensaje actual (que guardamos antes).
        """
        # El historial incluye el mensaje actual al final (que acabamos de guardar)
        # Necesitamos asegurarnos que el formato sea correcto para Claude
        messages = []

        for msg in history:
            role = msg["role"]  # "user" o "assistant"
            content = msg["content"]
            messages.append({"role": role, "content": content})

        # Si el último mensaje no es del usuario, agregar el mensaje actual
        if not messages or messages[-1]["role"] != "user":
            messages.append({"role": "user", "content": current_message})

        return messages

    async def _update_conversation_topic(self, conversation_id: str, message: str, response: str):
        """Extrae y guarda el tema de la conversación."""
        try:
            topic_system = """Analiza el mensaje del cliente y responde SOLO con una de estas categorías:
precio, disponibilidad, envio, garantia, pago, devoluciones, informacion_producto,
consulta_general, queja, otro.
Responde solo la categoría, nada más."""

            topic = await self.claude.analyze_message(message, topic_system)
            topic = topic.strip().lower()

            async with self.db.session() as db:
                from database.models import Conversation
                from sqlalchemy import select
                result = await db.execute(
                    select(Conversation).where(Conversation.id == conversation_id)
                )
                conv = result.scalar_one_or_none()
                if conv:
                    conv.topic = topic
        except Exception:
            pass  # No crítico si falla

    def invalidate_system_prompt_cache(self):
        """Limpia el cache del system prompt (usar cuando se actualiza el conocimiento)."""
        self._system_prompt_cache = None
        self._knowledge_cache = None
