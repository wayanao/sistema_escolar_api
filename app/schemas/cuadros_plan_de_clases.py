"""Lo que entra por HTTP al renombrar los cuadros del plan de clase.

Ver `docs/funcionalidades/NOMBRES_CUADROS_PLAN.md`. Los textos llegan
recortados. Las reglas (claves validas, largos, ayuda solo en los cuadros de
texto) las revisa `app/core/cuadros_plan_de_clases.py` desde el controlador,
para responder con un mensaje en español y no con el detalle tecnico del
validador.
"""
from pydantic import BaseModel, Field, field_validator

from app.core.cuadros_plan_de_clases import CLAVES


class CuadroPlan(BaseModel):
    """Un cuadro renombrado."""

    clave: str
    nombre: str
    ayuda: str = ""

    @field_validator("clave", "nombre", "ayuda", mode="before")
    @classmethod
    def _recortar(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor


class CuadrosPlanUpdate(BaseModel):
    """La lista completa de cuadros renombrados; vacia vuelve a los originales.

    Nunca hay mas cuadros que claves: con mas, alguno sobra o se repite.
    """

    cuadros: list[CuadroPlan] = Field(max_length=len(CLAVES))
