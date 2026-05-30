from pydantic import BaseModel, Field

class NotaCreate(BaseModel):
    estudiante_id: int
    asignacion_id: int
    nota: float = Field(..., ge=0, le=5)  # 🔥 rango válido
    descripcion: str
