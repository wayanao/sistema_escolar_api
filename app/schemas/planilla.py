from pydantic import BaseModel, Field
from typing import Optional

# 🎯 Registrar nota desde planilla
class NotaPlanillaCreate(BaseModel):
    estudiante_id: int
    asignacion_id: int
    nota: Optional[float] = Field(None, ge=1, le=5)
    descripcion: str
    periodo: Optional[int] = 1
    tipo_evaluacion: str = "numerica"
    valoracion: Optional[str] = None
