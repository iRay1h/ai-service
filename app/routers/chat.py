import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.chat import ChatRequest, ChatResponse
from app.security.auth import verify_internal_key
from app.services.llm_client import ask_gemini
from app.services.prompt_builder import build_prompt

router = APIRouter(prefix="/ai", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_internal_key)])
def chat(request: ChatRequest) -> ChatResponse:
    """
    Recibe un mensaje del aprendiz (ya reenviado por el backend Java,
    junto con el contexto del proyecto e historial) y devuelve la
    respuesta generada por la IA.

    Este endpoint NO guarda nada en base de datos. Guardar la conversacion
    y los mensajes (AiConversationEntity / AiMessageEntity) es
    responsabilidad del backend de Java.

    La deteccion de "suggested_card" se realiza como propuesta estructurada;
    la tarjeta solo se crea después de una confirmación explícita en Angular.
    """
    prompt = build_prompt(request)
    try:
        raw_response = ask_gemini(prompt)
    except RuntimeError as exc:
        logger.error("Configuracion de Gemini invalida: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="El proveedor de IA no está configurado") from None
    except Exception:
        logger.exception("Error al consultar Gemini")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="El proveedor de IA no está disponible") from None
    try:
        normalized_response = raw_response.strip()
        if normalized_response.startswith("```"):
            normalized_response = normalized_response.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        parsed = json.loads(normalized_response)
        return ChatResponse.model_validate(parsed)
    except (json.JSONDecodeError, ValueError, TypeError):
        logger.warning("Gemini devolvio un formato no estructurado; se usa como respuesta textual")
        return ChatResponse(reply=raw_response.strip(), suggested_card=None)
