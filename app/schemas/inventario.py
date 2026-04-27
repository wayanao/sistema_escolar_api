from pydantic import BaseModel

class InventarioBase(BaseModel):
    nombre: str
    costo: float
    precio_venta: float
    stock_actual: int

class InventarioCreate(InventarioBase):
    pass

class InventarioUpdate(InventarioBase):
    pass
