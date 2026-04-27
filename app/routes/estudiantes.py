from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas.estudiante import EstudianteCreate

# 👇 IMPORTAMOS CONTROLLER
from app.controllers.estudiante_controller import (
    crear_estudiante_controller,
    obtener_estudiantes_controller,
    obtener_detalles_estudiante_controller,
    actualizar_estudiante_controller,
    obtener_estudiante_por_id_controller
)

router = APIRouter(tags=["Estudiantes"], dependencies=[Depends(get_current_user)])


# 🚀 Crear estudiante
@router.post("/estudiantes")
def crear_estudiante(est: EstudianteCreate):

    estudiante_id = crear_estudiante_controller(est)

    return {
        "mensaje": "Estudiante creado",
        "id": estudiante_id
    }


# 🔍 Listar estudiantes
@router.get("/estudiantes")
def obtener_estudiantes():

    return obtener_estudiantes_controller()

# 🔍 Obtener detalles de un estudiante
@router.get("/estudiantes/{estudiante_id}/detalles")
def obtener_detalles_estudiante(estudiante_id: int):
    return obtener_detalles_estudiante_controller(estudiante_id)

# 🔍 Obtener un estudiante por ID
@router.get("/estudiantes/{estudiante_id}")
def obtener_estudiante_por_id(estudiante_id: int):
    return obtener_estudiante_por_id_controller(estudiante_id)

# ✏️ Actualizar estudiante
@router.put("/estudiantes/{estudiante_id}")
def actualizar_estudiante(estudiante_id: int, est: EstudianteCreate):
    return actualizar_estudiante_controller(estudiante_id, est)
