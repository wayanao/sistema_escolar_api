from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, HTTPException
from app.core.permissions import require_asignacion_access, require_profesor_scope
from app.controllers.dashboard_controller import obtener_inasistencias_profesor_controller, obtener_notas_bajas_profesor_controller, obtener_ranking_rendimiento_controller, obtener_notas_altas_profesor_controller, obtener_ranking_mejor_rendimiento_controller

router = APIRouter(tags=['Dashboard'], dependencies=[Depends(get_current_user)])


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
    current_user: dict = Depends(get_current_user)
):
    require_profesor_scope(profesor_id, current_user, detail="No tienes permisos para consultar datos de otro profesor")
    try:
        data = obtener_notas_bajas_profesor_controller(profesor_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/dashboard/notas-altas/{profesor_id}')
async def obtener_notas_altas_profesor(
    profesor_id: int,
    current_user: dict = Depends(get_current_user)
):
    require_profesor_scope(profesor_id, current_user, detail="No tienes permisos para consultar datos de otro profesor")
    try:
        data = obtener_notas_altas_profesor_controller(profesor_id)
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
