"""
Punto de entrada del microservicio de IA de Syncra.

Para correrlo en desarrollo:
    uvicorn app.main:app --reload --port 8000

Documentacion interactiva automatica disponible en:
    http://localhost:8000/docs
"""

from fastapi import FastAPI

from app.routers import chat, health

app = FastAPI(
    title="Syncra AI Service",
    description="Microservicio de IA para el asistente de Syncra",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(chat.router)
