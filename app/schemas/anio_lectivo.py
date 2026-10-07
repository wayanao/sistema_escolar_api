from pydantic import BaseModel, Field, field_validator


class CopiarConfiguracionAnio(BaseModel):
    """Opciones adicionales; cursos y conceptos se copian siempre."""

    copiar_precios: bool = False
    copiar_carga_academica: bool = False
    copiar_directores: bool = False


class PromocionEstudiantes(BaseModel):
    """Selección explícita que pasa de un curso activo al siguiente año."""

    curso_origen_id: int = Field(gt=0)
    curso_destino_id: int = Field(gt=0)
    estudiante_ids: list[int] = Field(min_length=1)

    @field_validator("estudiante_ids")
    @classmethod
    def validar_estudiantes(cls, valores):
        if any(valor <= 0 for valor in valores):
            raise ValueError("Los estudiantes deben tener identificadores positivos.")
        if len(valores) != len(set(valores)):
            raise ValueError("No se puede seleccionar dos veces al mismo estudiante.")
        return valores
