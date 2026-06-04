from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.dependencies import get_current_active_admin
from app.schemas.materia import MateriaEstadoUpdate
from app.controllers.materia_controller import (
    actualizar_estado_materia_controller,
    crear_materia_controller,
    actualizar_materia_controller,
)
from app.controllers.materia_controller import obtener_materias_controller, obtener_materias_paginado_controller

router = APIRouter(tags=["Materias"], dependencies=[Depends(get_current_active_admin)])

ESTADOS_MATERIA_FILTRO = {"activo", "inactivo", "todos"}


def validar_estado_filtro(estado: str) -> str:
    estado_normalizado = str(estado or "activo").strip().lower()
    if estado_normalizado not in ESTADOS_MATERIA_FILTRO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Estado de materia inválido.",
        )
    return estado_normalizado


@router.post("/materia")
def crear_materia(data: dict):
    return crear_materia_controller(data)

@router.get("/materias")
def obtener_materias(
    limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    busqueda: Optional[str] = None,
    estado: str = "activo",
):
    estado = validar_estado_filtro(estado)
    if limit is not None:
        return obtener_materias_paginado_controller(limit=limit, offset=offset, busqueda=busqueda, estado=estado)
    return obtener_materias_controller(estado=estado)


@router.put("/materias/{materia_id}")
def actualizar_materia(materia_id: int, data: dict):
    return actualizar_materia_controller(materia_id, data)


@router.patch("/materias/{materia_id}/estado")
def actualizar_estado_materia(materia_id: int, payload: MateriaEstadoUpdate):
    resultado = actualizar_estado_materia_controller(materia_id, payload.estado)
    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=resultado["error"])
    return resultado
