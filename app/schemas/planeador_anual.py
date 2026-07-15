from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from datetime import date

class PlaneadorAnualBase(BaseModel):

    unidad_tematica: str = ""
    estandar_competencia: str = ""
    contenido: str = ""
    actividades_recursos: str = ""
    fecha: Optional[date] = None

    @field_validator(
        "unidad_tematica",
        "estandar_competencia",
        "contenido",
        "actividades_recursos",
        mode="before",
    )
    @classmethod
    def normalizar_texto(cls, valor):
        return str(valor or "").strip()

    @field_validator("fecha", mode="before")
    @classmethod
    def normalizar_fecha_vacia(cls, valor):
        return None if valor in (None, "") else valor

    @model_validator(mode="after")
    def validar_contenido_y_fecha(self):
        tiene_contenido = any((
            self.unidad_tematica,
            self.estandar_competencia,
            self.contenido,
            self.actividades_recursos,
        ))
        if tiene_contenido and self.fecha is None:
            raise ValueError("Cada fila con contenido debe tener una fecha límite.")
        if self.fecha is not None and not tiene_contenido:
            raise ValueError("Una fecha límite debe acompañar al menos un campo de contenido.")
        return self

class PlaneadorAnualCreate(PlaneadorAnualBase):
    asignacion_id: int

class PlaneadorAnualUpdate(PlaneadorAnualBase):
    pass

class PlaneadorAnual(PlaneadorAnualBase):
    id: int
    asignacion_id: int

    class Config:
        from_attributes = True
