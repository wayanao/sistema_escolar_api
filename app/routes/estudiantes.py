from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.dependencies import get_current_active_admin
from app.schemas.estudiante import EstudianteCreate, EstudianteEstadoUpdate

# 👇 IMPORTAMOS CONTROLLER
from app.controllers.estudiante_controller import (
    ESTADOS_FILTRO_ESTUDIANTE,
    crear_estudiante_controller,
    obtener_deudas_estudiante_controller,
    obtener_estudiantes_controller,
    obtener_estudiantes_paginado_controller,
    obtener_detalles_estudiante_controller,
    actualizar_estudiante_controller,
    actualizar_estado_estudiante_controller,
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
    estado: Optional[str] = "activo",
):
    estado_normalizado = str(estado or "activo").strip().lower()
    if estado_normalizado not in ESTADOS_FILTRO_ESTUDIANTE:
        raise HTTPException(
            status_code=422,
            detail="Filtro de estado de estudiante invalido",
        )

    if limit is not None:
        return obtener_estudiantes_paginado_controller(
            limit=limit,
            offset=offset,
            busqueda=busqueda,
            estado=estado_normalizado,
        )

    return obtener_estudiantes_controller(estado=estado_normalizado)

# 🔍 Obtener detalles de un estudiante
@router.get("/estudiantes/{estudiante_id}/detalles")
def obtener_detalles_estudiante(estudiante_id: int):
    return obtener_detalles_estudiante_controller(estudiante_id)

# 🔍 Obtener deudas academicas de un estudiante
@router.get("/estudiantes/{estudiante_id}/deudas")
def obtener_deudas_estudiante(
    estudiante_id: int,
    anio_lectivo_id: Annotated[Optional[int], Query(gt=0)] = None,
):
    """Sin `anio_lectivo_id`, las deudas del año activo."""
    try:
        return obtener_deudas_estudiante_controller(estudiante_id, anio_lectivo_id=anio_lectivo_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

# 🔍 Obtener un estudiante por ID
@router.get("/estudiantes/{estudiante_id}")
def obtener_estudiante_por_id(estudiante_id: int):
    return obtener_estudiante_por_id_controller(estudiante_id)

# ✏️ Actualizar estudiante
@router.put("/estudiantes/{estudiante_id}")
def actualizar_estudiante(estudiante_id: int, est: EstudianteCreate):
    return actualizar_estudiante_controller(estudiante_id, est)


@router.patch("/estudiantes/{estudiante_id}/estado")
def actualizar_estado_estudiante(estudiante_id: int, data: EstudianteEstadoUpdate):
    resultado = actualizar_estado_estudiante_controller(estudiante_id, data.estado)
    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=resultado["error"])
    return resultado
