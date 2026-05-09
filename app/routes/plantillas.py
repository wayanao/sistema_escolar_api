from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user, get_current_active_admin
from app.schemas.plantilla import PlantillaCreate, PlantillaUpdate
from app.controllers.plantilla_controller import (
    listar_plantillas_controller,
    obtener_plantilla_activa_controller,
    crear_plantilla_controller,
    actualizar_plantilla_controller,
    activar_plantilla_controller,
    duplicar_plantilla_controller,
    eliminar_plantilla_controller,
)

router = APIRouter(tags=["Plantillas"], dependencies=[Depends(get_current_user)])


@router.get("/plantillas")
def listar_plantillas(tipo: str | None = Query(None)):
    return listar_plantillas_controller(tipo)


@router.get("/plantillas/activa/{tipo}")
def obtener_plantilla_activa(tipo: str):
    return obtener_plantilla_activa_controller(tipo)


@router.post("/plantillas", dependencies=[Depends(get_current_active_admin)])
def crear_plantilla(plantilla: PlantillaCreate):
    return crear_plantilla_controller(plantilla)


@router.put("/plantillas/{plantilla_id}", dependencies=[Depends(get_current_active_admin)])
def actualizar_plantilla(plantilla_id: int, datos: PlantillaUpdate):
    return actualizar_plantilla_controller(plantilla_id, datos)


@router.post("/plantillas/{plantilla_id}/activar", dependencies=[Depends(get_current_active_admin)])
def activar_plantilla(plantilla_id: int):
    return activar_plantilla_controller(plantilla_id)


@router.post("/plantillas/{plantilla_id}/duplicar", dependencies=[Depends(get_current_active_admin)])
def duplicar_plantilla(plantilla_id: int, nuevo_nombre: str | None = Query(None)):
    return duplicar_plantilla_controller(plantilla_id, nuevo_nombre)


@router.delete("/plantillas/{plantilla_id}", dependencies=[Depends(get_current_active_admin)])
def eliminar_plantilla(plantilla_id: int):
    return eliminar_plantilla_controller(plantilla_id)
