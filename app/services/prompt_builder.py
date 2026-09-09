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
- Puedes consultar y resumir los documentos, subdocumentos y actas incluidos
    en el contexto. Si no aparecen allí, indica que no tienes ese contenido.
- Puedes explicar cómo diligenciar una plantilla usando su contenido real.
- Puedes ejecutar las acciones solicitadas por el aprendiz sobre el proyecto
    actual. Devuelve las acciones en "actions"; el backend las validará antes
    de ejecutarlas. Nunca inventes IDs ni actúes sobre otro proyecto.
- Si el aprendiz dice "asígnamela a mí" o equivalente, usa el current_user_id
    del contexto como assigned_to.
- Si el mensaje contiene una tarea concreta con suficiente informacion,
    incluye una propuesta de tarjeta; si no, usa null.
- Devuelve exclusivamente JSON valido con las claves "reply", "actions" y
    "suggested_card". Si una acción crea una tarea, no es necesario devolver
    una tarjeta pendiente. La propuesta usa "title", "description" y
    "suggested_priority" (ALTA, MEDIA o BAJA), y opcionalmente "column_id",
    "assigned_to" y "due_date". Las acciones permitidas son:
    CREATE_TASK, UPDATE_TASK, MOVE_TASK, ASSIGN_TASK, DELETE_TASK,
    CREATE_DOCUMENT, UPDATE_DOCUMENT y DELETE_DOCUMENT.
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
            f"- Aprendiz actual: {ctx.current_user_name or 'usuario actual'} (id {ctx.current_user_id or 'desconocido'})\n"
        )
        if ctx.members:
            parts.append("Miembros:\n" + "\n".join(
                f"- {item.get('userId', item.get('user_id'))}: {item.get('name')} ({item.get('role')})"
                for item in ctx.members
            ))
        if ctx.columns:
            parts.append("Columnas del tablero:\n" + "\n".join(
                f"- {item.get('id')}: {item.get('name')}" for item in ctx.columns
            ))
        if ctx.tasks:
            parts.append("Tareas del proyecto:\n" + "\n".join(
                f"- id={item.get('id')} titulo={item.get('title')} descripcion={item.get('description') or 'sin descripcion'} "
                f"columna={item.get('columnId', item.get('column_id'))} sprint={item.get('sprintId', item.get('sprint_id'))} "
                f"vence={item.get('dueDate', item.get('due_date'))} responsable={item.get('assignedTo', item.get('assigned_to'))}"
                for item in ctx.tasks
            ))
        if ctx.sprints:
            parts.append("Sprints:\n" + "\n".join(
                f"- {item.get('id')}: {item.get('name')} ({item.get('startDate', item.get('start_date'))} a {item.get('endDate', item.get('end_date'))}, {item.get('status')})"
                for item in ctx.sprints
            ))
        if ctx.documents:
            parts.append("Documentos, subdocumentos y actas:\n" + "\n".join(
                f"- id={item.get('id')} titulo={item.get('title')} tipo={item.get('type')} padre={item.get('parentDocumentId', item.get('parent_document_id'))} estado={item.get('status')} reunion={item.get('meetingType', item.get('meeting_type'))}\n"
                f"  contenido:\n{item.get('content') or 'sin contenido'}"
                for item in ctx.documents
            ))

    if request.history:
        parts.append("\nHistorial reciente de la conversacion:")
        for item in request.history[-10:]:  # solo los ultimos 10 mensajes
            parts.append(f"{item.role}: {item.content}")

    parts.append(f"\nMensaje nuevo del aprendiz:\n{request.message}")

    return "\n".join(parts)
