from typing import Literal, Optional

from pydantic import BaseModel, Field


EstadoCurso = Literal["activo", "inactivo"]
NivelCurso = Literal["preescolar", "primaria"]

class CursoCreate(BaseModel):
    nombre: str
    jornada: str = "Mañana"
    estado: EstadoCurso = "activo"
    nivel: Optional[NivelCurso] = None
    director_grupo_id: Optional[int] = None


class CursoCreateConAnio(CursoCreate):
    """Cuerpo exclusivo del alta; editar un curso no permite moverlo de año."""

    anio_lectivo_id: Optional[int] = Field(default=None, gt=0)


class CursoEstadoUpdate(BaseModel):
    estado: EstadoCurso
