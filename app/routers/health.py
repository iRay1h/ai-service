from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """
    Endpoint sin autenticacion, solo para verificar que el servicio esta
    corriendo. Util para docker-compose healthchecks y para tu primera prueba.
    """
    return {"status": "ok"}
