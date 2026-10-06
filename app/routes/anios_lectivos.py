from fastapi import APIRouter, Depends, HTTPException, status

from app.controllers.anios_lectivos_controller import (
    AnioLectivoActivoInexistenteError,
    AnioLectivoEnPreparacionError,
    AnioLectivoSiguienteExistenteError,
    crear_anio_lectivo_controller,
    listar_anios_lectivos_controller,
)
from app.dependencies import get_current_active_admin, get_current_user

# Admin y profesor: el admin ve todos los años y el profesor solo el activo.
# La regla vive en el servicio; aqui solo se exige sesion.
router = APIRouter(tags=["Años lectivos"], dependencies=[Depends(get_current_user)])


@router.get("/anios-lectivos")
def listar_anios_lectivos(current_user: dict = Depends(get_current_user)):
    """Años lectivos con su estado, el mas reciente primero."""
    return listar_anios_lectivos_controller(current_user)


@router.post(
    "/anios-lectivos",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_active_admin)],
)
def crear_anio_lectivo():
    """Crea N+1 en preparación; el cliente no elige el número del año."""
    try:
        return crear_anio_lectivo_controller()
    except (
        AnioLectivoActivoInexistenteError,
        AnioLectivoEnPreparacionError,
        AnioLectivoSiguienteExistenteError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
