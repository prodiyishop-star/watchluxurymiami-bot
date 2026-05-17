from .facebook import router as facebook_router
from .whatsapp import router as whatsapp_router
from .instagram import router as instagram_router
from .admin import router as admin_router

__all__ = ["facebook_router", "whatsapp_router", "instagram_router", "admin_router"]
