from pydantic import BaseModel

class CursoCreate(BaseModel):
    nombre: str
    matricula: float
    mensualidad: float
    meses: int
    jornada: str = "Mañana"