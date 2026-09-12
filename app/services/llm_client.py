"""Cliente central para OpenRouter con fallback multi-modelo."""

import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

MODEL_PRIORITY = ["primary", "secondary", "fallback"]

DEFAULT_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_project",
            "description": "Devuelve la información básica del proyecto actual, estado y contexto operativo.",
            "parameters": {
                "type": "object",
                "properties": {"project_id": {"type": "integer"}},
                "required": ["project_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_members",
            "description": "Lista los miembros del proyecto para identificar responsables seguros.",
            "parameters": {"type": "object", "properties": {"project_id": {"type": "integer"}}, "required": ["project_id"], "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_project_member",
            "description": "Busca un miembro por nombre o apellido usando coincidencia segura y aproximada.",
            "parameters": {"type": "object", "properties": {"project_id": {"type": "integer"}, "query": {"type": "string"}}, "required": ["project_id", "query"], "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tasks",
            "description": "Lista las tareas del proyecto para revisar estados, fechas, responsables y tablero.",
            "parameters": {"type": "object", "properties": {"project_id": {"type": "integer"}}, "required": ["project_id"], "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Crea una tarea real en el tablero del proyecto usando validación del backend.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "due_date": {"type": "string", "format": "date"},
                    "assigned_to": {"type": ["integer", "null"]},
                    "column_id": {"type": ["integer", "null"]},
                    "sprint_id": {"type": ["integer", "null"]},
                },
                "required": ["project_id", "title"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Actualiza una tarea existente y revalida permisos del proyecto.",
            "parameters": {"type": "object", "properties": {"project_id": {"type": "integer"}, "task_id": {"type": "integer"}, "title": {"type": "string"}, "description": {"type": "string"}, "due_date": {"type": "string", "format": "date"}, "assigned_to": {"type": ["integer", "null"]}}, "required": ["project_id", "task_id"], "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_task",
            "description": "Mueve una tarea a otra columna del tablero y reasigna posición si hace falta.",
            "parameters": {"type": "object", "properties": {"project_id": {"type": "integer"}, "task_id": {"type": "integer"}, "column_id": {"type": "integer"}, "position": {"type": ["integer", "null"]}}, "required": ["project_id", "task_id", "column_id"], "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_board_columns",
            "description": "Lista las columnas del tablero para reutilizar estados o crear nuevas si hace falta.",
            "parameters": {"type": "object", "properties": {"project_id": {"type": "integer"}}, "required": ["project_id"], "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_board_column",
            "description": "Crea una columna nueva en el tablero si no existe una compatible.",
            "parameters": {"type": "object", "properties": {"project_id": {"type": "integer"}, "name": {"type": "string"}, "color": {"type": "string"}}, "required": ["project_id", "name"], "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_documents",
            "description": "Lista documentos y actas del proyecto para consultar contenido o identificar la última acta relevante.",
            "parameters": {"type": "object", "properties": {"project_id": {"type": "integer"}}, "required": ["project_id"], "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_document",
            "description": "Consulta un documento concreto por id y devuelve su contenido principal.",
            "parameters": {"type": "object", "properties": {"project_id": {"type": "integer"}, "document_id": {"type": "integer"}}, "required": ["project_id", "document_id"], "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_acta",
            "description": "Consulta una acta concreta por id o título para analizar su contenido y convertirlo en tareas reales.",
            "parameters": {"type": "object", "properties": {"project_id": {"type": "integer"}, "document_id": {"type": ["integer", "null"]}, "title": {"type": ["string", "null"]}}, "required": ["project_id"], "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_actas",
            "description": "Lista las actas del proyecto para identificar la más reciente o la adecuada por tipo.",
            "parameters": {"type": "object", "properties": {"project_id": {"type": "integer"}}, "required": ["project_id"], "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_document",
            "description": "Crea un documento o acta real en la base de datos del proyecto usando servicios del backend.",
            "parameters": {"type": "object", "properties": {"project_id": {"type": "integer"}, "title": {"type": "string"}, "document_type": {"type": "string"}, "content": {"type": "string"}, "meeting_type": {"type": ["string", "null"]}}, "required": ["project_id", "title"], "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_document",
            "description": "Actualiza un documento existente solo si el usuario lo solicita explícitamente.",
            "parameters": {"type": "object", "properties": {"project_id": {"type": "integer"}, "document_id": {"type": "integer"}, "title": {"type": ["string", "null"]}, "content": {"type": ["string", "null"]}}, "required": ["project_id", "document_id"], "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_document",
            "description": "Elimina un documento solo si hay una intención explícita del usuario y el backend valida permisos.",
            "parameters": {"type": "object", "properties": {"project_id": {"type": "integer"}, "document_id": {"type": "integer"}}, "required": ["project_id", "document_id"], "additionalProperties": False},
        },
    },
]


class OpenRouterClientError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        error_code: str,
        http_status: int | None = None,
        provider: str = "openrouter",
        reason: str | None = None,
        retryable: bool = False,
        model: str | None = None,
        status_message: str | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.http_status = http_status
        self.provider = provider
        self.reason = reason or error_code
        self.retryable = retryable
        self.model = model
        self.status_message = status_message or message


def _build_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.OPENROUTER_HTTP_REFERER,
        "X-Title": settings.OPENROUTER_APP_TITLE,
    }


def _ordered_model_candidates(preferred_model: str | None) -> list[str]:
    requested = (preferred_model or "primary").lower()
    ordered: list[str] = []
    if requested in settings.MODELS:
        ordered.append(requested)
    for model_key in MODEL_PRIORITY:
        if model_key not in ordered:
            ordered.append(model_key)
    return ordered


def _extract_text(message: Any) -> str:
    if isinstance(message, str):
        return message.strip()
    if isinstance(message, dict):
        if "content" in message:
            return _extract_text(message["content"])
        if "text" in message:
            return str(message["text"]).strip()
    if isinstance(message, list):
        parts: list[str] = []
        for item in message:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                elif item.get("type") == "output_text":
                    parts.append(str(item.get("text", "")))
        if parts:
            return "".join(parts).strip()
    return ""


def _classify_http_error(exc: httpx.HTTPError, model_name: str) -> OpenRouterClientError:
    if isinstance(exc, httpx.TimeoutException):
        return OpenRouterClientError(
            f"OpenRouter tardó demasiado en responder para {model_name}.",
            error_code="TIMEOUT",
            http_status=408,
            provider="openrouter",
            reason="provider_timeout",
            retryable=True,
            model=model_name,
            status_message="El proveedor de IA tardó demasiado en responder. Reinténtalo en unos segundos.",
        )

    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code if exc.response is not None else 0
        payload: dict[str, Any] | None = None
        try:
            payload = exc.response.json() if exc.response is not None else None
        except ValueError:
            payload = None

        error_details = payload.get("error") if isinstance(payload, dict) and isinstance(payload.get("error"), dict) else {}
        message = str(error_details.get("message") or payload.get("message") or exc)
        if status_code == 401:
            return OpenRouterClientError(
                message or "La clave de OpenRouter no es válida.",
                error_code="INVALID_API_KEY",
                http_status=401,
                provider="openrouter",
                reason="invalid_api_key",
                retryable=False,
                model=model_name,
                status_message="La autenticación con el proveedor de IA no es válida. Contacta con el administrador del sistema.",
            )
        if status_code == 403:
            return OpenRouterClientError(
                message or "OpenRouter rechazó la solicitud por permisos.",
                error_code="FORBIDDEN",
                http_status=403,
                provider="openrouter",
                reason="forbidden",
                retryable=False,
                model=model_name,
                status_message="El proveedor de IA rechazó la solicitud por permisos.",
            )

        if status_code == 404:
            return OpenRouterClientError(
                message or f"El modelo {model_name} no existe en OpenRouter.",
                error_code="MODEL_NOT_FOUND",
                http_status=404,
                provider="openrouter",
                reason="model_not_found",
                retryable=True,
                model=model_name,
                status_message=f"El modelo {model_name} no está disponible. Se intentará con el siguiente.",
            )
        
        if status_code == 429:
            return OpenRouterClientError(
                message or "Se agotó la cuota del modelo actual.",
                error_code="RATE_LIMITED",
                http_status=429,
                provider="openrouter",
                reason="rate_limited",
                retryable=True,
                model=model_name,
                status_message="Se agotó la cuota del modelo activo. Se intentará con el siguiente modelo disponible.",
            )
        if status_code in {500, 502, 503, 504}:
            return OpenRouterClientError(
                message or "El proveedor de IA no está disponible en este momento.",
                error_code="PROVIDER_UNAVAILABLE",
                http_status=status_code,
                provider="openrouter",
                reason="provider_unavailable",
                retryable=True,
                model=model_name,
                status_message="El proveedor de IA está temporalmente caído o no responde. Inténtalo de nuevo en unos segundos.",
            )
        return OpenRouterClientError(
            message or f"OpenRouter devolvió un error HTTP {status_code} para {model_name}.",
            error_code="HTTP_ERROR",
            http_status=status_code,
            provider="openrouter",
            reason="http_error",
            retryable=status_code >= 500,
            model=model_name,
            status_message="El proveedor de IA respondió con un error no recuperable.",
        )

    return OpenRouterClientError(
        str(exc) or "Error de conexión con OpenRouter.",
        error_code="CONNECTION_ERROR",
        http_status=502,
        provider="openrouter",
        reason="connection_error",
        retryable=True,
        model=model_name,
        status_message="Hay un problema temporal de conexión con el proveedor de IA.",
    )


def _usage_payload(body: dict[str, Any]) -> dict[str, Any] | None:
    usage = body.get("usage") or {}
    if not usage:
        return None
    return {
        "prompt_tokens": usage.get("prompt_tokens") or usage.get("input_tokens"),
        "completion_tokens": usage.get("completion_tokens") or usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }


def _normalise_tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    tool_calls = message.get("tool_calls") or []
    if not tool_calls:
        return []

    normalised: list[dict[str, Any]] = []
    for item in tool_calls:
        if not isinstance(item, dict):
            continue
        func = item.get("function") or {}
        arguments = func.get("arguments") or {}
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        normalised.append({
            "id": item.get("id") or "call_1",
            "type": item.get("type") or "function",
            "function": {
                "name": func.get("name"),
                "arguments": arguments if isinstance(arguments, dict) else {"value": arguments},
            },
        })
    return normalised


def ask_openrouter(
    prompt: str,
    model_key: str | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        raise OpenRouterClientError(
            "OPENROUTER_API_KEY no configurada. Define la clave en el archivo .env del microservicio.",
            error_code="MISSING_API_KEY",
            http_status=500,
            provider="openrouter",
            reason="missing_api_key",
            retryable=False,
            model=settings.get_model_name_for_key(model_key or "primary"),
            status_message="La configuración del proveedor de IA no está preparada. Contacta con el administrador.",
        )

    active_tools = DEFAULT_TOOLS if tools is None else tools
    candidates = _ordered_model_candidates(model_key)
    last_index = len(candidates) - 1
    last_error: OpenRouterClientError | None = None

    for idx, candidate_key in enumerate(candidates):
        is_last = (idx == last_index)
        model_name = settings.get_model_name_for_key(candidate_key)

        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.35,
            "reasoning": {
                "effort": settings.OPENROUTER_REASONING_EFFORT,
                "exclude": True,
            },
        }
        if active_tools:
            payload["tools"] = active_tools
            payload["tool_choice"] = "auto"
        if settings.OPENROUTER_MAX_OUTPUT_TOKENS and settings.OPENROUTER_MAX_OUTPUT_TOKENS > 0:
            payload["max_tokens"] = settings.OPENROUTER_MAX_OUTPUT_TOKENS

        try:
            with httpx.Client(timeout=settings.OPENROUTER_TIMEOUT_SECONDS) as client:
                response = client.post(
                    f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                    headers=_build_headers(api_key),
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPError as exc:
            classified = _classify_http_error(exc, model_name)
            logger.warning(
                "OpenRouter fallo para modelo %s: %s (%s)",
                model_name, classified.error_code, classified.reason,
            )
            last_error = classified
            if not classified.retryable or is_last:
                raise classified
            continue

        choices = body.get("choices") or []
        if not choices:
            classified = OpenRouterClientError(
                f"OpenRouter no devolvió contenido válido para {model_name}.",
                error_code="EMPTY_RESPONSE",
                http_status=502,
                provider="openrouter",
                reason="empty_response",
                retryable=True,
                model=model_name,
                status_message="El proveedor de IA no devolvió respuesta útil. Reinténtalo en unos segundos.",
            )
            logger.warning("OpenRouter no devolvió contenido válido para %s", model_name)
            last_error = classified
            if is_last:
                raise classified
            continue

        message = choices[0].get("message", {})
        text = _extract_text(message)
        if not text:
            text = choices[0].get("text", "")

        tool_calls = _normalise_tool_calls(message)
        usage_payload = _usage_payload(body)
        fallback = (candidate_key != candidates[0]) if candidates else False

        if tool_calls:
            return {
                "text": text,
                "model": model_name,
                "requested_model": settings.get_model_name_for_key(model_key or "primary"),
                "fallback": fallback,
                "usage": usage_payload,
                "tool_calls": tool_calls,
            }

        if not text:
            classified = OpenRouterClientError(
                f"OpenRouter devolvió un texto vacío para {model_name}.",
                error_code="EMPTY_TEXT",
                http_status=502,
                provider="openrouter",
                reason="empty_text",
                retryable=True,
                model=model_name,
                status_message="El proveedor de IA devolvió un contenido vacío. Se reintentará con el siguiente modelo si está disponible.",
            )
            logger.warning("OpenRouter devolvió texto vacío para %s", model_name)
            last_error = classified
            if is_last:
                raise classified
            continue

        return {
            "text": text,
            "model": model_name,
            "requested_model": settings.get_model_name_for_key(model_key or "primary"),
            "fallback": fallback,
            "usage": usage_payload,
        }

    if last_error is not None:
        raise last_error
    raise OpenRouterClientError(
        "OpenRouter no devolvió una respuesta válida para ningún modelo configurado.",
        error_code="NO_MODELS_AVAILABLE",
        http_status=503,
        provider="openrouter",
        reason="no_models_available",
        retryable=True,
        model=settings.get_model_name_for_key(model_key or "primary"),
        status_message="No hay ningún modelo disponible para procesar la solicitud en este momento.",
    )


def ask_gemini(prompt: str) -> str:
    """Compatibilidad temporal: delega el mismo contrato a OpenRouter."""
    return ask_openrouter(prompt, "primary")["text"]