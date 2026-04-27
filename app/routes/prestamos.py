from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.controllers.prestamo_controller import obtener_prestamos, crear_prestamo, eliminar_prestamo, actualizar_estado_prestamo
from app.dependencies import get_current_active_admin

router = APIRouter(prefix="/api/prestamos", tags=["Prestamos"])

class PrestamoCreate(BaseModel):
    profesor_id: int
    monto: float
    fecha: Optional[date] = None
    estado: Optional[str] = "Pendiente"
    notas: Optional[str] = ""

class EstadoUpdate(BaseModel):
    estado: str

@router.get("/")
def get_prestamos(current_admin: dict = Depends(get_current_active_admin)):
    return obtener_prestamos()

@router.post("/")
def add_prestamo(prestamo: PrestamoCreate, current_admin: dict = Depends(get_current_active_admin)):
    return crear_prestamo(prestamo)

@router.put("/{prestamo_id}/estado")
def update_estado(prestamo_id: int, estado: EstadoUpdate, current_admin: dict = Depends(get_current_active_admin)):
    return actualizar_estado_prestamo(prestamo_id, estado.estado)

@router.delete("/{prestamo_id}")
def delete_prestamo(prestamo_id: int, current_admin: dict = Depends(get_current_active_admin)):
    return eliminar_prestamo(prestamo_id)