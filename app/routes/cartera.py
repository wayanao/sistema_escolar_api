from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_active_admin
from app.controllers.cartera_mora_controller import (
    reporte_cartera_vencida,
    resumen_cartera_vencida,
)

router = APIRouter(tags=["Cartera"], dependencies=[Depends(get_current_active_admin)])


@router.get("/cartera/mora")
def get_cartera_mora(curso_id: Optional[int] = Query(default=None)):
    """Lista detallada de estudiantes en mora."""
    return reporte_cartera_vencida(curso_id)


@router.get("/cartera/mora/resumen")
def get_resumen_cartera_mora():
    """Resumen agregado (para el dashboard)."""
    return resumen_cartera_vencida()
