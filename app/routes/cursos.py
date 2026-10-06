from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.dependencies import get_current_active_admin
from app.schemas.curso import CursoCreate, CursoCreateConAnio, CursoEstadoUpdate
from app.controllers.curso_controller import (
    CursoDuplicadoError,
    actualizar_curso_controller,
    actualizar_estado_curso_controller,
    crear_curso_controller,
    obtener_cursos_paginado_controller,
    obtener_cursos_controller
)

router = APIRouter(tags=["Cursos"], dependencies=[Depends(get_current_active_admin)])

ESTADOS_CURSO_FILTRO = {"activo", "inactivo", "todos"}


def validar_estado_filtro(estado: str) -> str:
    estado_normalizado = str(estado or "activo").strip().lower()
    if estado_normalizado not in ESTADOS_CURSO_FILTRO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Estado de curso inválido.",
        )
    return estado_normalizado


# 🚀 Crear curso
@router.post("/cursos")
def crear_curso(curso: CursoCreateConAnio):
    try:
        curso_id = crear_curso_controller(curso)
    except CursoDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    return {
        "mensaje": "Curso creado",
        "id": curso_id
    }


# 📚 Listar cursos
@router.get("/cursos")
def obtener_cursos(
    limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    busqueda: Optional[str] = None,
    estado: str = "activo",
    anio_lectivo_id: Annotated[Optional[int], Query(gt=0)] = None,
):
    """Sin `anio_lectivo_id`, los cursos del año activo."""
    estado = validar_estado_filtro(estado)
    try:
        if limit is not None:
            return obtener_cursos_paginado_controller(
                limit=limit,
                offset=offset,
                busqueda=busqueda,
                estado=estado,
                anio_lectivo_id=anio_lectivo_id,
            )
        return obtener_cursos_controller(estado=estado, anio_lectivo_id=anio_lectivo_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/cursos/{curso_id}")
def actualizar_curso(curso_id: int, curso: CursoCreate):
    try:
        resultado = actualizar_curso_controller(curso_id, curso)
    except CursoDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=resultado["error"])
    return resultado


@router.patch("/cursos/{curso_id}/estado")
def actualizar_estado_curso(curso_id: int, payload: CursoEstadoUpdate):
    resultado = actualizar_estado_curso_controller(curso_id, payload.estado)
    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=resultado["error"])
    return resultado
