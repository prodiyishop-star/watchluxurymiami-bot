"""
Modelos de la base de datos.
Aquí se define toda la estructura de datos que el bot guarda.
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_id():
    return str(uuid.uuid4())


class Customer(Base):
    """Perfil de cada cliente que habla con el bot."""
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=generate_id)
    platform = Column(String, nullable=False)        # facebook, whatsapp, instagram
    platform_user_id = Column(String, nullable=False) # ID del usuario en la plataforma
    name = Column(String)                            # Nombre del cliente
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_messages = Column(Integer, default=0)
    notes = Column(Text)                             # Notas importantes sobre el cliente
    tags = Column(JSON, default=list)                # ["interesado", "comprador", "mayorista"]
    preferences = Column(JSON, default=dict)         # Preferencias del cliente
    purchase_history = Column(JSON, default=list)    # Historial de compras
    is_active = Column(Boolean, default=True)

    conversations = relationship("Conversation", back_populates="customer")
    messages = relationship("Message", back_populates="customer")


class Conversation(Base):
    """Cada sesión de conversación con un cliente."""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_id)
    customer_id = Column(String, ForeignKey("customers.id"))
    platform = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text)                           # Resumen de la conversación
    status = Column(String, default="active")        # active, closed, escalated
    topic = Column(String)                           # Tema principal (precio, disponibilidad, etc.)
    outcome = Column(String)                         # venta, consulta, sin_respuesta

    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """Cada mensaje individual enviado o recibido."""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_id)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    customer_id = Column(String, ForeignKey("customers.id"))
    platform = Column(String, nullable=False)
    sender = Column(String, nullable=False)          # "customer" o "bot"
    content = Column(Text, nullable=False)
    message_type = Column(String, default="text")    # text, image, audio, document
    sent_at = Column(DateTime, default=datetime.utcnow)
    was_helpful = Column(Boolean)                    # Para entrenar el bot
    platform_message_id = Column(String)             # ID del mensaje en la plataforma

    conversation = relationship("Conversation", back_populates="messages")
    customer = relationship("Customer", back_populates="messages")


class KnowledgeItem(Base):
    """Base de conocimiento del negocio (productos, FAQs, etc.)."""
    __tablename__ = "knowledge"

    id = Column(String, primary_key=True, default=generate_id)
    category = Column(String, nullable=False)        # producto, faq, politica, proceso
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    keywords = Column(JSON, default=list)            # Palabras clave para búsqueda
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_count = Column(Integer, default=0)         # Cuántas veces se usó
    helpfulness_score = Column(Float, default=0.0)   # Qué tan útil resultó


class BotLearning(Base):
    """Registro de aprendizaje del bot — qué funcionó y qué no."""
    __tablename__ = "bot_learning"

    id = Column(String, primary_key=True, default=generate_id)
    context = Column(Text)                           # El mensaje del cliente
    response = Column(Text)                          # Respuesta del bot
    feedback = Column(String)                        # good, bad, corrected
    corrected_response = Column(Text)                # La respuesta correcta (si fue corregida)
    created_at = Column(DateTime, default=datetime.utcnow)
    platform = Column(String)
