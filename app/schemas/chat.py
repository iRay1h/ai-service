"""
Estos son los "moldes" de los datos que entran y salen del microservicio.
Son el equivalente a los DTOs que ya usan en el backend de Java.

IMPORTANTE: cuando definan el contrato final con el backend, estos campos
deben coincidir con lo que el AiClient de Java va a mandar.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ProjectContext(BaseModel):
    """
    Contexto del proyecto que el backend le manda a la IA (RF107),
    para que pueda responder con informacion real y no inventada.
    """
    project_id: int
    project_name: str
    active_sprint_name: Optional[str] = None
    pending_tasks_summary: Optional[str] = None
    members: list[dict] = Field(default_factory=list)
    columns: list[dict] = Field(default_factory=list)
    tasks: list[dict] = Field(default_factory=list)
    sprints: list[dict] = Field(default_factory=list)
    documents: list[dict] = Field(default_factory=list)
    current_user_id: Optional[int] = None
    current_user_name: Optional[str] = None


class ChatHistoryItem(BaseModel):
    role: str  # "USER" o "ASSISTANT", igual que el enum AiRoleEnum de Java
    content: str


class ToolCallFunction(BaseModel):
    name: str
    arguments: dict = Field(default_factory=dict)


class ToolCall(BaseModel):
    id: Optional[str] = None
    type: str = "function"
    function: ToolCallFunction


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32000)
    context: Optional[ProjectContext] = None
    history: list[ChatHistoryItem] = Field(default_factory=list)
    model: Optional[str] = None
    tools: Optional[list[dict]] = None


class SuggestedCard(BaseModel):
    """
    Propuesta de tarjeta Kanban generada por la IA (RF108).
    El aprendiz debe confirmarla antes de que el backend la cree de verdad (RF109).
    Este microservicio SOLO propone, nunca crea la tarjeta en la base de datos.
    """
    title: str
    description: Optional[str] = None
    suggested_priority: Optional[str] = None  # ej: "ALTA", "MEDIA", "BAJA"
    column_id: Optional[int] = None
    assigned_to: Optional[int] = None
    due_date: Optional[str] = None


class AiAction(BaseModel):
    type: str = Field(alias="action")
    task_id: Optional[int] = None
    document_id: Optional[int] = None
    project_id: Optional[int] = None
    column_id: Optional[int] = None
    assigned_to: Optional[int] = None
    sprint_id: Optional[int] = None
    position: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    document_type: Optional[str] = None
    color: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None

    model_config = {"populate_by_name": True}


class ChatResponse(BaseModel):
    success: bool = True
    reply: str = ""
    suggested_card: Optional[SuggestedCard] = None
    actions: list[AiAction] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: Optional[dict] = None
    model: Optional[str] = None
    fallback: bool = False
    level: Optional[str] = None
    quota: Optional[dict] = None
    status_message: Optional[str] = None
    error_code: Optional[str] = None
    http_status: Optional[int] = None
    provider: Optional[str] = None
    reason: Optional[str] = None
    retryable: bool = False
