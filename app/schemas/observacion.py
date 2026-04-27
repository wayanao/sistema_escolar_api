from pydantic import BaseModel

class ObservacionCreate(BaseModel):
    estudiante_id: int
    asignacion_id: int
    periodo: int
    conductual: str
    cognitivo: str
    lenguaje: str