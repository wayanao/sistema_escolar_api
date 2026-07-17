from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import date

from typing import List

class MetodoPago(BaseModel):
    tipo: str
    monto: float
    nota: Optional[str] = None


class PagoAplicacionCreate(BaseModel):
    tipo_pago_id: int
    periodo: date
    monto: float = Field(gt=0)

class PagoCreate(BaseModel):
    estudiante_id: int
    monto: float
    descripcion: Optional[str] = None
    fecha: Optional[date] = None
    venta_id: Optional[int] = None
    metodos: Optional[List[MetodoPago]] = None
    aplicaciones: Optional[List[PagoAplicacionCreate]] = None

class PagoAnular(BaseModel):
    motivo: str


class PagoAdelantadoCreate(BaseModel):
    estudiante_id: int
    tipo_pago_id: int
    cantidad_meses: Optional[int] = Field(default=None, ge=1, le=12)
    monto_distribuir: Optional[float] = Field(default=None, gt=0)
    fecha: Optional[date] = None
    metodos: List[MetodoPago] = Field(min_length=1)

    @model_validator(mode="after")
    def validar_metodos(self):
        if any(float(metodo.monto or 0) <= 0 for metodo in self.metodos):
            raise ValueError("Cada método de pago debe tener un monto mayor a cero.")
        if (self.cantidad_meses is None) == (self.monto_distribuir is None):
            raise ValueError(
                "Debes enviar cantidad_meses o monto_distribuir, pero no ambos."
            )
        return self
