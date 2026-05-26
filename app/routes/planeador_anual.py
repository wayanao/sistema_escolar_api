from fastapi import APIRouter, Depends
from app.core.permissions import require_asignacion_access
from app.dependencies import get_current_user, HTTPException
from app.controllers.planeador_anual_controller import (
    obtener_planeadores_anual_controller,
    bulk_actualizar_planeadores_controller
)
from app.schemas.planeador_anual import PlaneadorAnualUpdate
from typing import List

router = APIRouter(tags=["Planeador Anual"], dependencies=[Depends(get_current_user)])

@router.get("/planeador-anual/{asignacion_id}/{periodo}")
def obtener_planeador_anual(
    asignacion_id: int,
    periodo: int,
    current_user: dict = Depends(get_current_user),
):
    require_asignacion_access(asignacion_id, current_user)
    try:
        planeadores = obtener_planeadores_anual_controller(asignacion_id, periodo)
        return {"planeadores": planeadores}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/planeador-anual/{asignacion_id}/{periodo}")
def actualizar_planeador_anual(
    asignacion_id: int,
    periodo: int,
    planeadores: List[PlaneadorAnualUpdate],
    current_user: dict = Depends(get_current_user),
):
    require_asignacion_access(asignacion_id, current_user)
    try:
        bulk_actualizar_planeadores_controller(asignacion_id, periodo, planeadores)
        return {"message": "Planeador actualizado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
