from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user
from app.database import get_connection
from app.core.permissions import require_estudiante_access
from app.schemas.nota import NotaCreate, BoletinGuardar

from app.controllers.notas_controller import (
    crear_nota_controller,
    notas_estudiante_controller,
    boletin_estudiante_controller,
    planilla_asignacion_controller,
    boletin_detallado_controller,
    guardar_boletin_controller
)

router = APIRouter(tags=["Notas"], dependencies=[Depends(get_current_user)])


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
            (asignacion_id, current_user.get("id"))
        )
        if cursor.fetchone():
            return
    finally:
        cursor.close()
        conn.close()

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")


# 🚀 Crear nota
@router.post("/notas")
def crear_nota(nota: NotaCreate, current_user: dict = Depends(get_current_user)):
    validar_acceso_asignacion(nota.asignacion_id, current_user)

    nota_id = crear_nota_controller(nota)

    return {
        "mensaje": "Nota registrada",
        "id": nota_id
    }


# 📊 Ver notas + promedio
@router.get("/notas/{estudiante_id}")
def notas_estudiante(estudiante_id: int, current_user: dict = Depends(get_current_user)):
    require_estudiante_access(estudiante_id, current_user)

    return notas_estudiante_controller(estudiante_id)

# 📊 Boletín
@router.get("/boletin/{estudiante_id}")
def boletin(estudiante_id: int, current_user: dict = Depends(get_current_user)):
    require_estudiante_access(estudiante_id, current_user)

    return boletin_estudiante_controller(estudiante_id)

@router.get("/planilla/{asignacion_id}")
def planilla(asignacion_id: int, current_user: dict = Depends(get_current_user)):
    validar_acceso_asignacion(asignacion_id, current_user)

    return planilla_asignacion_controller(asignacion_id)

@router.get("/boletin/detallado/{estudiante_id}")
def boletin_detallado(
    estudiante_id: int,
    periodo: int = 1,
    current_user: dict = Depends(get_current_user),
):
    require_estudiante_access(estudiante_id, current_user)
    return boletin_detallado_controller(estudiante_id, periodo)

@router.post("/boletin/guardar")
def guardar_boletin(data: BoletinGuardar, current_user: dict = Depends(get_current_user)):
    for materia in data.materias:
        validar_acceso_asignacion(materia.asignacion_id, current_user)
    return guardar_boletin_controller(data)
