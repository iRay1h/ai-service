"""
Configuracion central del microservicio.

Todas las variables sensibles (API keys, secretos) se leen desde variables
de entorno, NUNCA se escriben directamente en el codigo.

En desarrollo local, estas variables se cargan desde un archivo .env.
"""

import os
from typing import Dict

from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_TIMEOUT_SECONDS: float = float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "90"))
    OPENROUTER_MAX_OUTPUT_TOKENS: int = int(os.getenv("OPENROUTER_MAX_OUTPUT_TOKENS", "0"))
    OPENROUTER_REASONING_EFFORT: str = os.getenv("OPENROUTER_REASONING_EFFORT", "low")
    OPENROUTER_HTTP_REFERER: str = os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost:8000")
    OPENROUTER_APP_TITLE: str = os.getenv("OPENROUTER_APP_TITLE", "Syncra AI")

    MODELS: Dict[str, Dict[str, str]] = {
        "primary": {
            "name": os.getenv("OPENROUTER_MODEL_PRIMARY", "nvidia/nemotron-3-ultra-550b-a55b:free"),
            "label": "advanced",
        },
        "secondary": {
            "name": os.getenv("OPENROUTER_MODEL_SECONDARY", "nvidia/nemotron-3-super-120b-a12b:free"),
            "label": "standard",
        },
        "fallback": {
            "name": os.getenv("OPENROUTER_MODEL_FALLBACK", "nvidia/nemotron-nano-9b-v2:free"),
            "label": "basic",
        },
    }

    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY") or os.getenv("AI_INTERNAL_API_KEY", "")
    AI_INTERNAL_API_KEY: str = os.getenv("AI_INTERNAL_API_KEY") or os.getenv("INTERNAL_API_KEY", "")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    @classmethod
    def get_api_key_for_model(cls, model_key: str | None) -> str:
        return cls.OPENROUTER_API_KEY

    @classmethod
    def get_model_name_for_key(cls, model_key: str | None) -> str:
        return cls.MODELS.get((model_key or "primary").lower(), cls.MODELS["primary"]).get("name", cls.MODELS["primary"]["name"])

    @classmethod
    def get_level_for_model(cls, model_key: str | None) -> str:
        return cls.MODELS.get((model_key or "primary").lower(), cls.MODELS["primary"]).get("label", "advanced")


settings = Settings()
