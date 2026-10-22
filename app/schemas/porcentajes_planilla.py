"""Lo que entra por HTTP en los porcentajes por tipo de nota.

Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md` (PB2 y PB8). Como en las
subnotas, `tipo_nota` llega recortado y mide de 1 a 100 (`varchar(100)`), y
`periodo` empieza en 1.

`porcentaje` admite solo numeros: un `true` o un "40" no son porcentaje. Que
sea un entero de 1 a 100 lo valida el controlador, para responder con un
mensaje en español y no con el detalle tecnico del validador. Es obligatorio
aunque sea `null`: quitar un porcentaje se pide a proposito, no por olvido.
"""
from typing import Optional, Union

from pydantic import BaseModel, Field, StrictFloat, StrictInt, field_validator


class PorcentajeTipoUpdate(BaseModel):
    """El porcentaje de un tipo de nota, o `null` para quitarlo."""

    asignacion_id: int
    periodo: int = Field(ge=1)
    tipo_nota: str = Field(min_length=1, max_length=100)
    porcentaje: Optional[Union[StrictInt, StrictFloat]]

    @field_validator("tipo_nota", mode="before")
    @classmethod
    def _recortar_tipo(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor
