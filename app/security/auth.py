"""
Autenticacion interna: solo el backend de Spring Boot puede llamar
a este microservicio, nunca el frontend ni nadie mas directamente.

Como usarlo en un endpoint:

    from fastapi import Depends
    from app.security.auth import verify_internal_key

    @router.post("/chat")
    def chat(body: ChatRequest, _=Depends(verify_internal_key)):
        ...
"""

from fastapi import Header, HTTPException, status
from app.core.config import settings


def verify_internal_key(x_internal_api_key: str = Header(default="")):
    if not settings.INTERNAL_API_KEY:
        # Si no configuraste la clave en .env, bloqueamos todo por seguridad
        # en vez de dejar el servicio abierto por accidente.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_API_KEY no configurada en el microservicio.",
        )

    if x_internal_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autorizado. Este endpoint solo puede ser llamado por el backend.",
        )
