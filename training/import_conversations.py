"""
Importador de conversaciones reales.
Úsalo para entrenar al bot con tus conversaciones pasadas de Facebook/WhatsApp.

Uso:
    python -m training.import_conversations --file mis_conversaciones.json
"""

import json
import asyncio
import argparse
from pathlib import Path
from database.manager import DatabaseManager
from core.memory.knowledge_base import KnowledgeManager


class ConversationImporter:
    """Importa conversaciones reales para entrenar al bot."""

    def __init__(self):
        self.db = DatabaseManager()
        self.knowledge = KnowledgeManager()

    async def import_from_json(self, filepath: str):
        """
        Importa conversaciones desde un archivo JSON.

        Formato esperado:
        [
          {
            "customer": "Hola, ¿tienen el producto X?",
            "response": "Sí, tenemos! Cuesta $299. ¿Te interesa?"
          },
          ...
        ]
        """
        path = Path(filepath)
        if not path.exists():
            print(f"❌ Archivo no encontrado: {filepath}")
            return

        with open(path, "r", encoding="utf-8") as f:
            conversations = json.load(f)

        print(f"📂 Importando {len(conversations)} conversaciones...")

        imported = 0
        for conv in conversations:
            customer_msg = conv.get("customer", "")
            bot_response = conv.get("response", "")

            if customer_msg and bot_response:
                await self.db.save_learning(
                    context=customer_msg,
                    response=bot_response,
                    feedback="imported",
                )
                imported += 1

        print(f"✅ {imported} conversaciones importadas correctamente")

    async def import_products_from_csv(self, filepath: str):
        """
        Importa productos desde un CSV.
        Columnas esperadas: nombre, precio, descripcion, disponibilidad
        """
        import csv
        path = Path(filepath)
        if not path.exists():
            print(f"❌ Archivo no encontrado: {filepath}")
            return

        products = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                products.append({
                    "name": row.get("nombre", row.get("name", "")),
                    "price": row.get("precio", row.get("price", "")),
                    "description": row.get("descripcion", row.get("description", "")),
                    "availability": row.get("disponibilidad", row.get("availability", "disponible")),
                })

        await self.knowledge.import_products(products)
        print(f"✅ {len(products)} productos importados")

    async def import_faqs_from_json(self, filepath: str):
        """Importa FAQs desde JSON."""
        path = Path(filepath)
        if not path.exists():
            print(f"❌ Archivo no encontrado: {filepath}")
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        faqs = data if isinstance(data, list) else data.get("faqs", [])
        await self.knowledge.import_faqs(faqs)
        print(f"✅ {len(faqs)} FAQs importadas")


async def main():
    parser = argparse.ArgumentParser(description="Importar conversaciones al bot")
    parser.add_argument("--conversations", help="Archivo JSON con conversaciones")
    parser.add_argument("--products-csv", help="Archivo CSV con productos")
    parser.add_argument("--faqs", help="Archivo JSON con FAQs")
    args = parser.parse_args()

    importer = ConversationImporter()
    await importer.db.initialize()

    if args.conversations:
        await importer.import_from_json(args.conversations)
    if args.products_csv:
        await importer.import_products_from_csv(args.products_csv)
    if args.faqs:
        await importer.import_faqs_from_json(args.faqs)

    if not any([args.conversations, args.products_csv, args.faqs]):
        print("Uso: python -m training.import_conversations --conversations archivo.json")


if __name__ == "__main__":
    asyncio.run(main())
