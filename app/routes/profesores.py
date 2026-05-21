from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_active_admin
from app.schemas.profesor import ProfesorCreate

from app.controllers.profesor_controller import (
    actualizar_profesor_controller,
    crear_profesor_controller,
    obtener_profesores_paginado_controller,
    obtener_profesores_controller
)

router = APIRouter(tags=["Profesores"], dependencies=[Depends(get_current_active_admin)])


# 🚀 Crear profesor
@router.post("/profesores")
def crear_profesor(profesor: ProfesorCreate):

    profesor_id = crear_profesor_controller(profesor)

    return {
        "mensaje": "Profesor creado correctamente",
        "id": profesor_id
    }


# 📚 Obtener profesores
@router.get("/profesores")
def obtener_profesores(
    limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    busqueda: Optional[str] = None,
):
    if limit is not None:
        return obtener_profesores_paginado_controller(limit=limit, offset=offset, busqueda=busqueda)
    return obtener_profesores_controller()


@router.put("/profesores/{profesor_id}")
def actualizar_profesor(profesor_id: int, profesor: ProfesorCreate):
    return actualizar_profesor_controller(profesor_id, profesor)
