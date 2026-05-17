"""
Gestión de la base de datos.
Todas las operaciones de lectura y escritura pasan por aquí.
"""

from sqlalchemy import create_engine, select, and_, or_, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

from .models import Base, Customer, Conversation, Message, KnowledgeItem, BotLearning
from config.settings import settings


# Motor de base de datos
DATABASE_URL = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class DatabaseManager:

    async def initialize(self):
        """Crea las tablas si no existen."""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self):
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # ============ CLIENTES ============

    async def get_or_create_customer(self, platform: str, platform_user_id: str, name: str = None) -> Customer:
        async with self.session() as db:
            result = await db.execute(
                select(Customer).where(
                    and_(Customer.platform == platform, Customer.platform_user_id == platform_user_id)
                )
            )
            customer = result.scalar_one_or_none()

            if not customer:
                customer = Customer(
                    platform=platform,
                    platform_user_id=platform_user_id,
                    name=name or "Cliente",
                )
                db.add(customer)
                await db.flush()
            else:
                customer.last_seen = datetime.utcnow()
                if name and customer.name in (None, "Cliente"):
                    customer.name = name

            return customer

    async def update_customer_notes(self, customer_id: str, notes: str):
        async with self.session() as db:
            result = await db.execute(select(Customer).where(Customer.id == customer_id))
            customer = result.scalar_one_or_none()
            if customer:
                customer.notes = notes

    async def add_customer_tag(self, customer_id: str, tag: str):
        async with self.session() as db:
            result = await db.execute(select(Customer).where(Customer.id == customer_id))
            customer = result.scalar_one_or_none()
            if customer:
                tags = customer.tags or []
                if tag not in tags:
                    tags.append(tag)
                    customer.tags = tags

    # ============ CONVERSACIONES ============

    async def get_or_create_conversation(self, customer_id: str, platform: str) -> Conversation:
        """Obtiene la conversación activa o crea una nueva."""
        async with self.session() as db:
            # Buscar conversación activa reciente (últimas 24 horas)
            cutoff = datetime.utcnow() - timedelta(hours=24)
            result = await db.execute(
                select(Conversation).where(
                    and_(
                        Conversation.customer_id == customer_id,
                        Conversation.platform == platform,
                        Conversation.status == "active",
                        Conversation.last_message_at >= cutoff,
                    )
                ).order_by(desc(Conversation.last_message_at))
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                conversation = Conversation(
                    customer_id=customer_id,
                    platform=platform,
                )
                db.add(conversation)
                await db.flush()
            else:
                conversation.last_message_at = datetime.utcnow()

            return conversation

    # ============ MENSAJES ============

    async def save_message(
        self,
        conversation_id: str,
        customer_id: str,
        platform: str,
        sender: str,
        content: str,
        message_type: str = "text",
        platform_message_id: str = None,
    ) -> Message:
        async with self.session() as db:
            message = Message(
                conversation_id=conversation_id,
                customer_id=customer_id,
                platform=platform,
                sender=sender,
                content=content,
                message_type=message_type,
                platform_message_id=platform_message_id,
            )
            db.add(message)

            # Actualizar contador del cliente
            result = await db.execute(select(Customer).where(Customer.id == customer_id))
            customer = result.scalar_one_or_none()
            if customer:
                customer.total_messages = (customer.total_messages or 0) + 1

            return message

    async def get_conversation_history(
        self, conversation_id: str, limit: int = 20
    ) -> List[Dict]:
        """Obtiene el historial de mensajes de una conversación."""
        async with self.session() as db:
            result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(desc(Message.sent_at))
                .limit(limit)
            )
            messages = result.scalars().all()
            messages = list(reversed(messages))

            return [
                {
                    "role": "user" if m.sender == "customer" else "assistant",
                    "content": m.content,
                    "sent_at": m.sent_at.isoformat(),
                }
                for m in messages
            ]

    async def get_customer_history_summary(self, customer_id: str) -> str:
        """Resumen del historial completo del cliente para contexto."""
        async with self.session() as db:
            result = await db.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = result.scalar_one_or_none()
            if not customer:
                return ""

            # Últimas conversaciones
            conv_result = await db.execute(
                select(Conversation)
                .where(Conversation.customer_id == customer_id)
                .order_by(desc(Conversation.last_message_at))
                .limit(5)
            )
            conversations = conv_result.scalars().all()

            summary_parts = []
            if customer.name:
                summary_parts.append(f"Cliente: {customer.name}")
            if customer.tags:
                summary_parts.append(f"Etiquetas: {', '.join(customer.tags)}")
            if customer.notes:
                summary_parts.append(f"Notas: {customer.notes}")
            if customer.purchase_history:
                summary_parts.append(f"Historial de compras: {json.dumps(customer.purchase_history, ensure_ascii=False)}")
            if conversations:
                topics = [c.topic for c in conversations if c.topic]
                if topics:
                    summary_parts.append(f"Temas anteriores: {', '.join(topics)}")

            return "\n".join(summary_parts) if summary_parts else ""

    # ============ CONOCIMIENTO ============

    async def search_knowledge(self, query: str, category: str = None, limit: int = 5) -> List[KnowledgeItem]:
        """Busca en la base de conocimiento."""
        async with self.session() as db:
            conditions = [KnowledgeItem.is_active == True]
            if category:
                conditions.append(KnowledgeItem.category == category)

            result = await db.execute(
                select(KnowledgeItem).where(and_(*conditions)).limit(limit * 3)
            )
            items = result.scalars().all()

            # Búsqueda simple por palabras clave
            query_words = query.lower().split()
            scored = []
            for item in items:
                score = 0
                text = (item.title + " " + item.content + " " + " ".join(item.keywords or [])).lower()
                for word in query_words:
                    if word in text:
                        score += 1
                if score > 0:
                    scored.append((score, item))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [item for _, item in scored[:limit]]

    async def get_all_knowledge(self, category: str = None) -> List[KnowledgeItem]:
        async with self.session() as db:
            conditions = [KnowledgeItem.is_active == True]
            if category:
                conditions.append(KnowledgeItem.category == category)
            result = await db.execute(select(KnowledgeItem).where(and_(*conditions)))
            return result.scalars().all()

    async def save_knowledge_item(self, category: str, title: str, content: str, keywords: List[str] = None) -> KnowledgeItem:
        async with self.session() as db:
            item = KnowledgeItem(
                category=category,
                title=title,
                content=content,
                keywords=keywords or [],
            )
            db.add(item)
            return item

    # ============ APRENDIZAJE ============

    async def save_learning(self, context: str, response: str, feedback: str, corrected: str = None, platform: str = None):
        async with self.session() as db:
            learning = BotLearning(
                context=context,
                response=response,
                feedback=feedback,
                corrected_response=corrected,
                platform=platform,
            )
            db.add(learning)
