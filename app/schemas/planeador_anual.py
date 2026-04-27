from pydantic import BaseModel
from typing import Optional
from datetime import date

class PlaneadorAnualBase(BaseModel):

    unidad_tematica: Optional[str] = None
    estandar_competencia: Optional[str] = None
    contenido: Optional[str] = None
    actividades_recursos: Optional[str] = None
    fecha: Optional[date] = None

class PlaneadorAnualCreate(PlaneadorAnualBase):
    asignacion_id: int

class PlaneadorAnualUpdate(PlaneadorAnualBase):
    pass

class PlaneadorAnual(PlaneadorAnualBase):
    id: int
    asignacion_id: int

    class Config:
        from_attributes = True