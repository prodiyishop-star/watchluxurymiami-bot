"""
Panel de administración — endpoints para gestionar el bot sin tocar código.
Permite ver conversaciones, agregar conocimiento, corregir respuestas, etc.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from database.manager import DatabaseManager
from core.memory.knowledge_base import KnowledgeManager
from core.personality.style import PersonalityManager
from core.ai.response_engine import ResponseEngine

router = APIRouter()
db = DatabaseManager()
knowledge = KnowledgeManager()
personality = PersonalityManager()
engine = ResponseEngine()


# ─── Modelos Pydantic ───────────────────────────────────────────────────────

class KnowledgeItemIn(BaseModel):
    category: str
    title: str
    content: str
    keywords: Optional[List[str]] = []


class CorrectionIn(BaseModel):
    customer_message: str
    bad_response: str
    correct_response: str


class TestMessageIn(BaseModel):
    message: str
    platform: str = "facebook"


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/status")
async def status():
    """Estado general del bot."""
    return {
        "status": "online",
        "message": "Panel de administración activo",
    }


@router.get("/knowledge")
async def list_knowledge(category: str = None):
    """Lista todo el conocimiento del negocio."""
    items = await knowledge.get_all(category=category)
    return [
        {
            "id": item.id,
            "category": item.category,
            "title": item.title,
            "content": item.content[:200],
            "keywords": item.keywords,
        }
        for item in items
    ]


@router.post("/knowledge")
async def add_knowledge(item: KnowledgeItemIn):
    """Agrega nuevo conocimiento al bot."""
    await knowledge.add_item(
        category=item.category,
        title=item.title,
        content=item.content,
        keywords=item.keywords,
    )
    # Limpiar cache del sistema para que el nuevo conocimiento se use
    engine.invalidate_system_prompt_cache()
    return {"status": "ok", "message": "Conocimiento agregado"}


@router.post("/correct")
async def correct_response(correction: CorrectionIn):
    """
    Corrige una respuesta del bot.
    El bot aprende del ejemplo correcto para el futuro.
    """
    await personality.save_corrected_response(
        customer_message=correction.customer_message,
        bad_response=correction.bad_response,
        correct_response=correction.correct_response,
    )
    engine.invalidate_system_prompt_cache()
    return {"status": "ok", "message": "Corrección guardada. El bot aprenderá de esto."}


@router.post("/test")
async def test_bot(body: TestMessageIn):
    """
    Prueba el bot con un mensaje sin enviarlo a ninguna plataforma.
    Útil para verificar respuestas antes de activar en producción.
    """
    response = await engine.process_message(
        platform=body.platform,
        platform_user_id="admin_test_user",
        message_text=body.message,
        user_name="Admin (Prueba)",
    )
    return {"message": body.message, "response": response}


@router.delete("/cache")
async def clear_cache():
    """Limpia el cache del sistema prompt (útil al actualizar archivos JSON)."""
    engine.invalidate_system_prompt_cache()
    return {"status": "ok", "message": "Cache limpiado"}
