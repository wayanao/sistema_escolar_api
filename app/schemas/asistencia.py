from pydantic import BaseModel
from datetime import date

class AsistenciaCreate(BaseModel):
    estudiante_id: int
    asignacion_id: int
    fecha: date
    estado: str
    periodo: int = 1