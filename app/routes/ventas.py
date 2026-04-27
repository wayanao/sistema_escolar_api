from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.controllers.venta_controller import obtener_ventas, crear_venta, eliminar_venta, obtener_ventas_pendientes
from app.dependencies import get_current_active_admin

router = APIRouter(prefix="/api/ventas", tags=["Ventas"])

class VentaDetalleCreate(BaseModel):
    inventario_id: int
    cantidad: int
    precio_unitario: float
    subtotal: float

class VentaCreate(BaseModel):
    estudiante_id: Optional[int] = None
    tipo_venta: str  # 'Contado' o 'Credito'
    total: float
    notas: Optional[str] = ""
    detalles: List[VentaDetalleCreate]

@router.get("/")
def get_ventas(current_admin: dict = Depends(get_current_active_admin)):
    return obtener_ventas()

@router.get("/pendientes/{estudiante_id}")
def get_ventas_pendientes(estudiante_id: int, current_admin: dict = Depends(get_current_active_admin)):
    return obtener_ventas_pendientes(estudiante_id)

@router.post("/")
def add_venta(venta: VentaCreate, current_admin: dict = Depends(get_current_active_admin)):
    return crear_venta(venta)

@router.delete("/{venta_id}")
def delete_venta(venta_id: int, current_admin: dict = Depends(get_current_active_admin)):
    return eliminar_venta(venta_id)