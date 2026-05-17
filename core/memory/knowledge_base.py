"""
Gestión dinámica de la base de conocimiento.
Permite agregar, buscar y actualizar conocimiento del negocio en tiempo real.
"""

from typing import List, Optional
from database.manager import DatabaseManager


class KnowledgeManager:
    """Maneja la base de conocimiento del negocio almacenada en BD."""

    def __init__(self):
        self.db = DatabaseManager()

    async def add_item(
        self,
        category: str,
        title: str,
        content: str,
        keywords: List[str] = None,
    ):
        """Agrega un nuevo item de conocimiento."""
        return await self.db.save_knowledge_item(
            category=category,
            title=title,
            content=content,
            keywords=keywords or [],
        )

    async def search(self, query: str, category: str = None, limit: int = 5):
        """Busca conocimiento relevante para una consulta."""
        return await self.db.search_knowledge(query, category=category, limit=limit)

    async def get_all(self, category: str = None):
        """Obtiene todo el conocimiento, opcionalmente filtrado por categoría."""
        return await self.db.get_all_knowledge(category=category)

    async def import_products(self, products: List[dict]):
        """Importa lista de productos a la base de conocimiento."""
        for product in products:
            name = product.get("name", "")
            price = product.get("price", "")
            description = product.get("description", "")
            availability = product.get("availability", "disponible")

            content = f"Precio: ${price}\nDescripción: {description}\nDisponibilidad: {availability}"
            keywords = name.lower().split() + [str(price)]

            await self.add_item(
                category="producto",
                title=name,
                content=content,
                keywords=keywords,
            )

    async def import_faqs(self, faqs: List[dict]):
        """Importa preguntas frecuentes a la base de conocimiento."""
        for faq in faqs:
            question = faq.get("question", "")
            answer = faq.get("answer", "")
            if question and answer:
                keywords = question.lower().split()[:10]
                await self.add_item(
                    category="faq",
                    title=question,
                    content=answer,
                    keywords=keywords,
                )
