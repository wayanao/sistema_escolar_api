from fastapi import APIRouter, Depends
from app.core.permissions import require_asignacion_access
from app.dependencies import get_current_user, HTTPException
from app.controllers.planeador_anual_controller import (
    obtener_planeadores_anual_controller,
    bulk_actualizar_planeadores_controller,
    consultar_planeador_anio_anterior_controller,
    traer_planeador_anio_anterior_controller,
)
from app.schemas.planeador_anual import PlaneadorAnualUpdate
from typing import List

router = APIRouter(tags=["Planeador Anual"], dependencies=[Depends(get_current_user)])

# Año lectivo, fase 7: traer el planeador del año pasado. Van antes que las
# rutas de un periodo a propósito: tienen la misma forma de dirección y FastAPI
# usa la primera que coincide; después, "anio-anterior" se leería como un
# periodo y la petición daría 422. El permiso lo revisa el controlador, en su
# misma conexión.
@router.get("/planeador-anual/{asignacion_id}/anio-anterior")
def consultar_planeador_anio_anterior(
    asignacion_id: int,
    current_user: dict = Depends(get_current_user),
):
    return consultar_planeador_anio_anterior_controller(asignacion_id, usuario=current_user)

@router.post("/planeador-anual/{asignacion_id}/anio-anterior")
def traer_planeador_anio_anterior(
    asignacion_id: int,
    current_user: dict = Depends(get_current_user),
):
    return traer_planeador_anio_anterior_controller(asignacion_id, usuario=current_user)

@router.get("/planeador-anual/{asignacion_id}/{periodo}")
def obtener_planeador_anual(
    asignacion_id: int,
    periodo: int,
    current_user: dict = Depends(get_current_user),
):
    require_asignacion_access(asignacion_id, current_user)
    try:
        planeadores = obtener_planeadores_anual_controller(asignacion_id, periodo)
        return {"planeadores": planeadores}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/planeador-anual/{asignacion_id}/{periodo}")
def actualizar_planeador_anual(
    asignacion_id: int,
    periodo: int,
    planeadores: List[PlaneadorAnualUpdate],
    current_user: dict = Depends(get_current_user),
):
    require_asignacion_access(asignacion_id, current_user)
    try:
        bulk_actualizar_planeadores_controller(
            asignacion_id, periodo, planeadores, usuario=current_user
        )
        return {"message": "Planeador actualizado correctamente"}
    except HTTPException:
        # La guardia del año lectivo (409 o 403) sale tal cual, no como 500.
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
