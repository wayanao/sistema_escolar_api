from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.dependencies import get_current_active_admin
from app.schemas.profesor import ProfesorCreate, ProfesorEstadoUpdate

from app.controllers.profesor_controller import (
    ESTADOS_FILTRO_PROFESOR,
    ProfesorDuplicadoError,
    actualizar_profesor_controller,
    actualizar_estado_profesor_controller,
    crear_profesor_controller,
    obtener_profesores_paginado_controller,
    obtener_profesores_controller
)

router = APIRouter(tags=["Profesores"], dependencies=[Depends(get_current_active_admin)])


# 🚀 Crear profesor
@router.post("/profesores")
def crear_profesor(profesor: ProfesorCreate):
    try:
        profesor_id = crear_profesor_controller(profesor)
    except ProfesorDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

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
    estado: Optional[str] = "activo",
):
    estado_normalizado = str(estado or "activo").strip().lower()
    if estado_normalizado not in ESTADOS_FILTRO_PROFESOR:
        raise HTTPException(
            status_code=422,
            detail="Filtro de estado de profesor invalido",
        )

    if limit is not None:
        return obtener_profesores_paginado_controller(
            limit=limit,
            offset=offset,
            busqueda=busqueda,
            estado=estado_normalizado,
        )
    return obtener_profesores_controller(estado=estado_normalizado)


@router.put("/profesores/{profesor_id}")
def actualizar_profesor(profesor_id: int, profesor: ProfesorCreate):
    try:
        resultado = actualizar_profesor_controller(profesor_id, profesor)
    except ProfesorDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=resultado["error"])
    return resultado


@router.patch("/profesores/{profesor_id}/estado")
def actualizar_estado_profesor(profesor_id: int, data: ProfesorEstadoUpdate):
    resultado = actualizar_estado_profesor_controller(profesor_id, data.estado)
    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=resultado["error"])
    return resultado
