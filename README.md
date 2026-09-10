# Syncra AI Service

Microservicio en Python (FastAPI) que le da soporte de IA al asistente de
Syncra. Habla únicamente con el backend de Java — nunca directo con el
frontend ni con la base de datos.

Esta guía asume que **no tienes nada instalado todavía**. Sigue los pasos
en orden.

---

## 1. Instalar Python

Verifica primero si ya lo tienes:

```bash
python --version
```

o en algunos sistemas:

```bash
python3 --version
```

Necesitas **Python 3.11 o superior**. Si no lo tienes o la versión es
vieja:

- **Windows**: descarga el instalador desde https://www.python.org/downloads/
  Durante la instalación, **marca la casilla "Add Python to PATH"** — es el
  error más común, si no la marcas después el comando `python` no funciona.
- **Mac**: `brew install python@3.12` (si tienes Homebrew), o descárgalo
  desde la misma página oficial.
- **Linux (Ubuntu/Debian)**: `sudo apt update && sudo apt install python3 python3-venv python3-pip`

Confirma que quedó bien instalado repitiendo `python --version`.

---

## 2. Crear el entorno virtual

Un entorno virtual es una "burbuja" aislada donde se instalan las
dependencias de este proyecto, sin mezclarlas con otros proyectos de
Python que tengas en tu computador. Siempre se hace, es estándar.

Párate dentro de la carpeta `ai-service/` (esta carpeta) y ejecuta:

```bash
python -m venv venv
```

Esto crea una carpeta `venv/` (no se sube a git, ya está en `.gitignore`).

Ahora actívalo:

- **Windows (PowerShell)**:
  ```powershell
  venv\Scripts\Activate.ps1
  ```
  Si te da un error de "ejecución de scripts deshabilitada", corre esto una
  vez como administrador: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

- **Windows (CMD)**:
  ```cmd
  venv\Scripts\activate.bat
  ```

- **Mac / Linux**:
  ```bash
  source venv/bin/activate
  ```

Sabrás que funcionó porque tu terminal ahora muestra `(venv)` al inicio de
la línea. **Debes activar este entorno cada vez que abras una terminal
nueva para trabajar en este proyecto.**

---

## 3. Instalar el framework y las dependencias

Con el entorno virtual activado (`(venv)` visible), instala todo lo que
necesita el proyecto de una sola vez:

```bash
pip install -r requirements.txt
```

Esto instala:
- **FastAPI**: el framework web.
- **Uvicorn**: el servidor que corre la aplicación.
- **Pydantic**: valida automáticamente los datos que entran y salen.
- **python-dotenv**: lee el archivo `.env`.
- **httpx**: realiza las llamadas HTTP a OpenRouter.

---

## 4. Configurar tus variables de entorno

Copia el archivo de ejemplo:

```bash
# Mac/Linux
cp .env.example .env

# Windows (CMD)
copy .env.example .env
```

Abre el nuevo archivo `.env` y completa:

1. **OPENROUTER_API_KEY**: usa la misma clave para todos los modelos de OpenRouter.
   No se usan varias API keys; el fallback se hace entre modelos, no entre proveedores.
2. **OPENROUTER_MODEL_PRIMARY**, **OPENROUTER_MODEL_SECONDARY**, **OPENROUTER_MODEL_FALLBACK**:
   por defecto se usan los modelos gratuitos activos que responden correctamente en OpenRouter:
   - `openai/gpt-oss-20b`
   - `meta-llama/llama-3.2-3b-instruct`
   - `google/gemma-3-4b-it`
3. **INTERNAL_API_KEY**: invéntate un texto largo y aleatorio. Puedes
   generarlo con:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Este mismo valor lo vas a poner después en el `application.properties`
   del backend de Java, para que solo él pueda llamar a este microservicio.

**Nunca subas el archivo `.env` a git** (ya está protegido en `.gitignore`,
pero revisa que no lo estés forzando con `git add -f`).

---

## 5. Correr el microservicio

Con el entorno virtual activado:

```bash
uvicorn app.main:app --reload --port 8000
```

Si todo salió bien, verás algo como:

```
Uvicorn running on http://127.0.0.1:8000
```

`--reload` hace que el servidor se reinicie solo cada vez que guardas un
cambio en el código — muy útil mientras programas.

---

## 6. Probar que funciona

Abre en tu navegador:

```
http://localhost:8000/docs
```

Esto te muestra una interfaz automática (Swagger) donde puedes probar los
endpoints sin necesidad de Postman.

Prueba rápida por consola:

```bash
curl http://localhost:8000/health
```

Debe responder `{"status":"ok"}`.

Para probar el chat (reemplaza `TU_CLAVE_INTERNA` por lo que pusiste en `.env`):

```bash
curl -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -H "X-Internal-Api-Key: TU_CLAVE_INTERNA" \
  -d '{"message": "Hola, ¿qué puedes hacer?"}'
```

Si te responde con un JSON que trae `"reply": "..."`, ¡ya está funcionando!
Si te da 401, revisa que el header tenga la clave exacta del `.env`.

---

## Estructura del proyecto

```
ai-service/
  app/
    main.py              -> arranca la aplicación y registra las rutas
    core/
      config.py           -> lee las variables de entorno
    routers/
      health.py           -> endpoint GET /health
      chat.py              -> endpoint POST /ai/chat
    schemas/
      chat.py              -> los "moldes" de entrada/salida (equivalente a los DTOs de Java)
    services/
      llm_client.py        -> único lugar que habla con Gemini
      prompt_builder.py    -> arma el texto que se le manda a la IA
    security/
      auth.py              -> valida que solo el backend Java pueda llamar
  requirements.txt
  .env.example
  .gitignore
  Dockerfile               -> para cuando lo integren a docker-compose
  README.md
```

---

## Siguientes pasos (cuando quieras seguir avanzando)

1. Conectar esto desde el backend de Java (llenar `AiClientService`,
   `AiConversationService`, `AiMessageService`, que hoy están vacíos).
2. Construir la pantalla de chat en Angular.
3. Enviar el contexto real del proyecto (tareas, sprint activo) en cada
   request — ahora mismo `ProjectContext` está definido pero el backend
   todavía no lo llena con datos reales.
4. Implementar la generación de `suggested_card` (propuesta de tarjeta).
5. Integrar este servicio a la carpeta `docker/` del repo principal para
   que se levante junto con el backend y la base de datos.


cd ai-service
venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000