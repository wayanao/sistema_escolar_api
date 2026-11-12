"""Entrada de las firmas guardadas para el boletin. Ver
`docs/funcionalidades/FIRMAS_BOLETIN.md`.

**Ni `profesor_id` ni `usuario_id` aparecen aqui, y es a proposito.** Salen
siempre de la sesion: si viajaran en el cuerpo, un profesor podria guardar su
garabato como firma de otro. Pydantic ignora los campos que no declara, asi
que mandarlos no hace nada; hay prueba que lo fija.
"""
from pydantic import BaseModel, Field, field_validator

from app.core.firmas import decodificar_firma


class FirmaIn(BaseModel):
    """La imagen de la firma, como PNG en base64 (con o sin el prefijo
    `data:image/png;base64,`)."""

    # 100 KB de PNG en base64 son unos 136.600 caracteres; el prefijo suma 22.
    # Cortar aqui evita decodificar algo enorme solo para rechazarlo despues.
    imagen: str = Field(min_length=1, max_length=140_000)

    @field_validator("imagen")
    @classmethod
    def validar_imagen(cls, valor):
        """Un PNG aceptable o un 422 con un mensaje que se puede mostrar.

        Vive en el esquema, como en la firma del acudiente: mas abajo, una
        imagen mala seria un 500.
        """
        decodificar_firma(valor)
        return valor
