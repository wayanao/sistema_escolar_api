from typing import Literal

from pydantic import BaseModel

EstadoInventario = Literal["activo", "inactivo"]


class InventarioBase(BaseModel):
    nombre: str
    costo: float
    precio_venta: float
    stock_actual: int
    estado: EstadoInventario = "activo"

class InventarioCreate(InventarioBase):
    pass

class InventarioUpdate(InventarioBase):
    pass


class InventarioEstadoUpdate(BaseModel):
    estado: EstadoInventario
