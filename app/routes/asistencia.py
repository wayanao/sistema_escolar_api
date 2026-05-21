from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user
from app.database import get_connection
from typing import List
from app.schemas.asistencia import AsistenciaCreate
from app.controllers.asistencia_controller import guardar_asistencia_controller
from app.controllers.asistencia_controller import obtener_historial_asistencia


router = APIRouter(tags=["Asistencia"], dependencies=[Depends(get_current_user)])


def validar_acceso_asignacion(asignacion_id: int, current_user: dict):
    if current_user.get("rol") == "admin":
        return
    if current_user.get("rol") != "profesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM asignaciones WHERE id = %s AND profesor_id = %s",
            (asignacion_id, current_user.get("id")),
        )
        if cursor.fetchone():
            return
    finally:
        cursor.close()
        conn.close()

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")


def validar_estudiante_en_asignacion(estudiante_id: int, asignacion_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 1
            FROM estudiantes e
            JOIN asignaciones a ON a.curso_id = e.curso_id
            WHERE e.id = %s AND a.id = %s
            """,
            (estudiante_id, asignacion_id),
        )
        if cursor.fetchone():
            return
    finally:
        cursor.close()
        conn.close()

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="El estudiante no pertenece a esta asignación",
    )


@router.post("/asistencia")
def guardar_asistencia(data: List[AsistenciaCreate], current_user: dict = Depends(get_current_user)):
    for item in data:
        validar_acceso_asignacion(item.asignacion_id, current_user)
        validar_estudiante_en_asignacion(item.estudiante_id, item.asignacion_id)
    return guardar_asistencia_controller(data)


@router.get("/asistencia/historial/{asignacion_id}/{periodo}")
def historial(
    asignacion_id: int,
    periodo: int = 1,
    current_user: dict = Depends(get_current_user),
):
    validar_acceso_asignacion(asignacion_id, current_user)
    return obtener_historial_asistencia(asignacion_id, periodo)
