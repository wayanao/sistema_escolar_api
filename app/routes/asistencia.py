from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.core.permissions import require_asignacion_access, require_estudiante_in_asignacion
from typing import List
from app.schemas.asistencia import AsistenciaCreate
from app.controllers.asistencia_controller import guardar_asistencia_controller
from app.controllers.asistencia_controller import obtener_historial_asistencia


router = APIRouter(tags=["Asistencia"], dependencies=[Depends(get_current_user)])


@router.post("/asistencia")
def guardar_asistencia(data: List[AsistenciaCreate], current_user: dict = Depends(get_current_user)):
    for item in data:
        require_asignacion_access(item.asignacion_id, current_user)
        require_estudiante_in_asignacion(item.estudiante_id, item.asignacion_id)
    return guardar_asistencia_controller(data)


@router.get("/asistencia/historial/{asignacion_id}/{periodo}")
def historial(
    asignacion_id: int,
    periodo: int = 1,
    current_user: dict = Depends(get_current_user),
):
    require_asignacion_access(asignacion_id, current_user)
    return obtener_historial_asistencia(asignacion_id, periodo)
