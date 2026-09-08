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
    # Se puede ir ampliando con mas datos segun lo necesiten
    # (columnas del tablero, miembros del equipo, etc.)


class ChatHistoryItem(BaseModel):
    role: str  # "USER" o "ASSISTANT", igual que el enum AiRoleEnum de Java
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    context: Optional[ProjectContext] = None
    history: list[ChatHistoryItem] = Field(default_factory=list)


class SuggestedCard(BaseModel):
    """
    Propuesta de tarjeta Kanban generada por la IA (RF108).
    El aprendiz debe confirmarla antes de que el backend la cree de verdad (RF109).
    Este microservicio SOLO propone, nunca crea la tarjeta en la base de datos.
    """
    title: str
    description: Optional[str] = None
    suggested_priority: Optional[str] = None  # ej: "ALTA", "MEDIA", "BAJA"


class ChatResponse(BaseModel):
    reply: str
    suggested_card: Optional[SuggestedCard] = None
