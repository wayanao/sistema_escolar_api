"""Paso 3 de "Listas de Seguimiento por Curso": los esquemas de entrada.

Ver `docs/funcionalidades/LISTAS_SEGUIMIENTO.md`. Fija tres cosas:

- que lo que se guarda es lo que se midio: el recorte de espacios corre antes
  de comprobar la longitud, no despues;
- que los limites del esquema **siguen coincidiendo con los de la tabla**. Las
  dos ultimas pruebas los leen del propio archivo de migracion, porque si se
  separan el sintoma no es un mensaje raro: es un 500 en vez de un 422;
- que el lote no puede traer la misma celda dos veces, que es lo unico que
  impide el error de PostgreSQL al guardar todo en una sentencia.
"""
import re
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from app.schemas.listas_seguimiento import (
    ColumnaSeguimientoCreate,
    LoteDeMarcas,
    MarcaSeguimientoItem,
)


MIGRACION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "20260921_listas_seguimiento.sql"
)

lote = TypeAdapter(LoteDeMarcas)


def celda(columna_id=5, estudiante_id=101, marcado=True, nota=""):
    return {
        "columna_id": columna_id,
        "estudiante_id": estudiante_id,
        "marcado": marcado,
        "nota": nota,
    }


# ---------------------------------------------------------------------------
# El nombre de una columna.
# ---------------------------------------------------------------------------


def test_el_nombre_se_guarda_recortado():
    assert ColumnaSeguimientoCreate(nombre="  Compro el libro  ").nombre == (
        "Compro el libro"
    )


def test_los_espacios_interiores_no_se_tocan():
    """Recortar los extremos es lo que cualquiera espera; reescribir el
    interior, no. Que dos nombres asi cuenten como el mismo lo resuelve el
    indice unico, no este modelo."""
    assert ColumnaSeguimientoCreate(nombre="Asistio  a la cumbre").nombre == (
        "Asistio  a la cumbre"
    )


@pytest.mark.parametrize("vacio", ["", "   ", "\t\n"])
def test_un_nombre_sin_contenido_se_rechaza(vacio):
    """La base no lo haria: la columna es NOT NULL, pero la cadena vacia le
    parece bien, y quedaria una columna sin nombre."""
    with pytest.raises(ValidationError):
        ColumnaSeguimientoCreate(nombre=vacio)


def test_el_nombre_admite_exactamente_cien_caracteres():
    nombre = "A" * 100

    assert ColumnaSeguimientoCreate(nombre=nombre).nombre == nombre


def test_el_nombre_de_ciento_uno_se_rechaza():
    with pytest.raises(ValidationError):
        ColumnaSeguimientoCreate(nombre="A" * 101)


def test_el_nombre_se_mide_despues_de_recortar():
    """Cien caracteres rodeados de espacios entran: lo que se mide es lo que
    se va a guardar, no lo que llego."""
    assert len(ColumnaSeguimientoCreate(nombre="   " + "A" * 100 + "   ").nombre) == 100


# ---------------------------------------------------------------------------
# Una celda.
# ---------------------------------------------------------------------------


def test_marcado_es_obligatorio():
    """Sin defecto a proposito: el lote se guarda con upsert, asi que un
    cliente que se olvidara del campo borraria la marca en vez de dejarla."""
    with pytest.raises(ValidationError):
        MarcaSeguimientoItem(columna_id=5, estudiante_id=101, nota="")


def test_la_nota_puede_no_venir():
    assert MarcaSeguimientoItem(columna_id=5, estudiante_id=101, marcado=True).nota == ""


def test_la_nota_nula_se_vuelve_cadena_vacia():
    """`null` es lo que manda un formulario vacio desde JavaScript. Las dos
    formas se guardan igual para que haya una sola representacion de "sin
    nota"."""
    item = MarcaSeguimientoItem(
        columna_id=5, estudiante_id=101, marcado=False, nota=None
    )

    assert item.nota == ""


def test_la_nota_se_guarda_recortada():
    item = MarcaSeguimientoItem(
        columna_id=5, estudiante_id=101, marcado=True, nota="  Llego tarde  "
    )

    assert item.nota == "Llego tarde"


def test_la_nota_admite_exactamente_doscientos_cuarenta():
    nota = "N" * 240
    item = MarcaSeguimientoItem(
        columna_id=5, estudiante_id=101, marcado=True, nota=nota
    )

    assert item.nota == nota


def test_la_nota_de_doscientos_cuarenta_y_uno_se_rechaza():
    with pytest.raises(ValidationError):
        MarcaSeguimientoItem(
            columna_id=5, estudiante_id=101, marcado=True, nota="N" * 241
        )


def test_el_curso_no_viaja_en_la_celda():
    """Va en la URL. Pydantic ignora lo que no declara, asi que mandarlo no
    hace nada; esta prueba lo fija para que nadie lo empiece a leer del
    cuerpo."""
    item = MarcaSeguimientoItem(
        **celda(), curso_id=999
    )

    assert not hasattr(item, "curso_id")


# ---------------------------------------------------------------------------
# El lote.
# ---------------------------------------------------------------------------


def test_un_lote_vacio_se_rechaza():
    with pytest.raises(ValidationError):
        lote.validate_python([])


def test_un_lote_normal_pasa():
    marcas = lote.validate_python(
        [celda(estudiante_id=101), celda(estudiante_id=102)]
    )

    assert len(marcas) == 2
    assert all(isinstance(m, MarcaSeguimientoItem) for m in marcas)


def test_la_misma_celda_dos_veces_se_rechaza():
    """Es lo unico que impide el error de PostgreSQL al guardar el lote entero
    en una sola sentencia con ON CONFLICT DO UPDATE."""
    with pytest.raises(ValidationError) as error:
        lote.validate_python([celda(nota="una"), celda(nota="otra")])

    assert "misma celda dos veces" in str(error.value)


def test_una_columna_con_varios_alumnos_no_es_repeticion():
    marcas = lote.validate_python(
        [celda(columna_id=5, estudiante_id=101), celda(columna_id=5, estudiante_id=102)]
    )

    assert len(marcas) == 2


def test_un_alumno_en_varias_columnas_no_es_repeticion():
    marcas = lote.validate_python(
        [celda(columna_id=5, estudiante_id=101), celda(columna_id=6, estudiante_id=101)]
    )

    assert len(marcas) == 2


# ---------------------------------------------------------------------------
# Los limites del esquema y los de la tabla, juntos.
#
# Si se separan, el sintoma no es un mensaje raro: lo que la base rechaza y el
# esquema deja pasar llega al usuario como un 500 en vez de un 422.
# ---------------------------------------------------------------------------


def _migracion():
    return MIGRACION.read_text(encoding="utf-8")


def test_el_limite_del_nombre_es_el_de_la_columna():
    assert "nombre character varying(100)" in _migracion()

    ColumnaSeguimientoCreate(nombre="A" * 100)
    with pytest.raises(ValidationError):
        ColumnaSeguimientoCreate(nombre="A" * 101)


def test_el_limite_de_la_nota_es_el_del_check():
    limite = re.search(r"char_length\(nota\) <= (\d+)", _migracion())

    assert limite, "el CHECK de longitud de la nota ya no esta en la migracion"
    assert limite.group(1) == "240"

    MarcaSeguimientoItem(columna_id=5, estudiante_id=101, marcado=True, nota="N" * 240)
    with pytest.raises(ValidationError):
        MarcaSeguimientoItem(
            columna_id=5, estudiante_id=101, marcado=True, nota="N" * 241
        )
