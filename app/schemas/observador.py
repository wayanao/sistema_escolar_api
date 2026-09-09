"""Entradas de la bitacora del observador. Ver
`docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`.

**`profesor_id` no aparece aqui, y es a proposito.** Sale siempre del token. Si
viajara en el cuerpo, un profesor podria firmar una anotacion con el nombre de
otro en un documento pensado para servir ante una reclamacion. Pydantic ignora
los campos que no declara, asi que mandarlo no hace nada; hay prueba que lo fija.

`materia` tampoco aparece: por ahora no se rellena. El motivo -que el servidor
no puede deducirla y que preguntarla es friccion- esta en el documento.
"""
from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.texto_observador import normalizar_texto


class _AnotacionBase(BaseModel):
    positiva: bool
    conductual: str = ""
    cognitivo: str = ""
    lenguaje: str = ""

    @field_validator("conductual", "cognitivo", "lenguaje", mode="before")
    @classmethod
    def corregir_mayusculas(cls, valor):
        """Se guarda el texto **ya corregido**, no el original.

        La profesora ve la misma correccion al salir del campo, asi que lo que
        aprueba con los ojos es lo que queda escrito. Decidido el 2026-09-08.
        """
        return normalizar_texto(valor)

    @model_validator(mode="after")
    def validar_contenido(self):
        """Al menos una de las tres dimensiones con contenido.

        Se conserva la validacion de `observaciones`: una anotacion vacia no
        dice nada y ensuciaria la bitacora. Vive en el esquema y no en el
        repositorio a proposito -es el hallazgo 4 de la capa 7.0-: bajarla
        convertiria este 422 en un 500.
        """
        if not any((self.conductual, self.cognitivo, self.lenguaje)):
            raise ValueError("Escribe al menos una observación antes de guardar.")
        return self


class AnotacionCreate(_AnotacionBase):
    estudiante_id: int

    # Mismo rango que el CHECK de la tabla. Aqui sale como 422 con un mensaje
    # util; sin esto, un periodo imposible reventaria en PostgreSQL y saldria
    # como 500.
    periodo: int = Field(ge=1, le=4)


class AnotacionUpdate(_AnotacionBase):
    """La edicion no cambia de estudiante ni de periodo.

    El periodo es la etiqueta del momento en que se escribio; moverla de
    periodo seria reescribir cuando paso, no corregir como se conto.
    """
