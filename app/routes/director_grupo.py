"""«Mi curso» del director de grupo (docs/funcionalidades/MI_CURSO_DIRECTOR.md).

Vive aparte de `boletines.py` a proposito: esas rutas tienen guardias de
caracterizacion que fijan sus cuatro entradas, y esto es otra cosa (una vista
del curso entero para su director), aunque lea lo que guarda el boletin.

Toda ruta nace protegida por `get_current_user` en el router; la del curso
exige ademas `require_director_de_curso`: el admin o el profesor que dirige ese
curso del año activo.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path

from app.controllers.director_grupo_controller import (
    listar_cursos_dirigidos_controller,
    obtener_mi_curso_controller,
)
from app.core.permissions import require_director_de_curso
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/director-grupo",
    tags=["director-grupo"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/cursos")
def listar_mis_cursos(current_user: dict = Depends(get_current_user)):
    """Cursos del año activo que dirige el profesor de la sesión (para mostrar
    o esconder la pestaña). El admin recibe una lista vacía."""
    try:
        return listar_cursos_dirigidos_controller(current_user)
    except Exception as e:
        logger.exception("Error listando los cursos del director de grupo")
        raise HTTPException(status_code=500, detail="No se pudieron cargar tus cursos") from e


@router.get("/cursos/{curso_id}/{periodo}")
def obtener_mi_curso(
    curso_id: Annotated[int, Path(gt=0)],
    periodo: Annotated[int, Path(ge=1, le=4)],
    current_user: dict = Depends(get_current_user),
):
    """Puesto, promedio, definitiva de cada materia e inasistencias del curso."""
    require_director_de_curso(curso_id, current_user)
    try:
        resultado = obtener_mi_curso_controller(curso_id, periodo)
    except Exception as e:
        logger.exception("Error cargando el curso del director de grupo")
        raise HTTPException(status_code=500, detail="No se pudo cargar el curso") from e
    if resultado is None:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return resultado
