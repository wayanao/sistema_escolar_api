from fastapi import APIRouter, Depends, status
from app.dependencies import get_current_user, HTTPException
from app.database import get_connection
from app.controllers.dashboard_controller import obtener_inasistencias_profesor_controller, obtener_notas_bajas_profesor_controller, obtener_ranking_rendimiento_controller, obtener_notas_altas_profesor_controller, obtener_ranking_mejor_rendimiento_controller

router = APIRouter(tags=['Dashboard'], dependencies=[Depends(get_current_user)])


def validar_acceso_profesor(profesor_id: int, current_user: dict):
    if current_user.get("rol") == "admin":
        return
    if current_user.get("rol") == "profesor" and current_user.get("id") == profesor_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permisos para consultar datos de otro profesor"
    )


def validar_acceso_asignacion(asignacion_id: int, current_user: dict):
    if current_user.get("rol") == "admin":
        return

    if current_user.get("rol") != "profesor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para consultar esta asignación"
        )

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM asignaciones WHERE id = %s AND profesor_id = %s",
            (asignacion_id, current_user.get("id"))
        )
        if cursor.fetchone():
            return
    finally:
        cursor.close()
        conn.close()

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permisos para consultar esta asignación"
    )

@router.get('/dashboard/inasistencias/{profesor_id}')
async def obtener_inasistencias_profesor(
    profesor_id: int,
    current_user: dict = Depends(get_current_user)
):
    validar_acceso_profesor(profesor_id, current_user)
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
    validar_acceso_profesor(profesor_id, current_user)
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
    validar_acceso_profesor(profesor_id, current_user)
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
    validar_acceso_asignacion(asignacion_id, current_user)
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
    validar_acceso_asignacion(asignacion_id, current_user)
    try:
        data = obtener_ranking_mejor_rendimiento_controller(asignacion_id, periodo)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
