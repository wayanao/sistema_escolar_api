from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_active_admin
from app.schemas.curso import CursoCreate
from app.controllers.curso_controller import (
    actualizar_curso_controller,
    crear_curso_controller,
    obtener_cursos_paginado_controller,
    obtener_cursos_controller
)

router = APIRouter(tags=["Cursos"], dependencies=[Depends(get_current_active_admin)])


# 🚀 Crear curso
@router.post("/cursos")
def crear_curso(curso: CursoCreate):

    curso_id = crear_curso_controller(curso)

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
):
    if limit is not None:
        return obtener_cursos_paginado_controller(limit=limit, offset=offset, busqueda=busqueda)
    return obtener_cursos_controller()
@router.put("/cursos/{curso_id}")
def actualizar_curso(curso_id: int, curso: CursoCreate):
    return actualizar_curso_controller(curso_id, curso)
