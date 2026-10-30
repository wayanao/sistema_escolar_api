"""Entradas de la bitacora del observador. Ver
`docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`.

**`profesor_id` no aparece aqui, y es a proposito.** Sale siempre del token. Si
viajara en el cuerpo, un profesor podria firmar una anotacion con el nombre de
otro en un documento pensado para servir ante una reclamacion. Pydantic ignora
los campos que no declara, asi que mandarlo no hace nada; hay prueba que lo fija.

`materia` tampoco aparece: por ahora no se rellena. El motivo -que el servidor
no puede deducirla y que preguntarla es friccion- esta en el documento.

`positiva` tampoco, desde el 2026-09-09: el usuario quito la marca de buena o
mala. La columna sigue en la tabla, como `materia`, y la lectura la sigue
devolviendo; simplemente ya no se pide ni se rellena. Pydantic ignora los campos
que no declara, asi que un cliente viejo que la mande no rompe nada.
"""
from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.firma_observador import decodificar_imagen
from app.core.texto_observador import normalizar_texto


class _AnotacionBase(BaseModel):
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


class _FirmaBase(BaseModel):
    """Quien firma y su firma: lo comun a firmar una anotacion o varias. Ver
    `docs/funcionalidades/FIRMA_OBSERVADOR.md`.

    **Quien toma la firma, la fecha y la hora no aparecen aqui**, igual que
    `profesor_id` en la anotacion: salen del token y del servidor
    (invariante 4). Si viajaran en el cuerpo, cualquiera podria fechar una
    firma o ponerla a nombre de otro. Pydantic ignora lo que no declara.
    """

    firmante_nombre: str = Field(min_length=1, max_length=150)
    firmante_tipo_documento: str = Field(min_length=1, max_length=50)
    firmante_documento: str = Field(min_length=1, max_length=50)
    firmante_parentesco: str = Field(min_length=1, max_length=50)
    # 100 KB de PNG en base64 son unos 136.600 caracteres; el prefijo
    # `data:image/png;base64,` suma 22. Cortar aqui evita decodificar algo
    # enorme solo para rechazarlo despues.
    imagen: str = Field(min_length=1, max_length=140_000)

    @field_validator(
        "firmante_nombre",
        "firmante_tipo_documento",
        "firmante_documento",
        "firmante_parentesco",
        mode="before",
    )
    @classmethod
    def quitar_espacios_sobrantes(cls, valor):
        """Sin espacios al principio, al final ni repetidos: «  Ana   Gomez »
        se guarda como «Ana Gomez», y un campo de solo espacios queda vacio y
        se rechaza."""
        if isinstance(valor, str):
            return " ".join(valor.split())
        return valor

    @field_validator("imagen")
    @classmethod
    def validar_imagen(cls, valor):
        """Un PNG aceptable o un 422 con un mensaje que se puede mostrar.

        Vive en el esquema, como la validacion del contenido de la anotacion:
        mas abajo, una imagen mala seria un 500.
        """
        decodificar_imagen(valor)
        return valor


class FirmaAnotacionCreate(_FirmaBase):
    """La firma del acudiente sobre una anotacion.

    `version` es la que la pantalla recibio con la bitacora: si la anotacion
    cambio desde entonces, la firma se rechaza.
    """

    version: str = Field(min_length=1, max_length=64)


class AnotacionAFirmar(BaseModel):
    """Una de las anotaciones de una firma de periodo, con la version que se
    mostro de ella."""

    id: int = Field(gt=0)
    version: str = Field(min_length=1, max_length=64)


class FirmaVariasCreate(_FirmaBase):
    """Una sola firma del acudiente para varias anotaciones del mismo
    estudiante: las pendientes de un periodo (decision 2, ampliada el
    2026-10-27).

    La pantalla manda **la lista exacta que mostro**, cada una con su version,
    y no el numero del periodo: si el servidor eligiera las anotaciones, una
    escrita mientras el acudiente leia entraria en la firma sin que nadie se
    la hubiera mostrado.

    Hasta 50: un periodo de un alumno no llega a tanto, y el limite evita
    pedidos desmedidos.
    """

    anotaciones: list[AnotacionAFirmar] = Field(min_length=1, max_length=50)

    @field_validator("anotaciones")
    @classmethod
    def sin_repetidas(cls, valor):
        ids = [anotacion.id for anotacion in valor]
        if len(ids) != len(set(ids)):
            raise ValueError("Una anotación viene repetida.")
        return valor
