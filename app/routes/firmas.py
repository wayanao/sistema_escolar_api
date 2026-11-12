"""Firmas guardadas para el boletin (docs/funcionalidades/FIRMAS_BOLETIN.md).

Toda ruta nace protegida por `get_current_user` en el router. Ademas:

- `/firmas/institucional` (la del rector o la rectora): **solo el admin**,
  tambien para leerla. La firma no viaja con la identidad institucional, que
  la lee cualquier usuario en cada impreso.
- `/firmas/mia`: **solo un profesor, y solo la suya**. El `id` sale de la
  sesion, nunca de la URL ni del cuerpo, asi que nadie guarda, ve ni borra la
  firma de otro. El admin no tiene una: recibe 403.

El admin ve la firma del director de grupo solo dentro del boletin que genera
(`GET /boletines/admin/generar/...`), que ya es solo suyo.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.controllers.firmas_controller import (
    borrar_firma_institucional_controller,
    borrar_mi_firma_controller,
    guardar_firma_institucional_controller,
    guardar_mi_firma_controller,
    obtener_firma_institucional_controller,
    obtener_mi_firma_controller,
)
from app.dependencies import get_current_active_admin, get_current_user
from app.schemas.firmas import FirmaIn

logger = logging.getLogger(__name__)

MENSAJE_SOLO_PROFESOR = "Solo un profesor puede guardar aquí su propia firma."

router = APIRouter(
    prefix="/firmas",
    tags=["firmas"],
    dependencies=[Depends(get_current_user)],
)


def profesor_de_la_sesion(current_user: dict = Depends(get_current_user)) -> dict:
    """El profesor de la sesion, o 403 para cualquier otro rol."""
    if current_user.get("rol") != "profesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MENSAJE_SOLO_PROFESOR)
    return current_user


# --------------------------------------------------------------------------
# Firma del rector(a): solo el admin
# --------------------------------------------------------------------------

@router.get("/institucional", dependencies=[Depends(get_current_active_admin)])
def obtener_firma_institucional():
    try:
        return obtener_firma_institucional_controller()
    except Exception as e:
        logger.exception("Error leyendo la firma institucional")
        raise HTTPException(status_code=500, detail="No se pudo cargar la firma") from e


@router.put("/institucional")
def guardar_firma_institucional(
    datos: FirmaIn,
    admin: dict = Depends(get_current_active_admin),
):
    try:
        return guardar_firma_institucional_controller(datos.imagen, admin)
    except Exception as e:
        logger.exception("Error guardando la firma institucional")
        raise HTTPException(status_code=500, detail="No se pudo guardar la firma") from e


@router.delete("/institucional", dependencies=[Depends(get_current_active_admin)])
def borrar_firma_institucional():
    try:
        return borrar_firma_institucional_controller()
    except Exception as e:
        logger.exception("Error borrando la firma institucional")
        raise HTTPException(status_code=500, detail="No se pudo quitar la firma") from e


# --------------------------------------------------------------------------
# Firma del profesor de la sesion
# --------------------------------------------------------------------------

@router.get("/mia")
def obtener_mi_firma(profesor: dict = Depends(profesor_de_la_sesion)):
    try:
        return obtener_mi_firma_controller(profesor["id"])
    except Exception as e:
        logger.exception("Error leyendo la firma del profesor")
        raise HTTPException(status_code=500, detail="No se pudo cargar tu firma") from e


@router.put("/mia")
def guardar_mi_firma(datos: FirmaIn, profesor: dict = Depends(profesor_de_la_sesion)):
    try:
        return guardar_mi_firma_controller(profesor["id"], datos.imagen)
    except Exception as e:
        logger.exception("Error guardando la firma del profesor")
        raise HTTPException(status_code=500, detail="No se pudo guardar tu firma") from e


@router.delete("/mia")
def borrar_mi_firma(profesor: dict = Depends(profesor_de_la_sesion)):
    try:
        return borrar_mi_firma_controller(profesor["id"])
    except Exception as e:
        logger.exception("Error borrando la firma del profesor")
        raise HTTPException(status_code=500, detail="No se pudo quitar tu firma") from e
