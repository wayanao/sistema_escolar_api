"""Lo que entra por HTTP en Admisiones (entrevista de admisión).

Ver `docs/funcionalidades/ENTREVISTA_ADMISION.md`, paso E2.

El criterio es el de `listas_seguimiento.py`: **toda regla que la base ya
impone se repite aquí**, para que salga como un 422 con un mensaje útil en vez
de reventar dentro de PostgreSQL y llegar como un 500. La de la base es la que
manda; la de aquí es la que se lee. Los límites de texto son los `VARCHAR` de
`migrations/20261013_admisiones.sql`.

- Los textos se recortan antes de medirlos. Un texto opcional vacío se guarda
  como `NULL`: un documento `''` contaría como repetido en el índice único
  por año, y un campo en blanco no dice nada.
- La autorización de datos (Ley 1581 de 2012) es obligatoria al registrar y
  al editar: no se puede quitar. Si la familia la retira, la admisión se borra
  (decisión 9).
- Ningún cuerpo trae el resultado, el motivo, el año ni el enlace al
  estudiante: el resultado tiene su propia ruta (paso E3), el año viaja en la
  ruta y el enlace lo pone la matrícula. Lo que llegue de más se ignora.
"""
from datetime import date
from typing import Annotated, Literal, Optional, get_args

from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


ResultadoAdmision = Literal["pendiente", "aprobado", "no_aprobado"]
RESULTADOS_ADMISION = get_args(ResultadoAdmision)

MENSAJE_AUTORIZACION_OBLIGATORIA = (
    "La autorización de datos es obligatoria: sin ella no se puede registrar "
    "al aspirante."
)
MENSAJE_MOTIVO_OBLIGATORIO = 'Para marcar "No aprobado" hay que escribir el motivo.'


def _recortado(valor):
    return valor.strip() if isinstance(valor, str) else valor


def _recortado_o_nulo(valor):
    if isinstance(valor, str):
        return valor.strip() or None
    return valor


def _obligatorio(maximo):
    return Annotated[
        str,
        BeforeValidator(_recortado),
        StringConstraints(min_length=1, max_length=maximo),
    ]


def _opcional(maximo=None):
    texto = str if maximo is None else Annotated[str, StringConstraints(max_length=maximo)]
    return Annotated[Optional[texto], BeforeValidator(_recortado_o_nulo)]


class AdmisionCreate(BaseModel):
    """Registrar un aspirante: sus datos y la autorización. Queda pendiente.

    El orden de los campos es el de `admisiones_repository.COLUMNAS_ASPIRANTE`
    (una prueba lo exige).
    """

    nombre: _obligatorio(100)
    apellido: _obligatorio(100)
    tipo_documento: _opcional(50) = None
    documento_identidad: _opcional(20) = None
    fecha_nacimiento: Optional[date] = None
    curso_id: Optional[int] = Field(default=None, gt=0)
    acudiente_nombre: _opcional(150) = None
    acudiente_parentesco: _opcional(50) = None
    acudiente_telefono: _opcional(50) = None
    autoriza_datos: bool
    autoriza_nombre: _obligatorio(150)

    @field_validator("autoriza_datos")
    @classmethod
    def exigir_autorizacion(cls, valor):
        if not valor:
            raise ValueError(MENSAJE_AUTORIZACION_OBLIGATORIA)
        return valor


class AdmisionUpdate(AdmisionCreate):
    """Editar el aspirante y su entrevista. No cambia el resultado.

    Es un reemplazo completo, como `PUT /estudiantes/{id}`: lo que no llega
    queda vacío. El orden de los campos nuevos es el de
    `admisiones_repository.COLUMNAS_ENTREVISTA`.
    """

    fecha_entrevista: Optional[date] = None
    # Se escribe a mano (decisión 10): quien entrevista puede no tener usuario.
    entrevistador: _opcional(150) = None
    asistentes: _opcional(250) = None
    colegio_anterior: _opcional(150) = None
    anio_cursado_anterior: _opcional(50) = None
    pre_escolar_anterior: _opcional(50) = None
    ebp_anterior: _opcional(50) = None
    motivo_retiro_anterior: _opcional() = None
    paz_salvo_anterior: _opcional(10) = None
    ocupacion_padre: _opcional(100) = None
    ocupacion_madre: _opcional(100) = None
    vive_con: _opcional(250) = None
    expectativas: _opcional() = None
    observaciones: _opcional() = None


class ResultadoAdmisionUpdate(BaseModel):
    """El resultado de la entrevista (paso E3).

    "No aprobado" exige el motivo (no discriminación, T-510 de 1994), igual
    que `chk_admisiones_motivo_no_aprobado` en la base. Volver a "pendiente"
    se permite mientras la admisión no esté matriculada.
    """

    resultado: ResultadoAdmision
    motivo_resultado: _opcional() = None

    @model_validator(mode="after")
    def exigir_motivo(self):
        if self.resultado == "no_aprobado" and self.motivo_resultado is None:
            raise ValueError(MENSAJE_MOTIVO_OBLIGATORIO)
        return self
