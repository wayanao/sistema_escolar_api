from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.controllers.egreso_controller import obtener_egresos, crear_egreso, eliminar_egreso
from app.dependencies import get_current_active_admin

router = APIRouter(prefix="/api/egresos", tags=["Egresos"])

class EgresoCreate(BaseModel):
    concepto: str
    monto: float
    fecha: Optional[date] = None
    categoria: Optional[str] = "Otros"
    notas: Optional[str] = ""

@router.get("/")
def get_egresos(current_admin: dict = Depends(get_current_active_admin)):
    return obtener_egresos()

@router.post("/")
def add_egreso(egreso: EgresoCreate, current_admin: dict = Depends(get_current_active_admin)):
    return crear_egreso(egreso)

@router.delete("/{egreso_id}")
def delete_egreso(egreso_id: int, current_admin: dict = Depends(get_current_active_admin)):
    return eliminar_egreso(egreso_id)