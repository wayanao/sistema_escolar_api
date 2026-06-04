from typing import Literal

from pydantic import BaseModel


EstadoCurso = Literal["activo", "inactivo"]

class CursoCreate(BaseModel):
    nombre: str
    jornada: str = "Mañana"
    estado: EstadoCurso = "activo"


class CursoEstadoUpdate(BaseModel):
    estado: EstadoCurso
