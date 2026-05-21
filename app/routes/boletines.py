import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_connection
from app.dependencies import get_current_active_admin, get_current_user
from app.schemas.boletin import BoletinCreate
from app.controllers.boletin_controller import (
    guardar_boletin_controller,
    obtener_boletin_admin_controller,
    obtener_boletin_para_profesor_controller,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/boletines",
    tags=["boletines"],
    dependencies=[Depends(get_current_user)],
)


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


@router.post("/guardar")
def guardar_boletin(
    boletin: BoletinCreate,
    current_user: dict = Depends(get_current_user),
):
    validar_acceso_asignacion(boletin.asignacion_id, current_user)
    validar_estudiante_en_asignacion(boletin.estudiante_id, boletin.asignacion_id)
    try:
        resultado = guardar_boletin_controller(boletin)
        return resultado
    except Exception as e:
        logger.exception("Error guardando boletin")
        raise HTTPException(status_code=500, detail="No se pudo guardar el boletin") from e

@router.get("/referencia/{asignacion_id}/{periodo}")
def obtener_notas_referencia(
    asignacion_id: int,
    periodo: int,
    current_user: dict = Depends(get_current_user),
):
    validar_acceso_asignacion(asignacion_id, current_user)
    try:
        notas = obtener_boletin_para_profesor_controller(asignacion_id, periodo)
        return notas
    except Exception as e:
        logger.exception("Error obteniendo notas de referencia")
        raise HTTPException(status_code=500, detail="No se pudieron obtener las notas") from e


@router.get("/admin/generar/{estudiante_id}/{periodo}")
def generar_boletin_admin(
    estudiante_id: int,
    periodo: int,
    _admin: dict = Depends(get_current_active_admin),
):
    try:
        resultado = obtener_boletin_admin_controller(estudiante_id, periodo)
        if not resultado:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error generando boletin admin")
        raise HTTPException(status_code=500, detail="No se pudo generar el boletin") from e
