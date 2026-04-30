from pydantic import BaseModel
from typing import List, Optional

class BoletinDetalleCreate(BaseModel):
    nota: Optional[float] = None
    observacion: str
    tipo_evaluacion: str = "numerica"
    valoracion: Optional[str] = None

class BoletinCreate(BaseModel):
    estudiante_id: int
    asignacion_id: int
    periodo: int
    definitiva: Optional[float] = None
    tipo_evaluacion: str = "numerica"
    detalles: List[BoletinDetalleCreate]
