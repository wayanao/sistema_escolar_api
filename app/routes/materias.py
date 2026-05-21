from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_active_admin
from app.controllers.materia_controller import crear_materia_controller, actualizar_materia_controller
from app.controllers.materia_controller import obtener_materias_controller, obtener_materias_paginado_controller

router = APIRouter(tags=["Materias"], dependencies=[Depends(get_current_active_admin)])

@router.post("/materia")
def crear_materia(data: dict):
    return crear_materia_controller(data)

@router.get("/materias")
def obtener_materias(
    limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    busqueda: Optional[str] = None,
):
    if limit is not None:
        return obtener_materias_paginado_controller(limit=limit, offset=offset, busqueda=busqueda)
    return obtener_materias_controller()
@router.put("/materias/{materia_id}")
def actualizar_materia(materia_id: int, data: dict):
    return actualizar_materia_controller(materia_id, data)
