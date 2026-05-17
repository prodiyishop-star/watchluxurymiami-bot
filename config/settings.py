"""
Configuración central del sistema.
Lee todas las variables del archivo .env
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Anthropic / Claude
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")

    # Facebook / Messenger
    facebook_page_access_token: str = Field("", env="FACEBOOK_PAGE_ACCESS_TOKEN")
    facebook_verify_token: str = Field("mi_token_secreto_123", env="FACEBOOK_VERIFY_TOKEN")
    facebook_app_secret: str = Field("", env="FACEBOOK_APP_SECRET")
    facebook_page_id: str = Field("", env="FACEBOOK_PAGE_ID")

    # WhatsApp
    whatsapp_access_token: str = Field("", env="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str = Field("", env="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_verify_token: str = Field("mi_token_whatsapp_123", env="WHATSAPP_VERIFY_TOKEN")
    whatsapp_business_account_id: str = Field("", env="WHATSAPP_BUSINESS_ACCOUNT_ID")

    # Instagram
    instagram_access_token: str = Field("", env="INSTAGRAM_ACCESS_TOKEN")
    instagram_verify_token: str = Field("mi_token_instagram_123", env="INSTAGRAM_VERIFY_TOKEN")
    instagram_business_account_id: str = Field("", env="INSTAGRAM_BUSINESS_ACCOUNT_ID")

    # Bot
    bot_name: str = Field("Asistente", env="BOT_NAME")
    business_name: str = Field("Mi Negocio", env="BUSINESS_NAME")
    owner_name: str = Field("Dueño", env="OWNER_NAME")
    timezone: str = Field("America/Mexico_City", env="TIMEZONE")
    language: str = Field("es", env="LANGUAGE")

    # Base de datos
    database_url: str = Field("sqlite:///./database/chatbot.db", env="DATABASE_URL")

    # Servidor
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    debug: bool = Field(False, env="DEBUG")

    # Seguridad
    secret_key: str = Field("cambia_esto", env="SECRET_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
