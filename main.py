"""
CHATBOT - Punto de entrada principal
=====================================
Inicia el servidor y configura todo el sistema.
"""

import uvicorn
from server.app import create_app
from database.manager import DatabaseManager
from config.settings import settings

app = create_app()


async def startup():
    """Inicializa la base de datos al arrancar."""
    db = DatabaseManager()
    await db.initialize()
    print(f"✅ Base de datos inicializada")
    print(f"🤖 {settings.bot_name} listo para atender en {settings.business_name}")
    print(f"🌐 Servidor corriendo en http://{settings.host}:{settings.port}")


@app.on_event("startup")
async def on_startup():
    await startup()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )
