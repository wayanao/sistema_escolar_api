from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.controllers.materia_controller import crear_materia_controller, actualizar_materia_controller
from app.controllers.materia_controller import obtener_materias_controller

router = APIRouter(tags=["Materias"], dependencies=[Depends(get_current_user)])

@router.post("/materia")
def crear_materia(data: dict):
    return crear_materia_controller(data)

@router.get("/materias")
def obtener_materias():
    return obtener_materias_controller()
@router.put("/materias/{materia_id}")
def actualizar_materia(materia_id: int, data: dict):
    return actualizar_materia_controller(materia_id, data)
