from typing import Literal, Optional

from pydantic import BaseModel


EstadoCurso = Literal["activo", "inactivo"]
NivelCurso = Literal["preescolar", "primaria"]

class CursoCreate(BaseModel):
    nombre: str
    jornada: str = "Mañana"
    estado: EstadoCurso = "activo"
    nivel: Optional[NivelCurso] = None
    director_grupo_id: Optional[int] = None


class CursoEstadoUpdate(BaseModel):
    estado: EstadoCurso
