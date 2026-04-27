from pydantic import BaseModel
from datetime import date
from typing import Optional

class NominaCreate(BaseModel):
    profesor_id: int
    salario_base: float
    deduccion_prestamos: float = 0.0
    otros_descuentos: float = 0.0
    bonificaciones: float = 0.0
    notas: Optional[str] = None
