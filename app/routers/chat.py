import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.security.auth import verify_internal_key
from app.services.llm_client import OpenRouterClientError, ask_openrouter, DEFAULT_TOOLS
from app.services.prompt_builder import build_prompt

router = APIRouter(prefix="/ai", tags=["chat"])
logger = logging.getLogger(__name__)


def _strip_code_fence(text: str) -> str:
    if not text.startswith("```"):
        return text
    stripped = text.split("\n", 1)[1] if "\n" in text else ""
    return stripped.rsplit("```", 1)[0].strip()


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_internal_key)])
def chat(request: ChatRequest) -> ChatResponse | JSONResponse:
    """Recibe el mensaje con contexto del proyecto y devuelve la respuesta del modelo."""
    prompt = build_prompt(request)
    target_model = (request.model or "primary").lower() if hasattr(request, "model") else "primary"
    tools = request.tools if request.tools is not None else DEFAULT_TOOLS
    try:
        raw_response = ask_openrouter(prompt, target_model, tools)
    except OpenRouterClientError as exc:
        logger.error("Error al consultar OpenRouter [%s]: %s", exc.error_code, exc.status_message)
        payload = ChatResponse(
            success=False,
            reply="",
            model=settings.get_model_name_for_key(target_model),
            fallback=False,
            level=settings.get_level_for_model(target_model),
            error_code=exc.error_code,
            http_status=exc.http_status or 503,
            provider=exc.provider,
            reason=exc.reason,
            retryable=exc.retryable,
            status_message=exc.status_message,
        )
        return JSONResponse(
            status_code=payload.http_status or 503,
            content=payload.model_dump(mode="json", exclude_none=True),
        )
    except Exception:
        logger.exception("Error inesperado al consultar OpenRouter")
        payload = ChatResponse(
            success=False,
            reply="",
            model=settings.get_model_name_for_key(target_model),
            fallback=False,
            level=settings.get_level_for_model(target_model),
            error_code="INTERNAL_AI_ERROR",
            http_status=500,
            provider="openrouter",
            reason="internal_ai_error",
            retryable=False,
            status_message="El servicio de IA no está disponible en este momento.",
        )
        return JSONResponse(
            status_code=500,
            content=payload.model_dump(mode="json", exclude_none=True),
        )

    text = (raw_response.get("text") or "").strip()
    actual_model = raw_response.get("model") or settings.get_model_name_for_key(target_model)
    fallback_used = bool(raw_response.get("fallback"))
    status_message = (
        "Se está usando el modelo principal de Syncra AI."
        if not fallback_used
        else f"Se activó fallback a {actual_model} porque el modelo principal no estaba disponible."
    )
    tool_calls = raw_response.get("tool_calls") or []
    usage = raw_response.get("usage")

    text = _strip_code_fence(text)

    if tool_calls:
        return ChatResponse(
            success=True,
            reply=text or "He recibido la necesidad de ejecutar una herramienta del backend.",
            tool_calls=tool_calls,
            model=actual_model,
            fallback=fallback_used,
            level=settings.get_level_for_model(target_model),
            usage=usage,
            status_message=status_message,
            provider="openrouter",
            http_status=200,
        )

    if text.strip().startswith("{"):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict) and (
            "reply" in parsed or "actions" in parsed or "suggested_card" in parsed
        ):
            reply_value = parsed.get("reply") or parsed.get("message") or "He completado la operación solicitada."
            return ChatResponse(
                success=True,
                reply=str(reply_value),
                suggested_card=parsed.get("suggested_card"),
                tool_calls=[],
                model=actual_model,
                fallback=fallback_used,
                level=settings.get_level_for_model(target_model),
                usage=usage,
                status_message=status_message,
                provider="openrouter",
                http_status=200,
            )

    try:
        parsed = json.loads(text)
        response = ChatResponse.model_validate(parsed)
        response.model = actual_model
        response.level = settings.get_level_for_model(actual_model)
        response.fallback = fallback_used
        response.status_message = status_message
        response.success = True
        response.provider = "openrouter"
        response.http_status = 200
        response.usage = usage
        return response
    except (json.JSONDecodeError, ValueError, TypeError):
        logger.debug("OpenRouter devolvió un formato no estructurado; se usa como respuesta textual")
        return ChatResponse(
            success=True,
            reply=text or "No pude generar una respuesta válida.",
            suggested_card=None,
            tool_calls=tool_calls,
            model=actual_model,
            fallback=fallback_used,
            level=settings.get_level_for_model(target_model),
            usage=usage,
            status_message=status_message,
            provider="openrouter",
            http_status=200,
        )