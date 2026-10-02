import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.permissions import require_asignacion_access, require_estudiante_in_asignacion
from app.dependencies import get_current_active_admin, get_current_user
from app.schemas.boletin import BoletinCreate
from app.controllers.boletin_controller import (
    guardar_boletin_controller,
    obtener_boletin_admin_controller,
    obtener_boletin_para_profesor_controller,
    obtener_reporte_parcial_admin_controller,
)
from app.services.anio_lectivo import AnioLectivoInexistenteError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/boletines",
    tags=["boletines"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/guardar")
def guardar_boletin(
    boletin: BoletinCreate,
    current_user: dict = Depends(get_current_user),
):
    require_asignacion_access(boletin.asignacion_id, current_user)
    require_estudiante_in_asignacion(boletin.estudiante_id, boletin.asignacion_id)
    try:
        resultado = guardar_boletin_controller(boletin, usuario=current_user)
        return resultado
    except HTTPException:
        # La guardia del año lectivo (409 o 403) sale tal cual, no como 500.
        raise
    except Exception as e:
        logger.exception("Error guardando boletin")
        raise HTTPException(status_code=500, detail="No se pudo guardar el boletin") from e

@router.get("/referencia/{asignacion_id}/{periodo}")
def obtener_notas_referencia(
    asignacion_id: int,
    periodo: int,
    current_user: dict = Depends(get_current_user),
):
    require_asignacion_access(asignacion_id, current_user)
    try:
        notas = obtener_boletin_para_profesor_controller(asignacion_id, periodo)
        return notas
    except Exception as e:
        logger.exception("Error obteniendo notas de referencia")
        raise HTTPException(status_code=500, detail="No se pudieron obtener las notas") from e


@router.get("/admin/generar/{estudiante_id}/{periodo}")
def generar_boletin_admin(
    estudiante_id: int,
    periodo: int,
    _admin: dict = Depends(get_current_active_admin),
    anio_lectivo_id: Annotated[Optional[int], Query(gt=0)] = None,
):
    """Sin `anio_lectivo_id`, o con el activo, el boletin de siempre; con otro
    año, el del curso de su matricula de ese año."""
    try:
        resultado = obtener_boletin_admin_controller(
            estudiante_id, periodo, anio_lectivo_id=anio_lectivo_id
        )
        if not resultado:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        return resultado
    except HTTPException:
        raise
    except AnioLectivoInexistenteError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error generando boletin admin")
        raise HTTPException(status_code=500, detail="No se pudo generar el boletin") from e


@router.get("/admin/reporte-parcial/{estudiante_id}/{periodo}")
def generar_reporte_parcial_admin(
    estudiante_id: int,
    periodo: int,
    _admin: dict = Depends(get_current_active_admin),
    anio_lectivo_id: Annotated[Optional[int], Query(gt=0)] = None,
):
    """Sin `anio_lectivo_id`, o con el activo, el reporte de siempre; con otro
    año, el del curso de su matricula de ese año."""
    try:
        resultado = obtener_reporte_parcial_admin_controller(
            estudiante_id, periodo, anio_lectivo_id=anio_lectivo_id
        )
        if not resultado:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        return resultado
    except HTTPException:
        raise
    except AnioLectivoInexistenteError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error generando reporte parcial admin")
        raise HTTPException(status_code=500, detail="No se pudo generar el reporte parcial") from e
