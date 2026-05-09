from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class BrandingBase(BaseModel):
    nombre_institucion: Optional[str] = ""
    eslogan: Optional[str] = ""
    direccion: Optional[str] = ""
    telefono: Optional[str] = ""
    email: Optional[str] = ""
    nit: Optional[str] = ""
    sitio_web: Optional[str] = ""
    color_primario: Optional[str] = "#0f314f"
    color_secundario: Optional[str] = "#526775"
    configuracion_extra: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BrandingUpdate(BrandingBase):
    pass


class Branding(BrandingBase):
    id: int
    logo_principal_url: Optional[str] = None
    logo_secundario_url: Optional[str] = None

    class Config:
        from_attributes = True
