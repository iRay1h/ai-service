"""
Unico lugar del proyecto donde se llama al proveedor de IA (Gemini).

Si en el futuro quieren cambiar de proveedor (ej. probar otro modelo),
solo tocan este archivo. El resto del microservicio no deberia enterarse
de que proveedor se usa por debajo.
"""

from google import genai
from app.core.config import settings

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY no configurada. Copia .env.example a .env "
                "y pon tu API key (la generas gratis en https://aistudio.google.com/apikey)."
            )
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def ask_gemini(prompt: str) -> str:
    """
    Envia un prompt ya armado a Gemini y devuelve el texto de la respuesta.
    La construccion del prompt (con contexto, historial, instrucciones)
    se hace en services/prompt_builder.py, no aqui.
    """
    client = _get_client()
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
    )
    return response.text or ""
