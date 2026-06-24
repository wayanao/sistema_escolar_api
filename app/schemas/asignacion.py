from pydantic import BaseModel, Field
from typing import Optional

# 🎯 Schema para asignar profesor a curso
class AsignacionCreate(BaseModel):
    profesor_id: int
    curso_id: int
    materia_id: int
    dia: Optional[str] = None
    horas: Optional[int] = None
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None

class AsignacionEdit(BaseModel):
    profesor_id: int
    curso_id: int
    materia_id: int
    dia: Optional[str] = None
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None


class OrdenBoletinItem(BaseModel):
    materia_id: int = Field(gt=0)


class OrdenBoletinUpdate(BaseModel):
    materias: list[OrdenBoletinItem]
