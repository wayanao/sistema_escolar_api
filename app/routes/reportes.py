from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from app.dependencies import get_current_active_admin
from app.controllers.reportes_controller import (
    reporte_general_controller,
    reporte_egresos_rango_controller,
    reporte_estado_cuenta_curso_controller,
    reporte_ingresos_mes_controller,
    reporte_ingresos_rango_controller
)

router = APIRouter(tags=["Reportes"], dependencies=[Depends(get_current_active_admin)])

# 📊 Reporte general del sistema
@router.get("/reportes/general")
def reporte_general():
    try:
        data = reporte_general_controller()
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 📊 Estado de cuenta por curso
@router.get("/reportes/estado-cuenta/{curso_id}")
def reporte_estado_cuenta_curso(curso_id: int):
    try:
        data = reporte_estado_cuenta_curso_controller(curso_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 📊 Reporte ingresos mes
@router.get("/reportes/ingresos-mes/{mes}")
def reporte_ingresos_mes(
    mes: str,
    limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    try:
        data = reporte_ingresos_mes_controller(mes, limit=limit, offset=offset)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 📊 Reporte ingresos rango
@router.get("/reportes/ingresos-rango")
def reporte_ingresos_rango(
    inicio: str,
    fin: str,
    limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    try:
        data = reporte_ingresos_rango_controller(inicio, fin, limit=limit, offset=offset)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reportes/egresos-rango")
def reporte_egresos_rango(
    inicio: str,
    fin: str,
    limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    try:
        data = reporte_egresos_rango_controller(inicio, fin, limit=limit, offset=offset)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
