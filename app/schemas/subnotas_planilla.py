"""Lo que entra por HTTP en las subnotas de la planilla.

Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`. Igual que en
`listas_seguimiento.py`, **toda regla que la base ya impone se repite aqui**,
para que salga como un 422 con un mensaje util y no como un 500 desde
PostgreSQL:

- `nombre` de 1 a 60 caracteres (`varchar(60)` y su CHECK de no vacio);
- `tipo_nota` de 1 a 100 (`varchar(100)`, el mismo largo que
  `notas_detalle.descripcion`);
- `periodo` desde 1 (`integer NOT NULL`).

Ambos textos se guardan recortados y la longitud se mide despues de recortar.

Lo que depende del curso (si la calificacion es nota o carita, y si la subnota
es de ese tipo) no se puede saber aqui: lo valida el controlador.
"""
from typing import Dict, Literal, Optional, Union

from pydantic import BaseModel, Field, StrictFloat, StrictInt, StrictStr, field_validator


def _recortado(valor):
    return valor.strip() if isinstance(valor, str) else valor


class _ConTipoNota(BaseModel):
    asignacion_id: int
    periodo: int = Field(ge=1)
    tipo_nota: str = Field(min_length=1, max_length=100)

    @field_validator("tipo_nota", mode="before")
    @classmethod
    def _recortar_tipo(cls, valor):
        return _recortado(valor)


class SubnotaCreate(_ConTipoNota):
    """Una subnota nueva para todo el curso (decision 5)."""

    nombre: str = Field(min_length=1, max_length=60)

    @field_validator("nombre", mode="before")
    @classmethod
    def _recortar_nombre(cls, valor):
        return _recortado(valor)


class SubnotaRename(BaseModel):
    """El nombre nuevo de una subnota (P5).

    `asignacion_id` viaja en el cuerpo para comprobar el permiso y el año
    lectivo igual que en las demas rutas de la planilla, y para que solo se
    renombre una subnota de esa clase.
    """

    asignacion_id: int
    nombre: str = Field(min_length=1, max_length=60)

    @field_validator("nombre", mode="before")
    @classmethod
    def _recortar_nombre(cls, valor):
        return _recortado(valor)


# Numeros estrictos: un `true` no se acepta como nota 1, ni un "4" como nota
# 4. El texto es para las caritas.
Calificacion = Optional[Union[StrictInt, StrictFloat, StrictStr]]


class CalificacionesCreate(_ConTipoNota):
    """Las calificaciones de un estudiante en un tipo de nota (P10).

    `valores` va de id de subnota a calificacion: una nota, el codigo de una
    carita o `null` para dejarla vacia. **Solo se tocan las subnotas que
    llegan**: una que no viene conserva lo que tenia. Asi un modal abierto
    antes de que alguien agregara otra subnota no la vacia al guardar.

    `tipo_evaluacion` es lo que pide la pantalla. El nivel del curso manda
    sobre el, igual que en `POST /planilla/nota`.
    """

    estudiante_id: int
    tipo_evaluacion: Literal["numerica", "desarrollo"] = "numerica"
    valores: Dict[int, Calificacion] = Field(min_length=1)
