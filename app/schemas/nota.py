from pydantic import BaseModel, Field
from typing import List

class NotaCreate(BaseModel):
    estudiante_id: int
    asignacion_id: int
    nota: float = Field(..., ge=0, le=5)  # 🔥 rango válido
    descripcion: str

class ActividadNota(BaseModel):
    id: int
    descripcion: str
    nota: float = Field(..., ge=0, le=5)

class MateriaBoletin(BaseModel):
    id: int
    asignacion_id: int
    actividades: List[ActividadNota]

class BoletinGuardar(BaseModel):
    estudiante_id: int
    periodo: int = 1
    materias: List[MateriaBoletin]