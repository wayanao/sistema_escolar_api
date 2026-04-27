from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, HTTPException
from app.controllers.dashboard_controller import obtener_inasistencias_profesor_controller, obtener_notas_bajas_profesor_controller, obtener_ranking_rendimiento_controller, obtener_notas_altas_profesor_controller, obtener_ranking_mejor_rendimiento_controller

router = APIRouter(tags=['Dashboard'], dependencies=[Depends(get_current_user)])

@router.get('/dashboard/inasistencias/{profesor_id}')
async def obtener_inasistencias_profesor(profesor_id: int):
    try:
        data = obtener_inasistencias_profesor_controller(profesor_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/dashboard/notas-bajas/{profesor_id}')
async def obtener_notas_bajas_profesor(profesor_id: int):
    try:
        data = obtener_notas_bajas_profesor_controller(profesor_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/dashboard/notas-altas/{profesor_id}')
async def obtener_notas_altas_profesor(profesor_id: int):
    try:
        data = obtener_notas_altas_profesor_controller(profesor_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/dashboard/ranking/{asignacion_id}/{periodo}')
async def obtener_ranking_rendimiento(asignacion_id: int, periodo: int = 1):
    try:
        data = obtener_ranking_rendimiento_controller(asignacion_id, periodo)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/dashboard/ranking-mejor/{asignacion_id}/{periodo}')
async def obtener_ranking_mejor_rendimiento(asignacion_id: int, periodo: int = 1):
    try:
        data = obtener_ranking_mejor_rendimiento_controller(asignacion_id, periodo)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
