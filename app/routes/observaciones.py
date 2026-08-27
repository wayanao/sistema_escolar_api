import logging

from fastapi import APIRouter, Depends, HTTPException
from app.core.permissions import require_asignacion_access, require_estudiante_in_asignacion
from app.database import get_cursor
from app.dependencies import get_current_user
from app.controllers.observacion_controller import (
    AsignacionInactivaError,
    guardar_observacion_controller,
)
from app.repositories import observaciones_repository
from app.schemas.observacion import ObservacionCreate
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor

logger = logging.getLogger(__name__)

# ATENCION: el frontend MUESTRA este texto al usuario. `Observaciones.jsx` hace
# `typeof resultado.detalle === "string" ? resultado.detalle : <mensaje generico>`,
# asi que lo que se ponga aqui aparece tal cual en un aviso.
#
# Por eso son constantes y NUNCA `str(e)`: poner ahi el texto de la excepcion
# mostraria un error de PostgreSQL en pantalla. Es exactamente el hallazgo que
# `dashboard` tenia y que se corrigio el 2026-08-25.
_ERROR_GUARDAR = "No se pudo guardar la observacion. Intenta de nuevo."
_ERROR_INACTIVA = "Esta asignacion ya no esta activa, asi que no admite observaciones nuevas."
_ERROR_CONSULTAR = "No se pudo consultar la observacion. Intenta de nuevo."

router = APIRouter(tags=["Observaciones"], dependencies=[Depends(get_current_user)])

@router.post("/observaciones")
def guardar_observacion(data: ObservacionCreate, current_user: dict = Depends(get_current_user)):
    # Las dos guardas van FUERA del `try`: lanzan `HTTPException` y
    # `HTTPException` tambien es `Exception`, asi que envolverlas convertiria sus
    # 403 en 500. Es la leccion que costo una regresion en `dashboard`.
    require_asignacion_access(data.asignacion_id, current_user)
    require_estudiante_in_asignacion(data.estudiante_id, data.asignacion_id)

    try:
        return guardar_observacion_controller(data.model_dump())
    except HTTPException:
        raise
    except AsignacionInactivaError:
        raise HTTPException(status_code=403, detail=_ERROR_INACTIVA)
    except Exception:
        logger.exception(
            "Fallo al guardar la observacion del estudiante %s en la asignacion %s",
            data.estudiante_id,
            data.asignacion_id,
        )
        raise HTTPException(status_code=500, detail=_ERROR_GUARDAR)

@router.get("/observaciones/{estudiante_id}/{asignacion_id}/{periodo}")
def obtener_observacion(
    estudiante_id: int,
    asignacion_id: int,
    periodo: int,
    current_user: dict = Depends(get_current_user),
):
    require_asignacion_access(asignacion_id, current_user)
    require_estudiante_in_asignacion(estudiante_id, asignacion_id)

    try:
        with get_cursor() as cursor:
            asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)

            row = observaciones_repository.leer_observacion(
                cursor, estudiante_id, asignacion_id, periodo
            )
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Fallo al consultar la observacion del estudiante %s en la asignacion %s, periodo %s",
            estudiante_id,
            asignacion_id,
            periodo,
        )
        raise HTTPException(status_code=500, detail=_ERROR_CONSULTAR)

    if row:
        return {"conductual": row[0], "cognitivo": row[1], "lenguaje": row[2]}

    return None
