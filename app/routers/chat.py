from fastapi import APIRouter, Depends

from app.schemas.chat import ChatRequest, ChatResponse
from app.security.auth import verify_internal_key
from app.services.llm_client import ask_gemini
from app.services.prompt_builder import build_prompt

router = APIRouter(prefix="/ai", tags=["chat"])


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_internal_key)])
def chat(request: ChatRequest) -> ChatResponse:
    """
    Recibe un mensaje del aprendiz (ya reenviado por el backend Java,
    junto con el contexto del proyecto e historial) y devuelve la
    respuesta generada por la IA.

    Este endpoint NO guarda nada en base de datos. Guardar la conversacion
    y los mensajes (AiConversationEntity / AiMessageEntity) es
    responsabilidad del backend de Java.

    La deteccion y generacion de "suggested_card" (RF108) se agregara
    aqui mas adelante, cuando definan como identificar que el aprendiz
    quiere crear una tarea.
    """
    prompt = build_prompt(request)
    reply_text = ask_gemini(prompt)

    return ChatResponse(reply=reply_text, suggested_card=None)
