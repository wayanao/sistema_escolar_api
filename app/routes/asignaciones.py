from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.permissions import require_profesor_scope
from app.dependencies import get_current_active_admin, get_current_user
from app.schemas.asignacion import AsignacionCreate, AsignacionEdit
from app.database import get_connection

from app.controllers.asignacion_controller import (
    asignar_profesor_controller,
    cursos_por_profesor_controller,
    profesor_por_curso_controller,
    eliminar_asignacion_controller,
    eliminar_asignacion_por_id_controller,
    obtener_horarios_admin_controller,
    obtener_todas_asignaciones_paginado_controller,
    obtener_todas_asignaciones_controller,
    editar_asignacion_controller,
    obtener_disponibilidad_profesor_controller,
)

router = APIRouter(tags=["Asignaciones"])


@router.get("/asignaciones/lista")
def obtener_todas_asignaciones(
    limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    profesor_id: Optional[int] = None,
    curso_id: Optional[int] = None,
    materia_id: Optional[int] = None,
    busqueda: Optional[str] = None,
    _admin: dict = Depends(get_current_active_admin),
):
    if limit is not None:
        return obtener_todas_asignaciones_paginado_controller(
            limit=limit,
            offset=offset,
            profesor_id=profesor_id,
            curso_id=curso_id,
            materia_id=materia_id,
            busqueda=busqueda,
        )
    return obtener_todas_asignaciones_controller()

@router.put("/asignaciones/{asignacion_id}")
def editar_asignacion(
    asignacion_id: int,
    asignacion: AsignacionEdit,
    _admin: dict = Depends(get_current_active_admin)
):
    resultado = editar_asignacion_controller(asignacion_id, asignacion)
    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado["error"])
    return resultado


# ❌ Eliminar asignación por ID
@router.delete("/asignaciones/{asignacion_id}")
def eliminar_asignacion_por_id(
    asignacion_id: int,
    _admin: dict = Depends(get_current_active_admin)
):
    resultado = eliminar_asignacion_por_id_controller(asignacion_id)
    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=resultado["error"])
    return resultado


# 🚀 Obtener todos los horarios para Dashboard
@router.get("/hora/horarios-admin")
def horarios_admin(_admin: dict = Depends(get_current_active_admin)):
    return obtener_horarios_admin_controller()


@router.get("/profesores/{profesor_id}/disponibilidad")
def disponibilidad_profesor(
    profesor_id: int,
    dia: str,
    excluir_asignacion_id: Optional[int] = None,
    _admin: dict = Depends(get_current_active_admin),
):
    return obtener_disponibilidad_profesor_controller(
        profesor_id=profesor_id,
        dia=dia,
        excluir_asignacion_id=excluir_asignacion_id,
    )

# 🚀 Asignar profesor a curso
@router.post("/asignaciones")
def asignar_profesor(
    asignacion: AsignacionCreate,
    _admin: dict = Depends(get_current_active_admin)
):

    resultado = asignar_profesor_controller(asignacion)
    
    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado["error"])

    return resultado


# 📚 Ver cursos de un profesor
@router.get("/profesores/{profesor_id}/cursos")
def cursos_profesor(
    profesor_id: int,
    current_user: dict = Depends(get_current_user)
):
    require_profesor_scope(profesor_id, current_user, detail="No tienes permisos para consultar clases de otro profesor")

    return cursos_por_profesor_controller(profesor_id)


# 👨‍🏫 Ver profesor de un curso
@router.get("/cursos/{curso_id}/profesores")
def profesores_curso(
    curso_id: int,
    _admin: dict = Depends(get_current_active_admin)
):

    return profesor_por_curso_controller(curso_id)

# ❌ Eliminar asignación (MEJOR FORMA)
@router.delete("/asignaciones/{profesor_id}/{curso_id}")
def eliminar_asignacion(
    profesor_id: int,
    curso_id: int,
    _admin: dict = Depends(get_current_active_admin)
):

    return eliminar_asignacion_controller(profesor_id, curso_id)

@router.get("/mis-clases/{profesor_id}")
def obtener_clases_profesor(
    profesor_id: int,
    current_user: dict = Depends(get_current_user)
):
    require_profesor_scope(profesor_id, current_user, detail="No tienes permisos para consultar clases de otro profesor")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            a.id,
            m.nombre AS materia,
            c.nombre AS curso,
            c.id AS curso_id,
            a.dia,
            a.hora_inicio,
            a.hora_fin

        FROM asignaciones a
        JOIN materias m ON a.materia_id = m.id
        JOIN cursos c ON a.curso_id = c.id

        WHERE a.profesor_id = %s
          AND a.activo = TRUE
          AND COALESCE(LOWER(c.estado), 'activo') = 'activo'
          AND COALESCE(LOWER(m.estado), 'activo') = 'activo'
    """, (profesor_id,))

    clases = cursor.fetchall()

    resultado = []
    for c in clases:
        resultado.append({
            "id": c[0],
            "materia": c[1],
            "curso": c[2],
            "curso_id": c[3],
            "dia": c[4],
            "hora_inicio": c[5],
            "hora_fin": c[6]
        })

    cursor.close()
    conn.close()

    return resultado



