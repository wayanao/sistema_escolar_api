from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Annotated, Optional
from datetime import date
from app.controllers.egreso_controller import (
    actualizar_egreso,
    crear_egreso,
    eliminar_egreso,
    obtener_egresos,
)
from app.dependencies import get_current_active_admin

router = APIRouter(prefix="/api/egresos", tags=["Egresos"])

class EgresoCreate(BaseModel):
    concepto: str
    monto: float
    fecha: Optional[date] = None
    categoria: Optional[str] = "Otros"
    notas: Optional[str] = ""

@router.get("/")
def get_egresos(
    fecha_desde: Annotated[Optional[date], Query()] = None,
    fecha_hasta: Annotated[Optional[date], Query()] = None,
    current_admin: dict = Depends(get_current_active_admin),
):
    hoy = date.today()
    desde = fecha_desde or hoy
    hasta = fecha_hasta or fecha_desde or hoy

    if desde > hasta:
        raise HTTPException(status_code=422, detail="La fecha desde no puede ser mayor que la fecha hasta.")

    return obtener_egresos(fecha_desde=desde, fecha_hasta=hasta)

@router.post("/")
def add_egreso(egreso: EgresoCreate, current_admin: dict = Depends(get_current_active_admin)):
    try:
        return crear_egreso(egreso)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.put("/{egreso_id}")
def update_egreso(egreso_id: int, egreso: EgresoCreate, current_admin: dict = Depends(get_current_active_admin)):
    try:
        return actualizar_egreso(egreso_id, egreso)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.delete("/{egreso_id}")
def delete_egreso(egreso_id: int, current_admin: dict = Depends(get_current_active_admin)):
    resultado = eliminar_egreso(egreso_id)
    raise HTTPException(status_code=405, detail=resultado["error"])
