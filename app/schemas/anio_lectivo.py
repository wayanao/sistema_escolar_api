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


class ConfirmacionAnioLectivo(BaseModel):
    """El año que el admin escribe para confirmar un cambio de estado del año.

    El backend lo compara con el año que cambia: protege de una pestaña vieja
    o de una llamada por error, además de la confirmación del frontend. Lo
    usan reabrir y volver a cerrar (fase 6.4a).
    """

    confirmar_anio: int = Field(ge=2000, le=2100)


class ActivarAnioLectivo(ConfirmacionAnioLectivo):
    """La misma confirmación, para activar el año siguiente (fase 6.3a)."""


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
