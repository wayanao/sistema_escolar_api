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
    profesor_tiene_asignacion_en_curso_controller,
    profesor_tiene_curso_controller,
)

router = APIRouter(tags=['Dashboard'], dependencies=[Depends(get_current_user)])


def validar_filtro_rendimiento_profesor(
    profesor_id: int,
    curso_id: int | None,
    asignacion_id: int | None,
    current_user: dict,
):
    if curso_id is None:
        raise HTTPException(status_code=422, detail="Debes seleccionar un curso para consultar rendimiento")

    if not profesor_tiene_curso_controller(profesor_id, curso_id):
        raise HTTPException(status_code=403, detail="No tienes permisos para consultar este curso")

    if asignacion_id is None:
        return

    require_asignacion_access(
        asignacion_id,
        current_user,
        detail="No tienes permisos para consultar esta asignación",
    )
    if not profesor_tiene_asignacion_en_curso_controller(profesor_id, curso_id, asignacion_id):
        raise HTTPException(status_code=403, detail="La asignación no pertenece al curso seleccionado")


@router.get('/dashboard/cumpleanos/admin')
async def obtener_cumpleanos_admin(
    dias: int = Query(7, ge=0, le=31),
    _admin: dict = Depends(get_current_active_admin),
):
    try:
        return obtener_cumpleanos_admin_controller(dias=dias)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/dashboard/cumpleanos/profesor/{profesor_id}')
async def obtener_cumpleanos_profesor(
    profesor_id: int,
    dias: int = Query(7, ge=0, le=31),
    current_user: dict = Depends(get_current_user),
):
    require_profesor_scope(profesor_id, current_user, detail="No tienes permisos para consultar datos de otro profesor")
    try:
        return obtener_cumpleanos_profesor_controller(profesor_id, dias=dias)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/dashboard/inasistencias/{profesor_id}')
async def obtener_inasistencias_profesor(
    profesor_id: int,
    current_user: dict = Depends(get_current_user)
):
    require_profesor_scope(profesor_id, current_user, detail="No tienes permisos para consultar datos de otro profesor")
    try:
        data = obtener_inasistencias_profesor_controller(profesor_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/dashboard/notas-bajas/{profesor_id}')
async def obtener_notas_bajas_profesor(
    profesor_id: int,
    curso_id: int | None = Query(None),
    asignacion_id: int | None = Query(None),
    current_user: dict = Depends(get_current_user)
):
    require_profesor_scope(profesor_id, current_user, detail="No tienes permisos para consultar datos de otro profesor")
    validar_filtro_rendimiento_profesor(profesor_id, curso_id, asignacion_id, current_user)
    try:
        data = obtener_notas_bajas_profesor_controller(
            profesor_id,
            curso_id=curso_id,
            asignacion_id=asignacion_id,
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/dashboard/notas-altas/{profesor_id}')
async def obtener_notas_altas_profesor(
    profesor_id: int,
    curso_id: int | None = Query(None),
    asignacion_id: int | None = Query(None),
    current_user: dict = Depends(get_current_user)
):
    require_profesor_scope(profesor_id, current_user, detail="No tienes permisos para consultar datos de otro profesor")
    validar_filtro_rendimiento_profesor(profesor_id, curso_id, asignacion_id, current_user)
    try:
        data = obtener_notas_altas_profesor_controller(
            profesor_id,
            curso_id=curso_id,
            asignacion_id=asignacion_id,
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/dashboard/ranking/{asignacion_id}/{periodo}')
async def obtener_ranking_rendimiento(
    asignacion_id: int,
    periodo: int = 1,
    current_user: dict = Depends(get_current_user)
):
    require_asignacion_access(asignacion_id, current_user, detail="No tienes permisos para consultar esta asignación")
    try:
        data = obtener_ranking_rendimiento_controller(asignacion_id, periodo)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/dashboard/ranking-mejor/{asignacion_id}/{periodo}')
async def obtener_ranking_mejor_rendimiento(
    asignacion_id: int,
    periodo: int = 1,
    current_user: dict = Depends(get_current_user)
):
    require_asignacion_access(asignacion_id, current_user, detail="No tienes permisos para consultar esta asignación")
    try:
        data = obtener_ranking_mejor_rendimiento_controller(asignacion_id, periodo)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
