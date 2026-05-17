"""
Gestión del estilo y personalidad del bot.
Aprende del historial de conversaciones para mejorar las respuestas.
"""

import json
from pathlib import Path
from typing import List
from database.manager import DatabaseManager


class PersonalityManager:
    """Gestiona la personalidad y aprende del estilo del dueño."""

    def __init__(self):
        self.db = DatabaseManager()
        self.style_path = Path("knowledge/style_examples.json")

    async def save_good_response(self, customer_message: str, bot_response: str):
        """Guarda una respuesta que fue buena para aprender de ella."""
        await self.db.save_learning(
            context=customer_message,
            response=bot_response,
            feedback="positive",
        )

    async def save_corrected_response(
        self,
        customer_message: str,
        bad_response: str,
        correct_response: str,
    ):
        """Guarda una corrección para que el bot aprenda."""
        await self.db.save_learning(
            context=customer_message,
            response=bad_response,
            feedback="corrected",
            corrected=correct_response,
        )
        # Agregar el ejemplo correcto al archivo de estilo
        await self._add_style_example(customer_message, correct_response)

    async def _add_style_example(self, customer_msg: str, bot_response: str):
        """Agrega un ejemplo al archivo de estilo para mejorar futuros prompts."""
        data = {"examples": []}
        if self.style_path.exists():
            with open(self.style_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        examples = data.get("examples", [])
        examples.append({
            "customer": customer_msg,
            "response": bot_response,
        })

        # Mantener máximo 50 ejemplos
        if len(examples) > 50:
            examples = examples[-50:]

        data["examples"] = examples
        with open(self.style_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_style_examples(self) -> List[dict]:
        """Carga los ejemplos de estilo actuales."""
        if not self.style_path.exists():
            return []
        with open(self.style_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("examples", [])
