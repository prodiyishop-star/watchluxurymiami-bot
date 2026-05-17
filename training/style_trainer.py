"""
Entrenador de estilo — analiza tus conversaciones y extrae tu estilo de escritura.
Lee conversaciones reales y genera ejemplos para el archivo style_examples.json.

Uso:
    python -m training.style_trainer --analyze mis_chats.json
"""

import json
import asyncio
import argparse
from pathlib import Path
from typing import List


class StyleTrainer:
    """Extrae y aprende el estilo de escritura del dueño."""

    def __init__(self):
        self.style_path = Path("knowledge/style_examples.json")

    def analyze_chat_export(self, chat_text: str) -> List[dict]:
        """
        Analiza un export de WhatsApp/Facebook y extrae pares cliente-respuesta.
        Formato WhatsApp: "DD/MM/YYYY, HH:MM - Nombre: mensaje"
        """
        lines = chat_text.strip().split("\n")
        examples = []
        last_customer_msg = None
        owner_lines = []

        for line in lines:
            if " - " not in line:
                continue
            parts = line.split(" - ", 1)
            if len(parts) < 2:
                continue

            content = parts[1]
            if ": " not in content:
                continue

            sender, message = content.split(": ", 1)
            message = message.strip()

            if sender.lower() in ("yo", "owner", "tú", "tu", "mi negocio"):
                owner_lines.append(message)
            else:
                if owner_lines and last_customer_msg:
                    full_response = " ".join(owner_lines)
                    examples.append({
                        "customer": last_customer_msg,
                        "response": full_response,
                    })
                    owner_lines = []

                last_customer_msg = message

        return examples

    def add_examples_to_style(self, examples: List[dict], max_total: int = 50):
        """Agrega ejemplos al archivo de estilo, manteniendo los mejores."""
        existing = {"examples": []}
        if self.style_path.exists():
            with open(self.style_path, "r", encoding="utf-8") as f:
                existing = json.load(f)

        current = existing.get("examples", [])
        combined = current + examples

        if len(combined) > max_total:
            combined = combined[-max_total:]

        existing["examples"] = combined
        with open(self.style_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        print(f"✅ {len(examples)} ejemplos agregados. Total: {len(combined)}")

    def manually_add_example(self, customer_msg: str, your_response: str):
        """Agrega manualmente un ejemplo de cómo responderías."""
        self.add_examples_to_style([{
            "customer": customer_msg,
            "response": your_response,
        }])


async def main():
    parser = argparse.ArgumentParser(description="Entrenador de estilo del bot")
    parser.add_argument("--analyze", help="Archivo de chat exportado para analizar")
    parser.add_argument("--add-example", nargs=2, metavar=("CLIENTE", "RESPUESTA"),
                        help="Agrega un ejemplo manualmente")
    args = parser.parse_args()

    trainer = StyleTrainer()

    if args.analyze:
        path = Path(args.analyze)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            examples = trainer.analyze_chat_export(content)
            print(f"📊 Encontrados {len(examples)} pares de conversación")
            trainer.add_examples_to_style(examples)
        else:
            print(f"❌ Archivo no encontrado: {args.analyze}")

    elif args.add_example:
        customer, response = args.add_example
        trainer.manually_add_example(customer, response)
        print(f"✅ Ejemplo agregado al estilo del bot")

    else:
        print("Uso:")
        print('  python -m training.style_trainer --analyze mi_chat.txt')
        print('  python -m training.style_trainer --add-example "Hola, ¿tienen X?" "Sí! Cuesta $299"')


if __name__ == "__main__":
    asyncio.run(main())
