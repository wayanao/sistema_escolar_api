import logging

from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_active_admin, get_current_user, HTTPException
from app.core.permissions import require_asignacion_access, require_profesor_scope
from app.controllers.dashboard_controller import (
    obtener_cumpleanos_admin_controller,
    obtener_cumpleanos_profesor_controller,
    obtener_inasistencias_profesor_controller,
    obtener_notas_altas_profesor_controller,
    obtener_notas_bajas_profesor_controller,
    obtener_ranking_mejor_rendimiento_controller,
    obtener_ranking_rendimiento_controller,
    validar_filtro_rendimiento_profesor_controller,
)

logger = logging.getLogger(__name__)

# Mensaje unico que reciben los siete paneles ante un fallo de infraestructura.
# No expone el texto de la excepcion: antes viajaba en el `detail` y un error de
# PostgreSQL podia llegar al navegador.
_ERROR_INTERNO_DASHBOARD = "No se pudo cargar la informacion del panel"

router = APIRouter(tags=['Dashboard'], dependencies=[Depends(get_current_user)])


def validar_filtro_rendimiento_profesor(
    profesor_id: int,
    curso_id: int | None,
    asignacion_id: int | None,
    current_user: dict,
):
    if curso_id is None:
        raise HTTPException(status_code=422, detail="Debes seleccionar un curso para consultar rendimiento")

    # `HTTPException` **tambien es `Exception`**, y este controlador lanza una
    # 403 propia desde dentro, via `require_asignacion_access`. Por eso hay que
    # dejarla pasar intacta antes de capturar el resto: sin el primer `except`,
    # ese 403 se convertiria en 500. Los `raise` de mas abajo quedan fuera del
    # `try` por la misma razon.
    try:
        (
            tiene_curso,
            tiene_asignacion,
            asignacion_academica_id,
        ) = validar_filtro_rendimiento_profesor_controller(
            profesor_id,
            curso_id,
            asignacion_id,
            current_user,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Fallo al validar el filtro de rendimiento del profesor %s", profesor_id
        )
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_DASHBOARD)

    if not tiene_curso:
        raise HTTPException(status_code=403, detail="No tienes permisos para consultar este curso")

    if asignacion_id is None:
        return None

    if not tiene_asignacion:
        raise HTTPException(status_code=403, detail="La asignación no pertenece al curso seleccionado")

    return asignacion_academica_id


@router.get('/dashboard/cumpleanos/admin')
def obtener_cumpleanos_admin(
    dias: int = Query(7, ge=0, le=31),
    _admin: dict = Depends(get_current_active_admin),
):
    try:
        return obtener_cumpleanos_admin_controller(dias=dias)
    except Exception:
        logger.exception("Fallo al cargar los cumpleanos del panel de administracion")
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_DASHBOARD)


@router.get('/dashboard/cumpleanos/profesor/{profesor_id}')
def obtener_cumpleanos_profesor(
    profesor_id: int,
    dias: int = Query(7, ge=0, le=31),
    current_user: dict = Depends(get_current_user),
):
    require_profesor_scope(profesor_id, current_user, detail="No tienes permisos para consultar datos de otro profesor")
    try:
        return obtener_cumpleanos_profesor_controller(profesor_id, dias=dias)
    except Exception:
        logger.exception("Fallo al cargar los cumpleanos del profesor %s", profesor_id)
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_DASHBOARD)


@router.get('/dashboard/inasistencias/{profesor_id}')
def obtener_inasistencias_profesor(
    profesor_id: int,
    current_user: dict = Depends(get_current_user)
):
    require_profesor_scope(profesor_id, current_user, detail="No tienes permisos para consultar datos de otro profesor")
    try:
        data = obtener_inasistencias_profesor_controller(profesor_id)
        return data
    except Exception:
        logger.exception("Fallo al cargar las inasistencias del profesor %s", profesor_id)
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_DASHBOARD)


@router.get('/dashboard/notas-bajas/{profesor_id}')
def obtener_notas_bajas_profesor(
    profesor_id: int,
    curso_id: int | None = Query(None),
    asignacion_id: int | None = Query(None),
    current_user: dict = Depends(get_current_user)
):
    require_profesor_scope(profesor_id, current_user, detail="No tienes permisos para consultar datos de otro profesor")
    asignacion_academica_id = validar_filtro_rendimiento_profesor(
        profesor_id, curso_id, asignacion_id, current_user
    )
    try:
        data = obtener_notas_bajas_profesor_controller(
            profesor_id,
            curso_id=curso_id,
            asignacion_id=asignacion_id,
            asignacion_academica_id=asignacion_academica_id,
        )
        return data
    except Exception:
        logger.exception("Fallo al cargar las notas bajas del profesor %s", profesor_id)
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_DASHBOARD)


@router.get('/dashboard/notas-altas/{profesor_id}')
def obtener_notas_altas_profesor(
    profesor_id: int,
    curso_id: int | None = Query(None),
    asignacion_id: int | None = Query(None),
    current_user: dict = Depends(get_current_user)
):
    require_profesor_scope(profesor_id, current_user, detail="No tienes permisos para consultar datos de otro profesor")
    asignacion_academica_id = validar_filtro_rendimiento_profesor(
        profesor_id, curso_id, asignacion_id, current_user
    )
    try:
        data = obtener_notas_altas_profesor_controller(
            profesor_id,
            curso_id=curso_id,
            asignacion_id=asignacion_id,
            asignacion_academica_id=asignacion_academica_id,
        )
        return data
    except Exception:
        logger.exception("Fallo al cargar las notas altas del profesor %s", profesor_id)
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_DASHBOARD)


@router.get('/dashboard/ranking/{asignacion_id}/{periodo}')
def obtener_ranking_rendimiento(
    asignacion_id: int,
    periodo: int = 1,
    current_user: dict = Depends(get_current_user)
):
    require_asignacion_access(asignacion_id, current_user, detail="No tienes permisos para consultar esta asignación")
    try:
        data = obtener_ranking_rendimiento_controller(asignacion_id, periodo)
        return data
    except Exception:
        logger.exception("Fallo al cargar el ranking de bajo rendimiento de la asignacion %s", asignacion_id)
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_DASHBOARD)


@router.get('/dashboard/ranking-mejor/{asignacion_id}/{periodo}')
def obtener_ranking_mejor_rendimiento(
    asignacion_id: int,
    periodo: int = 1,
    current_user: dict = Depends(get_current_user)
):
    require_asignacion_access(asignacion_id, current_user, detail="No tienes permisos para consultar esta asignación")
    try:
        data = obtener_ranking_mejor_rendimiento_controller(asignacion_id, periodo)
        return data
    except Exception:
        logger.exception("Fallo al cargar el ranking de mejor rendimiento de la asignacion %s", asignacion_id)
        raise HTTPException(status_code=500, detail=_ERROR_INTERNO_DASHBOARD)
