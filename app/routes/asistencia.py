from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user
from app.core.permissions import require_asignacion_access, require_estudiantes_in_asignacion
from typing import List
from app.schemas.asistencia import AsistenciaCreate
from app.controllers.asistencia_controller import guardar_asistencia_controller
from app.controllers.asistencia_controller import obtener_historial_asistencia


router = APIRouter(tags=["Asistencia"], dependencies=[Depends(get_current_user)])


@router.post("/asistencia")
def guardar_asistencia(data: List[AsistenciaCreate], current_user: dict = Depends(get_current_user)):
    if not data:
        raise HTTPException(status_code=422, detail="La asistencia debe incluir al menos un estudiante.")

    referencia = data[0]
    estudiantes_vistos = set()

    for item in data:
        if (
            item.asignacion_id != referencia.asignacion_id
            or item.fecha != referencia.fecha
            or item.periodo != referencia.periodo
        ):
            raise HTTPException(
                status_code=422,
                detail="Todos los registros deben pertenecer a la misma asignación, fecha y período.",
            )
        if item.estudiante_id in estudiantes_vistos:
            raise HTTPException(status_code=422, detail="La asistencia contiene estudiantes duplicados.")
        estudiantes_vistos.add(item.estudiante_id)

    require_asignacion_access(referencia.asignacion_id, current_user)
    require_estudiantes_in_asignacion(
        [item.estudiante_id for item in data],
        referencia.asignacion_id,
    )
    return guardar_asistencia_controller(data, usuario=current_user)


@router.get("/asistencia/historial/{asignacion_id}/{periodo}")
def historial(
    asignacion_id: int,
    periodo: int = 1,
    current_user: dict = Depends(get_current_user),
):
    require_asignacion_access(asignacion_id, current_user)
    return obtener_historial_asistencia(asignacion_id, periodo)
