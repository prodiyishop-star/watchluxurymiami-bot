"""
Servidor FastAPI — recibe webhooks de todas las plataformas.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import facebook_router, whatsapp_router, instagram_router, admin_router
from database.manager import DatabaseManager


def create_app() -> FastAPI:
    """Crea y configura la aplicación FastAPI."""
    app = FastAPI(
        title="Chatbot Vendedor IA",
        description="Bot de ventas con IA para Facebook, WhatsApp e Instagram",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Registrar routers
    app.include_router(facebook_router, prefix="/webhook/facebook", tags=["Facebook"])
    app.include_router(whatsapp_router, prefix="/webhook/whatsapp", tags=["WhatsApp"])
    app.include_router(instagram_router, prefix="/webhook/instagram", tags=["Instagram"])
    app.include_router(admin_router, prefix="/admin", tags=["Admin"])

    @app.get("/")
    async def root():
        return {"status": "online", "message": "Bot vendedor activo 🤖"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app
