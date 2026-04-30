from pydantic import BaseModel
from typing import Optional
from datetime import date

class PlanDeClasesCreate(BaseModel):
    asignacion_id: int
    periodo: int = 1
    unidad: str
    proposito: str
    clase: str
    estandar: str
    dba: str
    competencias: str
    actividad_casa: str
    tema: str
    fecha: date

class PlanDeClasesResponse(BaseModel):
    id: int
    asignacion_id: int
    periodo: int
    unidad: str
    proposito: str
    clase: str
    estandar: str
    dba: str
    competencias: str
    actividad_casa: str
    tema: str
    fecha: date
    imagen1: Optional[str] = None
    imagen2: Optional[str] = None
    profesor_id: Optional[int] = None
    profesor: Optional[str] = None
    curso: Optional[str] = None
    materia: Optional[str] = None
