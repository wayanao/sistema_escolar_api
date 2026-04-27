from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
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


# 🚀 Crear nota
@router.post("/notas")
def crear_nota(nota: NotaCreate):

    nota_id = crear_nota_controller(nota)

    return {
        "mensaje": "Nota registrada",
        "id": nota_id
    }


# 📊 Ver notas + promedio
@router.get("/notas/{estudiante_id}")
def notas_estudiante(estudiante_id: int):

    return notas_estudiante_controller(estudiante_id)

# 📊 Boletín
@router.get("/boletin/{estudiante_id}")
def boletin(estudiante_id: int):

    return boletin_estudiante_controller(estudiante_id)

@router.get("/planilla/{asignacion_id}")
def planilla(asignacion_id: int):

    return planilla_asignacion_controller(asignacion_id)

@router.get("/boletin/detallado/{estudiante_id}")
def boletin_detallado(estudiante_id: int, periodo: int = 1):
    return boletin_detallado_controller(estudiante_id, periodo)

@router.post("/boletin/guardar")
def guardar_boletin(data: BoletinGuardar):
    return guardar_boletin_controller(data)