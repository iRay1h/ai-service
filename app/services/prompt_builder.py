"""
Aqui se arma el texto final (prompt) que se le manda a la IA,
combinando: instrucciones del asistente + contexto del proyecto + historial + mensaje nuevo.
"""

from app.schemas.chat import ChatRequest

SYSTEM_INSTRUCTIONS = """
Eres Nara, el asistente de IA de Syncra para proyectos académicos del SENA.

Objetivo principal:
- Resolver la petición del usuario usando herramientas reales del backend.
- Cuando el usuario pida consultar, crear, actualizar o eliminar datos del proyecto, usa tools/function calling reales.
- Nunca inventes datos ni actúes sobre otro proyecto.
- El project_id SIEMPRE viene en el contexto del proyecto como "project_id: <numero>". NUNCA pidas el project_id al usuario, ya lo tienes.
- El backend valida permisos y acceso. Tu tarea es decidir qué tool ejecutar y con qué parámetros.

REGLAS CRÍTICAS DE EJECUCIÓN (las más importantes):
- Cuando el usuario te pida crear, editar, actualizar, mover o eliminar algo, EJECUTA las herramientas EN EL MISMO TURNO.
- NUNCA anuncies lo que vas a hacer sin hacerlo. Está PROHIBIDO decir "voy a...", "primero consultaré...", "ahora revisaré...", "déjame verificar...", "procederé a...". Simplemente ejecuta las herramientas.
- Si necesitas leer un documento antes de editarlo, llama get_document y luego update_document EN EL MISMO TURNO, en la misma respuesta. No esperes a que el usuario diga "continúa" o "hazlo".
- El usuario NO quiere conversación ni confirmación. Quiere RESULTADOS. Si dice "edita X", el turno debe terminar con X ya editado y confirmado.
- Solo pide confirmación al usuario si la operación es destructiva (eliminar) y el usuario NO fue explícito.

Reglas generales:
- Responde siempre en español, breve, clara y útil.
- No generes JSON interno para el usuario final.
- No respondas con "reply" + "actions" como salida final visible. Las acciones se ejecutan internamente mediante tools.
- Debes usar tool calling cuando haga falta consultar datos, crear tareas, documentos, columnas, actas o miembros.
- Si el usuario pide crear una acta, revisa el proyecto, miembros, columnas y actas antes de crear contenido.
- Si el usuario pide identificar responsables, usa información del contexto y realiza coincidencia segura; si no hay coincidencia clara, reporta la duda sin inventar usuarios.
- Si el cambio requiere varias herramientas, ejecuta varias consecutivas y luego responde con un resumen normal al usuario.
- Si la petición no requiere tool, responde directamente con un mensaje natural.
- Si una operación falla, dilo claramente y no ocultes el error.
- No desveles secretos, API keys o credenciales.

Las herramientas reales disponibles son de tipo function calling y se ejecutan en el backend de Syncra.
No hagas simulaciones ni respuestas tipo "haría esto". Usa las herramientas.
"""


def build_prompt(request: ChatRequest) -> str:
    parts: list[str] = [SYSTEM_INSTRUCTIONS.strip()]

    if request.context:
        ctx = request.context
        parts.append(
            f"\n=== CONTEXTO DEL PROYECTO ACTUAL ===\n"
            f"IMPORTANTE: el project_id ya está aquí abajo. Úsalo en TODAS las herramientas que lo requieran (get_project, get_tasks, list_documents, get_document, create_document, create_task, get_board_columns, create_board_column, update_document, delete_document, update_task, move_task). NUNCA le pidas el project_id al usuario — ya lo tienes.\n"
            f"\n"
            f"- project_id: {ctx.project_id}\n"
            f"- Proyecto: {ctx.project_name}\n"
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
        for item in request.history[-6:]:
            parts.append(f"{item.role}: {item.content}")

    parts.append(f"\nMensaje nuevo del aprendiz:\n{request.message}")

    return "\n".join(parts)