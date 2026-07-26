from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional
from datetime import date, datetime


EstadoRevisionPlan = Literal["pendiente", "visto", "con_observaciones", "revisado"]


class PlanDeClasesCreate(BaseModel):
    asignacion_id: int
    version_esperada: Optional[int] = Field(default=None, ge=0)
    periodo: int = 1
    unidad: str = ""
    proposito: str = ""
    clase: str = ""
    estandar: str = ""
    dba: str = ""
    competencias: str = ""
    actividad_casa: str = ""
    tema: str = ""
    fecha: date


class PlanRevisionUpdate(BaseModel):
    estado: Literal["visto", "revisado"]
    version: int = Field(ge=1)
    comentario: Optional[str] = Field(default=None, max_length=3000)

    @field_validator("comentario", mode="before")
    @classmethod
    def normalizar_comentario(cls, value):
        if not isinstance(value, str):
            return value
        return value.strip() or None

    @model_validator(mode="after")
    def validar_comentario_de_revision(self):
        if self.estado != "revisado" and self.comentario:
            raise ValueError("El comentario solo se admite al marcar como revisado")
        return self


class PlanObservacionCreate(BaseModel):
    observacion: str = Field(min_length=1, max_length=3000)
    version: int = Field(ge=1)

    @field_validator("observacion", mode="before")
    @classmethod
    def normalizar_observacion(cls, value):
        if not isinstance(value, str):
            return value
        return value.strip()

class PlanDeClasesResponse(BaseModel):
    id: int
    asignacion_id: int
    periodo: int
    unidad: str = ""
    proposito: str = ""
    clase: str = ""
    estandar: str = ""
    dba: str = ""
    competencias: str = ""
    actividad_casa: str = ""
    tema: str = ""
    fecha: date
    imagen1: Optional[str] = None
    imagen2: Optional[str] = None
    profesor_id: Optional[int] = None
    profesor: Optional[str] = None
    curso: Optional[str] = None
    materia: Optional[str] = None
    estado_revision: EstadoRevisionPlan = "pendiente"
    version_revision: int = 1
    enviado_at: Optional[datetime] = None
    admin_visto_at: Optional[datetime] = None
    revisado_at: Optional[datetime] = None
    total_observaciones: int = 0
    observaciones_no_vistas: int = 0
    ultima_observacion_at: Optional[datetime] = None
