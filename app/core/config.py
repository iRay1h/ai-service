"""
Configuracion central del microservicio.

Todas las variables sensibles (API keys, secretos) se leen desde variables
de entorno, NUNCA se escriben directamente en el codigo.

En desarrollo local, estas variables se cargan desde un archivo .env
(ver .env.example en la raiz del proyecto).
"""

import os
from dotenv import load_dotenv

# Carga el archivo .env si existe (solo para desarrollo local).
# En produccion, las variables de entorno se configuran en el servidor
# o en el docker-compose, no en un archivo .env dentro del contenedor.
load_dotenv()


class Settings:
    # --- Proveedor de IA (Gemini) ---
    # API key generada en https://aistudio.google.com/apikey
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Modelo a usar. gemini-2.5-flash tiene capa gratuita generosa.
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # --- Seguridad interna ---
    # Clave secreta compartida entre el backend Java y este microservicio.
    # El backend debe enviarla en el header "X-Internal-Api-Key" en cada
    # request. Sin esta clave correcta, el microservicio rechaza la llamada.
    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY", "")

    # --- Configuracion del servidor ---
    APP_ENV: str = os.getenv("APP_ENV", "development")


settings = Settings()
