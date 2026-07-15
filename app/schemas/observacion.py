from pydantic import BaseModel, field_validator, model_validator

class ObservacionCreate(BaseModel):
    estudiante_id: int
    asignacion_id: int
    periodo: int
    conductual: str = ""
    cognitivo: str = ""
    lenguaje: str = ""

    @field_validator("conductual", "cognitivo", "lenguaje", mode="before")
    @classmethod
    def normalizar_texto(cls, valor):
        return str(valor or "").strip()

    @model_validator(mode="after")
    def validar_contenido(self):
        if not any((self.conductual, self.cognitivo, self.lenguaje)):
            raise ValueError("Escribe al menos una observación antes de guardar.")
        return self
