from fastapi import APIRouter, Depends

from app.controllers.anios_lectivos_controller import listar_anios_lectivos_controller
from app.dependencies import get_current_user

# Admin y profesor: el admin ve todos los años y el profesor solo el activo.
# La regla vive en el servicio; aqui solo se exige sesion.
router = APIRouter(tags=["Años lectivos"], dependencies=[Depends(get_current_user)])


@router.get("/anios-lectivos")
def listar_anios_lectivos(current_user: dict = Depends(get_current_user)):
    """Años lectivos con su estado, el mas reciente primero."""
    return listar_anios_lectivos_controller(current_user)
