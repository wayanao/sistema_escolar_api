from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.dependencies import get_current_user, get_current_active_admin
from app.schemas.branding import BrandingUpdate
from app.controllers.branding_controller import (
    obtener_branding_controller,
    actualizar_branding_controller,
    subir_logo_controller,
    eliminar_logo_controller,
)

router = APIRouter(tags=["Branding"], dependencies=[Depends(get_current_user)])


@router.get("/branding")
def obtener_branding():
    # Lectura permitida a cualquier usuario autenticado (lo necesitan los impresos).
    return obtener_branding_controller()


@router.put("/branding", dependencies=[Depends(get_current_active_admin)])
def actualizar_branding(data: BrandingUpdate):
    return actualizar_branding_controller(data)


@router.post("/branding/logo", dependencies=[Depends(get_current_active_admin)])
async def subir_logo(
    archivo: UploadFile = File(...),
    slot: str = Query("principal", description="'principal' o 'secundario'"),
):
    return await subir_logo_controller(archivo, slot)


@router.delete("/branding/logo", dependencies=[Depends(get_current_active_admin)])
def eliminar_logo(slot: str = Query("principal", description="'principal' o 'secundario'")):
    return eliminar_logo_controller(slot)
