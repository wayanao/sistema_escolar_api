from pydantic import BaseModel
from typing import List

class BoletinDetalleCreate(BaseModel):
    nota: float
    observacion: str

class BoletinCreate(BaseModel):
    estudiante_id: int
    asignacion_id: int
    periodo: int
    definitiva: float
    detalles: List[BoletinDetalleCreate]
