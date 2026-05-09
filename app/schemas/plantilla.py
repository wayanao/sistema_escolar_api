from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


TIPOS_PLANTILLA = {
    "boletin",
    "voucher_pago",
    "volante_venta",
    "reporte_estudiante",
    "observaciones",
    "planeador",
}


class PlantillaBase(BaseModel):
    tipo: str
    nombre: str
    config_json: Dict[str, Any] = Field(default_factory=dict)


class PlantillaCreate(PlantillaBase):
    pass


class PlantillaUpdate(BaseModel):
    nombre: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None


class Plantilla(PlantillaBase):
    id: int
    codigo: Optional[str] = None
    es_predefinida: bool = False
    activa: bool = False
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True
