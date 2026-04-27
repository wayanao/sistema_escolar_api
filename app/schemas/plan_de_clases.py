from pydantic import BaseModel
from typing import Optional
from datetime import date

class PlanDeClasesCreate(BaseModel):
    asignacion_id: int
    unidad: str
    proposito: str
    estandar: str
    dba: str
    competencias: str
    tema: str
    fecha: date

class PlanDeClasesResponse(BaseModel):
    id: int
    asignacion_id: int
    unidad: str
    proposito: str
    estandar: str
    dba: str
    competencias: str
    tema: str
    fecha: date
    imagen1: Optional[str] = None
    imagen2: Optional[str] = None