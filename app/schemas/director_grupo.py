"""«Mi curso» del director de grupo (docs/funcionalidades/MI_CURSO_DIRECTOR.md)."""

from pydantic import BaseModel, Field, field_validator

# Decidido con el usuario el 2026-11-07: lo que cabe en los tres renglones de
# la caja "Observación general" del boletín impreso. La migración
# 20261107_boletin_observacion_general.sql tiene el mismo límite.
LARGO_MAXIMO_OBSERVACION = 500


class ObservacionGeneralIn(BaseModel):
    """La observación general de un estudiante. Vacía (o solo espacios) borra
    la que había."""

    texto: str = Field(default="", max_length=LARGO_MAXIMO_OBSERVACION)

    @field_validator("texto", mode="before")
    @classmethod
    def _limpiar(cls, valor):
        if valor is None:
            return ""
        if isinstance(valor, str):
            # Fin de línea de Windows a uno solo, y sin espacios en los bordes:
            # el largo se cuenta sobre lo que de verdad se guarda.
            return valor.replace("\r\n", "\n").strip()
        return valor
