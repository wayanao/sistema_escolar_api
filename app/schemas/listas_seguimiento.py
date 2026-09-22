"""Lo que entra por HTTP en Listas de Seguimiento.

Ver `docs/funcionalidades/LISTAS_SEGUIMIENTO.md`.

El criterio de este modulo es el mismo que el de `observador.py`: **toda regla
que la base ya impone se repite aqui**, para que salga como un 422 con un
mensaje util en vez de reventar dentro de PostgreSQL y llegar al usuario como
un 500. Son dos guardas de la misma regla, no una duplicada de mas: la de la
base es la que manda, la de aqui es la que se lee.

Lo que se repite, y de donde sale cada limite:

- `nombre` a 100 caracteres, que es el `VARCHAR(100)` de
  `listas_seguimiento_columnas`.
- `nota` a 240 caracteres, que es el CHECK
  `chk_listas_seguimiento_marcas_nota_longitud`.
- El lote de marcas sin celdas repetidas. Esta no espeja un limite de la base
  sino que **evita un error de PostgreSQL**: `guardar_marcas` escribe el lote
  entero en una sola sentencia con `ON CONFLICT DO UPDATE`, y ahi el motor
  aborta con "ON CONFLICT DO UPDATE command cannot affect row a second time"
  si la misma celda viene dos veces. Sin esta guarda ese 422 que promete el
  documento seria un 500.

`curso_id` no aparece en ningun modelo: viaja en la ruta, no en el cuerpo. Que
una marca pertenezca de verdad al curso de la URL lo comprueba el controlador,
que es quien puede preguntarle a la base.
"""
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, field_validator


def _recortado(valor):
    """Quita los espacios de los extremos. Deja pasar lo que no sea texto.

    Corre **antes** de medir la longitud, asi que un nombre que solo se pasa
    por espacios sobrantes se acepta en vez de rechazarse por largo. Lo que se
    mide es lo que se va a guardar.
    """
    return valor.strip() if isinstance(valor, str) else valor


class ColumnaSeguimientoCreate(BaseModel):
    """El nombre de una columna nueva.

    Se guarda **ya recortado**: lo que el administrador ve escrito es lo que
    queda en la base. Los espacios interiores no se tocan -recortar los
    extremos es lo que cualquiera espera; reescribir el interior, no-. Que
    "Asistio  a la cumbre" y "Asistio a la cumbre" cuenten como el mismo
    nombre lo resuelve el indice unico, no este modelo.

    `min_length=1` se mide despues de recortar, asi que un nombre de puros
    espacios se rechaza. La base no lo haria: la columna es `NOT NULL`, pero
    la cadena vacia es un valor perfectamente valido para PostgreSQL, y
    quedaria una columna sin nombre imposible de identificar en pantalla.
    """

    nombre: str = Field(min_length=1, max_length=100)

    @field_validator("nombre", mode="before")
    @classmethod
    def recortar_nombre(cls, valor):
        return _recortado(valor)


class MarcaSeguimientoItem(BaseModel):
    """Una celda: el cruce de una columna con un alumno.

    `marcado` es obligatorio a proposito, sin valor por defecto. Con un
    defecto de `False`, un cliente que se olvidara del campo **borraria** la
    marca en vez de dejarla como estaba, y el lote se guarda con upsert: lo
    que llega pisa lo que habia.

    `nota` acepta que no venga, y acepta `null`, que es lo que manda un
    formulario vacio desde JavaScript. Las dos formas se guardan como cadena
    vacia para que haya **una sola** representacion de "sin nota" aguas abajo.
    """

    columna_id: int
    estudiante_id: int
    marcado: bool
    nota: str = Field(default="", max_length=240)

    @field_validator("nota", mode="before")
    @classmethod
    def normalizar_nota(cls, valor):
        if valor is None:
            return ""
        return _recortado(valor)


def _sin_celdas_repetidas(marcas):
    """Rechaza el lote si la misma celda viene dos veces.

    No es una manina de limpieza: es lo que impide el error de PostgreSQL
    descrito arriba. Se podria "arreglar" quedandose con la ultima aparicion,
    y seria peor -el cliente creeria que guardo dos cosas distintas y solo
    quedo una, sin aviso-.
    """
    vistas = set()
    for marca in marcas:
        celda = (marca.columna_id, marca.estudiante_id)
        if celda in vistas:
            raise ValueError(
                "El lote trae la misma celda dos veces "
                f"(columna {marca.columna_id}, estudiante {marca.estudiante_id})."
            )
        vistas.add(celda)
    return marcas


LoteDeMarcas = Annotated[
    list[MarcaSeguimientoItem],
    Field(min_length=1),
    AfterValidator(_sin_celdas_repetidas),
]
"""El cuerpo de `POST /listas-seguimiento/{curso_id}/marcas`.

Es una lista pelada, el mismo formato que ya usa `POST /asistencia`, y no un
objeto con la lista dentro: cambiarlo romperia el contrato que fija el
documento.

Las dos reglas del lote -no vacio y sin celdas repetidas- viven aqui y no en
la ruta. `app/routes/asistencia.py` las tiene en la ruta, pero eso esta
documentado como un defecto conocido de esa capa, no como el patron a copiar.
"""
