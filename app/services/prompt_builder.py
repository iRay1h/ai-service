"""
Aqui se arma el texto final (prompt) que se le manda a la IA,
combinando: instrucciones del asistente + contexto del proyecto + historial + mensaje nuevo.

Tener esto separado del llm_client permite ajustar como "habla" el
asistente sin tocar la parte que se conecta con Gemini.
"""

from app.schemas.chat import ChatRequest

SYSTEM_INSTRUCTIONS = """
Eres el asistente de IA de Syncra, una plataforma de gestion de proyectos
academicos del SENA. Ayudas a aprendices a planificar tareas, organizar
su trabajo y hacer seguimiento de su proyecto.

Reglas:
- Responde siempre en espanol, de forma breve y clara.
- No inventes datos del proyecto que no se te hayan dado en el contexto.
- No puedes crear, editar ni eliminar nada directamente: solo puedes
  sugerir. Cualquier tarjeta que propongas debe ser confirmada por el
  aprendiz antes de agregarse al tablero.
"""


def build_prompt(request: ChatRequest) -> str:
    parts: list[str] = [SYSTEM_INSTRUCTIONS.strip()]

    if request.context:
        ctx = request.context
        parts.append(
            f"\nContexto del proyecto:\n"
            f"- Proyecto: {ctx.project_name} (id {ctx.project_id})\n"
            f"- Sprint activo: {ctx.active_sprint_name or 'ninguno'}\n"
            f"- Tareas pendientes: {ctx.pending_tasks_summary or 'sin informacion'}\n"
        )

    if request.history:
        parts.append("\nHistorial reciente de la conversacion:")
        for item in request.history[-10:]:  # solo los ultimos 10 mensajes
            parts.append(f"{item.role}: {item.content}")

    parts.append(f"\nMensaje nuevo del aprendiz:\n{request.message}")

    return "\n".join(parts)
