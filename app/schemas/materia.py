from typing import Literal

from pydantic import BaseModel


EstadoMateria = Literal["activo", "inactivo"]


class MateriaEstadoUpdate(BaseModel):
    estado: EstadoMateria
