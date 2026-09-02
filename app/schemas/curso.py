from typing import Literal, Optional

from pydantic import BaseModel


EstadoCurso = Literal["activo", "inactivo"]
NivelCurso = Literal["preescolar", "primaria"]

class CursoCreate(BaseModel):
    nombre: str
    jornada: str = "Mañana"
    estado: EstadoCurso = "activo"
    nivel: Optional[NivelCurso] = None


class CursoEstadoUpdate(BaseModel):
    estado: EstadoCurso
