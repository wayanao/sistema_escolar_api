from pydantic import BaseModel
from datetime import date
from typing import Literal

class AsistenciaCreate(BaseModel):
    estudiante_id: int
    asignacion_id: int
    fecha: date
    estado: Literal["presente", "ausente"]
    periodo: int = 1
