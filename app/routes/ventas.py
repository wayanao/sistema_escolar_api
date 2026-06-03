from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.controllers.venta_controller import (
    anular_venta,
    crear_venta,
    obtener_ventas,
    obtener_ventas_paginado,
    obtener_ventas_pendientes,
)
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

class VentaAnular(BaseModel):
    motivo: str

@router.get("/")
def get_ventas(
    limit: Annotated[Optional[int], Query(ge=1, le=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    busqueda: Optional[str] = None,
    estudiante_id: Optional[int] = None,
    estado: Optional[str] = None,
    current_admin: dict = Depends(get_current_active_admin),
):
    if limit is not None:
        return obtener_ventas_paginado(
            limit=limit,
            offset=offset,
            busqueda=busqueda,
            estudiante_id=estudiante_id,
            estado=estado,
        )
    return obtener_ventas()

@router.get("/pendientes/{estudiante_id}")
def get_ventas_pendientes(estudiante_id: int, current_admin: dict = Depends(get_current_active_admin)):
    return obtener_ventas_pendientes(estudiante_id)

@router.post("/")
def add_venta(venta: VentaCreate, current_admin: dict = Depends(get_current_active_admin)):
    return crear_venta(venta)

@router.delete("/{venta_id}")
def delete_venta(venta_id: int, current_admin: dict = Depends(get_current_active_admin)):
    raise HTTPException(
        status_code=405,
        detail="Las ventas no se eliminan físicamente. Usa POST /api/ventas/{venta_id}/anular."
    )

@router.post("/{venta_id}/anular")
def anular_venta_route(
    venta_id: int,
    data: VentaAnular,
    current_admin: dict = Depends(get_current_active_admin),
):
    try:
        return anular_venta(venta_id, data.motivo, current_admin["id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
