from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from typing import List
from app.schemas.asistencia import AsistenciaCreate
from app.controllers.asistencia_controller import guardar_asistencia_controller
from app.controllers.asistencia_controller import obtener_historial_asistencia


router = APIRouter(tags=["Asistencia"], dependencies=[Depends(get_current_user)])

@router.post("/asistencia")
def guardar_asistencia(data: List[AsistenciaCreate]):
    print("DATA RECIBIDA EN ROUTER:", data)
    return guardar_asistencia_controller(data)


@router.get("/asistencia/historial/{asignacion_id}/{periodo}")
def historial(asignacion_id: int, periodo: int = 1):
    return obtener_historial_asistencia(asignacion_id, periodo)