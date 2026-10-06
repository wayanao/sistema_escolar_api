from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.controllers.anios_lectivos_controller import (
    AnioLectivoActivoInexistenteError,
    AnioLectivoDestinoInvalidoError,
    AnioLectivoEnPreparacionError,
    AnioLectivoSiguienteExistenteError,
    ConfiguracionAnioDuplicadaError,
    ConfiguracionAnioInconsistenteError,
    copiar_configuracion_anio_controller,
    crear_anio_lectivo_controller,
    listar_anios_lectivos_controller,
)
from app.dependencies import get_current_active_admin, get_current_user
from app.schemas.anio_lectivo import CopiarConfiguracionAnio
from app.services.anio_lectivo import AnioLectivoInexistenteError

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


@router.post(
    "/anios-lectivos/{anio_lectivo_id}/copiar-configuracion",
    dependencies=[Depends(get_current_active_admin)],
)
def copiar_configuracion_anio(
    anio_lectivo_id: Annotated[int, Path(gt=0)],
    opciones: CopiarConfiguracionAnio,
):
    """Copia al N+1 en preparación; todo se confirma o se revierte junto."""
    try:
        return copiar_configuracion_anio_controller(anio_lectivo_id, opciones)
    except AnioLectivoInexistenteError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except (
        AnioLectivoActivoInexistenteError,
        AnioLectivoDestinoInvalidoError,
        ConfiguracionAnioDuplicadaError,
        ConfiguracionAnioInconsistenteError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
