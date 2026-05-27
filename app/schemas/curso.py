from pydantic import BaseModel

class CursoCreate(BaseModel):
    nombre: str
    jornada: str = "Mañana"
