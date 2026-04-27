from pydantic import BaseModel
from typing import Optional
from datetime import date

from typing import List, Dict

class MetodoPago(BaseModel):
    tipo: str
    monto: float

class PagoCreate(BaseModel):
    estudiante_id: int
    monto: float
    descripcion: Optional[str] = None
    fecha: Optional[date] = None
    venta_id: Optional[int] = None
    metodos: Optional[List[MetodoPago]] = None
