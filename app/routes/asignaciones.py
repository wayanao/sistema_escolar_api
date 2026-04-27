from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.schemas.asignacion import AsignacionCreate, AsignacionEdit
from app.database import get_connection

from app.controllers.asignacion_controller import (
    asignar_profesor_controller,
    cursos_por_profesor_controller,
    profesor_por_curso_controller,
    eliminar_asignacion_controller,
    obtener_horarios_admin_controller,
    obtener_todas_asignaciones_controller,
    editar_asignacion_controller
)

router = APIRouter(tags=["Asignaciones"], dependencies=[Depends(get_current_user)])

@router.get("/asignaciones/lista")
def obtener_todas_asignaciones():
    return obtener_todas_asignaciones_controller()

@router.put("/asignaciones/{asignacion_id}")
def editar_asignacion(asignacion_id: int, asignacion: AsignacionEdit):
    resultado = editar_asignacion_controller(asignacion_id, asignacion)
    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado["error"])
    return resultado


# 🚀 Obtener todos los horarios para Dashboard
@router.get("/hora/horarios-admin")
def horarios_admin():
    return obtener_horarios_admin_controller()

# 🚀 Asignar profesor a curso
@router.post("/asignaciones")
def asignar_profesor(asignacion: AsignacionCreate):

    resultado = asignar_profesor_controller(asignacion)
    
    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado["error"])

    return resultado


# 📚 Ver cursos de un profesor
@router.get("/profesores/{profesor_id}/cursos")
def cursos_profesor(profesor_id: int):

    return cursos_por_profesor_controller(profesor_id)


# 👨‍🏫 Ver profesor de un curso
@router.get("/cursos/{curso_id}/profesores")
def profesores_curso(curso_id: int):

    return profesor_por_curso_controller(curso_id)

# ❌ Eliminar asignación (MEJOR FORMA)
@router.delete("/asignaciones/{profesor_id}/{curso_id}")
def eliminar_asignacion(profesor_id: int, curso_id: int):

    return eliminar_asignacion_controller(profesor_id, curso_id)

@router.get("/mis-clases/{profesor_id}")
def obtener_clases_profesor(profesor_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            a.id,
            m.nombre AS materia,
            c.nombre AS curso

        FROM asignaciones a
        JOIN materias m ON a.materia_id = m.id
        JOIN cursos c ON a.curso_id = c.id

        WHERE a.profesor_id = %s
    """, (profesor_id,))

    clases = cursor.fetchall()

    resultado = []
    for c in clases:
        resultado.append({
            "id": c[0],
            "materia": c[1],
            "curso": c[2]
        })

    cursor.close()
    conn.close()

    return resultado
