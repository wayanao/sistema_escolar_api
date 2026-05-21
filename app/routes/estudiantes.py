from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_active_admin
from app.schemas.estudiante import EstudianteCreate

# 👇 IMPORTAMOS CONTROLLER
from app.controllers.estudiante_controller import (
    crear_estudiante_controller,
    obtener_estudiantes_controller,
    obtener_estudiantes_paginado_controller,
    obtener_detalles_estudiante_controller,
    actualizar_estudiante_controller,
    obtener_estudiante_por_id_controller
)

router = APIRouter(tags=["Estudiantes"], dependencies=[Depends(get_current_active_admin)])


# 🚀 Crear estudiante
@router.post("/estudiantes")
def crear_estudiante(est: EstudianteCreate):

    estudiante_id = crear_estudiante_controller(est)

    return {
        "mensaje": "Estudiante creado",
        "id": estudiante_id
    }


# 🔍 Listar estudiantes
@router.get("/estudiantes")
def obtener_estudiantes(
    limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    busqueda: Optional[str] = None,
):
    if limit is not None:
        return obtener_estudiantes_paginado_controller(limit=limit, offset=offset, busqueda=busqueda)

    return obtener_estudiantes_controller()

# 🔍 Obtener detalles de un estudiante
@router.get("/estudiantes/{estudiante_id}/detalles")
def obtener_detalles_estudiante(estudiante_id: int):
    return obtener_detalles_estudiante_controller(estudiante_id)

# 🔍 Obtener un estudiante por ID
@router.get("/estudiantes/{estudiante_id}")
def obtener_estudiante_por_id(estudiante_id: int):
    return obtener_estudiante_por_id_controller(estudiante_id)

# ✏️ Actualizar estudiante
@router.put("/estudiantes/{estudiante_id}")
def actualizar_estudiante(estudiante_id: int, est: EstudianteCreate):
    return actualizar_estudiante_controller(estudiante_id, est)
