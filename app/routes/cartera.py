from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_active_admin
from app.controllers.cartera_mora_controller import (
    reporte_cartera_vencida,
    resumen_cartera_vencida,
)
from app.controllers.puntualidad_controller import reporte_puntualidad

router = APIRouter(tags=["Cartera"], dependencies=[Depends(get_current_active_admin)])


@router.get("/cartera/mora")
def get_cartera_mora(
    curso_id: Optional[int] = Query(default=None),
    anio_lectivo_id: Annotated[Optional[int], Query(gt=0)] = None,
):
    """Lista detallada de estudiantes en mora. Sin `anio_lectivo_id`, del año activo."""
    try:
        return reporte_cartera_vencida(curso_id, anio_lectivo_id=anio_lectivo_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/cartera/mora/resumen")
def get_resumen_cartera_mora(
    anio_lectivo_id: Annotated[Optional[int], Query(gt=0)] = None,
):
    """Resumen agregado (para el dashboard). Sin `anio_lectivo_id`, del año activo."""
    try:
        return resumen_cartera_vencida(anio_lectivo_id=anio_lectivo_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/cartera/puntualidad")
def get_puntualidad_pagos():
    """Quién paga a tiempo sus cuotas mensuales del año activo (panel del admin):
    el total, el ranking de cursos y los mejores de cada curso y del colegio.
    Solo lee. Regla: `app/services/puntualidad.py`."""
    return reporte_puntualidad()
