from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.core.permissions import require_asignacion_access, require_estudiante_access
from app.schemas.nota import NotaCreate

from app.controllers.notas_controller import (
    crear_nota_controller,
    notas_estudiante_controller,
    boletin_estudiante_controller,
    planilla_asignacion_controller,
    boletin_detallado_controller
)

router = APIRouter(tags=["Notas"], dependencies=[Depends(get_current_user)])


# 🚀 Crear nota
@router.post("/notas")
def crear_nota(nota: NotaCreate, current_user: dict = Depends(get_current_user)):
    require_asignacion_access(nota.asignacion_id, current_user)

    nota_id = crear_nota_controller(nota, usuario=current_user)

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
    require_asignacion_access(asignacion_id, current_user)

    return planilla_asignacion_controller(asignacion_id)

@router.get("/boletin/detallado/{estudiante_id}")
def boletin_detallado(
    estudiante_id: int,
    periodo: int = 1,
    current_user: dict = Depends(get_current_user),
):
    require_estudiante_access(estudiante_id, current_user)
    return boletin_detallado_controller(estudiante_id, periodo)
