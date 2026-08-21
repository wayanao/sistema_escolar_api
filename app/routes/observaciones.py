from fastapi import APIRouter, Depends
from app.core.permissions import require_asignacion_access, require_estudiante_in_asignacion
from app.database import get_cursor
from app.dependencies import get_current_user
from app.controllers.observacion_controller import guardar_observacion_controller
from app.repositories import observaciones_repository
from app.schemas.observacion import ObservacionCreate
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor

router = APIRouter(tags=["Observaciones"], dependencies=[Depends(get_current_user)])

@router.post("/observaciones")
def guardar_observacion(data: ObservacionCreate, current_user: dict = Depends(get_current_user)):
    require_asignacion_access(data.asignacion_id, current_user)
    require_estudiante_in_asignacion(data.estudiante_id, data.asignacion_id)
    return guardar_observacion_controller(data.model_dump())

@router.get("/observaciones/{estudiante_id}/{asignacion_id}/{periodo}")
def obtener_observacion(
    estudiante_id: int,
    asignacion_id: int,
    periodo: int,
    current_user: dict = Depends(get_current_user),
):
    require_asignacion_access(asignacion_id, current_user)
    require_estudiante_in_asignacion(estudiante_id, asignacion_id)

    with get_cursor() as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)

        row = observaciones_repository.leer_observacion(
            cursor, estudiante_id, asignacion_id, periodo
        )

    if row:
        return {"conductual": row[0], "cognitivo": row[1], "lenguaje": row[2]}

    return None
