from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _validar_ids_estudiantes(valores):
    if any(valor <= 0 for valor in valores):
        raise ValueError("Los estudiantes deben tener identificadores positivos.")
    if len(valores) != len(set(valores)):
        raise ValueError("No se puede seleccionar dos veces al mismo estudiante.")
    return valores


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
        return _validar_ids_estudiantes(valores)


class ActivarAnioLectivo(BaseModel):
    """El año que el admin escribe para confirmar la activación (fase 6.3a).

    El backend lo compara con el año que se activa: protege de una pestaña
    vieja o de una llamada por error, además de la confirmación del frontend.
    """

    confirmar_anio: int = Field(ge=2000, le=2100)


class DecisionSalidaEstudiantes(BaseModel):
    """Marca de salida del año que termina; `null` la quita (fase 6.2b).

    Es obligatoria, también para quitarla: así un cuerpo incompleto no borra
    una decisión por accidente.
    """

    estudiante_ids: list[int] = Field(min_length=1)
    estado_salida: Literal["retirado", "egresado"] | None

    @field_validator("estudiante_ids")
    @classmethod
    def validar_estudiantes(cls, valores):
        return _validar_ids_estudiantes(valores)
