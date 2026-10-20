"""SISBÉN y lugar de residencia, paso S1: las columnas nuevas de ``estudiantes``.

Ocho datos opcionales de la ficha: si tiene SISBÉN, su grupo, subgrupo y nivel,
y el barrio, municipio, zona y punto de referencia de donde vive. ``direccion``
no cambia.

Estas pruebas leen el SQL porque CI no usa PostgreSQL. La validez real del SQL
y de sus reglas se comprueba después en una rama de Neon y solo entonces se
regenera el esquema base, como exige ``docs/MIGRACIONES.md``. Diseño en
``docs/funcionalidades/SISBEN_RESIDENCIA.md``.
"""

import re
from pathlib import Path

import pytest


RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20261019_estudiantes_sisben_residencia.sql"

COLUMNAS = {
    "SISBEN": "BOOLEAN",
    "SISBEN_GRUPO": "VARCHAR(1)",
    "SISBEN_SUBGRUPO": "VARCHAR(3)",
    "SISBEN_NIVEL": "SMALLINT",
    "BARRIO": "VARCHAR(150)",
    "MUNICIPIO": "VARCHAR(100)",
    "ZONA_RESIDENCIA": "VARCHAR(10)",
    "PUNTO_REFERENCIA": "VARCHAR(255)",
}

REGLAS = {
    "CHK_ESTUDIANTES_SISBEN_GRUPO": (
        "CHECK (SISBEN_GRUPO IN ('A', 'B', 'C', 'D'))"
    ),
    "CHK_ESTUDIANTES_SISBEN_SUBGRUPO": (
        "CHECK (SISBEN_SUBGRUPO IS NULL OR (SISBEN_GRUPO IS NOT NULL "
        "AND LEFT(SISBEN_SUBGRUPO, 1) = SISBEN_GRUPO "
        "AND SISBEN_SUBGRUPO ~ '^[A-D][1-9][0-9]?$'))"
    ),
    "CHK_ESTUDIANTES_SISBEN_NIVEL": "CHECK (SISBEN_NIVEL BETWEEN 1 AND 3)",
    "CHK_ESTUDIANTES_SISBEN_CLASIFICACION": (
        "CHECK (SISBEN IS TRUE OR (SISBEN_GRUPO IS NULL "
        "AND SISBEN_SUBGRUPO IS NULL AND SISBEN_NIVEL IS NULL))"
    ),
    "CHK_ESTUDIANTES_ZONA_RESIDENCIA": (
        "CHECK (ZONA_RESIDENCIA IN ('URBANA', 'RURAL'))"
    ),
}


def sql():
    assert MIGRACION.exists(), f"Falta la migración {MIGRACION.name}"
    return MIGRACION.read_text(encoding="utf-8")


def sql_sin_comentarios():
    return re.sub(r"--.*$", "", sql(), flags=re.MULTILINE)


def sql_normalizado():
    return " ".join(sql_sin_comentarios().upper().split())


@pytest.mark.parametrize("columna,tipo", COLUMNAS.items())
def test_agrega_cada_columna_opcional_y_sin_valor_por_defecto(columna, tipo):
    texto = sql_normalizado()

    sentencia = re.search(
        rf"ADD COLUMN IF NOT EXISTS {columna} ([^,;]*)[,;]", texto
    )

    assert sentencia is not None, f"Falta la columna {columna}"
    # Sin NOT NULL ni DEFAULT: los estudiantes que ya existen quedan "sin dato"
    # y la tabla no se reescribe.
    assert sentencia.group(1) == tipo


def test_no_toca_la_direccion_de_siempre():
    texto = sql_normalizado()

    assert "DIRECCION" not in texto


@pytest.mark.parametrize("nombre,regla", REGLAS.items())
def test_cada_regla_se_agrega_solo_si_falta(nombre, regla):
    texto = sql_normalizado()

    assert f"CONNAME = '{nombre}'" in texto
    assert f"ADD CONSTRAINT {nombre} {regla}" in texto


def test_las_reglas_se_agregan_despues_de_las_columnas():
    texto = sql_normalizado()

    ultima_columna = max(
        texto.index(f"ADD COLUMN IF NOT EXISTS {columna} ") for columna in COLUMNAS
    )
    primera_regla = min(texto.index(f"ADD CONSTRAINT {nombre} ") for nombre in REGLAS)
    assert ultima_columna < primera_regla


def test_las_reglas_miran_la_tabla_de_estudiantes():
    texto = sql_normalizado()

    assert texto.count("CONRELID = 'ESTUDIANTES'::REGCLASS") == len(REGLAS)


def test_solo_toca_la_tabla_de_estudiantes():
    texto = sql_normalizado()

    tablas = set(re.findall(r"ALTER TABLE ([A-Z_]+)", texto))
    assert tablas == {"ESTUDIANTES"}
    assert "CREATE TABLE" not in texto
    # Nadie busca ni filtra por estos datos todavía: sin índices.
    assert "CREATE INDEX" not in texto
    assert "CREATE UNIQUE INDEX" not in texto


def test_es_reejecutable_sin_duplicar_estructura():
    texto = sql_normalizado()

    assert texto.count("ADD COLUMN IF NOT EXISTS") == len(COLUMNAS)
    assert texto.count("ADD COLUMN") == len(COLUMNAS)
    # PostgreSQL no ofrece ADD CONSTRAINT IF NOT EXISTS: se comprueba antes.
    assert texto.count("FROM PG_CONSTRAINT") == len(REGLAS)
    assert texto.count("ADD CONSTRAINT") == len(REGLAS)


def test_no_cambia_ni_borra_datos_existentes():
    texto = sql_sin_comentarios().upper()

    for operacion in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "DROP"):
        assert not re.search(rf"\b{operacion}\b", texto)
