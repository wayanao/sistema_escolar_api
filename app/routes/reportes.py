from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user
from app.controllers.reportes_controller import (
    reporte_general_controller,
    reporte_estado_cuenta_curso_controller,
    reporte_ingresos_mes_controller,
    reporte_ingresos_rango_controller
)

router = APIRouter(tags=["Reportes"], dependencies=[Depends(get_current_user)]) 

# 📊 Reporte general del sistema
@router.get("/reportes/general")
async def reporte_general():
    try:
        data = reporte_general_controller()
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 📊 Estado de cuenta por curso
@router.get("/reportes/estado-cuenta/{curso_id}")
async def reporte_estado_cuenta_curso(curso_id: int):
    try:
        data = reporte_estado_cuenta_curso_controller(curso_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 📊 Reporte ingresos mes
@router.get("/reportes/ingresos-mes/{mes}")
async def reporte_ingresos_mes(mes: str):
    try:
        data = reporte_ingresos_mes_controller(mes)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 📊 Reporte ingresos rango
@router.get("/reportes/ingresos-rango")
async def reporte_ingresos_rango(inicio: str, fin: str):
    try:
        data = reporte_ingresos_rango_controller(inicio, fin)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
