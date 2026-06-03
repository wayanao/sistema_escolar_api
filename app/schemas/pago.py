from pydantic import BaseModel
from typing import Optional
from datetime import date

from typing import List

class MetodoPago(BaseModel):
    tipo: str
    monto: float
    nota: Optional[str] = None

class PagoCreate(BaseModel):
    estudiante_id: int
    monto: float
    descripcion: Optional[str] = None
    fecha: Optional[date] = None
    venta_id: Optional[int] = None
    metodos: Optional[List[MetodoPago]] = None

class PagoAnular(BaseModel):
    motivo: str
