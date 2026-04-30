import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas.boletin import BoletinCreate
from app.controllers.boletin_controller import (
    guardar_boletin_controller,
    obtener_boletin_admin_controller,
    obtener_boletin_para_profesor_controller,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/boletines",
    tags=["boletines"],
    dependencies=[Depends(get_current_user)],
)

@router.post("/guardar")
def guardar_boletin(boletin: BoletinCreate):
    try:
        resultado = guardar_boletin_controller(boletin)
        return resultado
    except Exception as e:
        logger.exception("Error guardando boletin")
        raise HTTPException(status_code=500, detail="No se pudo guardar el boletin") from e

@router.get("/referencia/{asignacion_id}/{periodo}")
def obtener_notas_referencia(asignacion_id: int, periodo: int):
    try:
        notas = obtener_boletin_para_profesor_controller(asignacion_id, periodo)
        return notas
    except Exception as e:
        logger.exception("Error obteniendo notas de referencia")
        raise HTTPException(status_code=500, detail="No se pudieron obtener las notas") from e


@router.get("/admin/generar/{estudiante_id}/{periodo}")
def generar_boletin_admin(estudiante_id: int, periodo: int):
    try:
        resultado = obtener_boletin_admin_controller(estudiante_id, periodo)
        if not resultado:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error generando boletin admin")
        raise HTTPException(status_code=500, detail="No se pudo generar el boletin") from e
