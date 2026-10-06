"""Año lectivo, fase 5.2: columnas que guardan el origen de una copia.

Estas pruebas leen el SQL porque CI no usa PostgreSQL. La validez real del SQL
se comprueba después en una rama de Neon y solo entonces se regenera el esquema
base, como exige ``docs/MIGRACIONES.md``.
"""

import re
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20261006_anios_lectivos_origenes.sql"


def sql():
    assert MIGRACION.exists(), f"Falta la migración {MIGRACION.name}"
    return MIGRACION.read_text(encoding="utf-8")


def sql_normalizado():
    return " ".join(sql().upper().split())


def sql_sin_comentarios():
    return re.sub(r"--.*$", "", sql(), flags=re.MULTILINE)


def test_agrega_solo_las_dos_columnas_de_origen_y_admiten_null():
    texto = sql_normalizado()
    columnas = re.findall(
        r"ALTER TABLE (\w+) ADD COLUMN IF NOT EXISTS (\w+) INTEGER\s*;",
        texto,
    )

    assert set(columnas) == {
        ("CURSOS", "CURSO_ORIGEN_ID"),
        ("TIPOS_DE_PAGOS", "TIPO_PAGO_ORIGEN_ID"),
    }
    assert len(columnas) == 2

    for tabla, columna in columnas:
        sentencia = re.search(
            rf"ALTER TABLE {tabla} ADD COLUMN IF NOT EXISTS {columna} (.*?);",
            texto,
        ).group(1)
        assert "NOT NULL" not in sentencia
        assert "DEFAULT" not in sentencia


def test_curso_origen_es_clave_foranea_autorreferente():
    texto = sql_normalizado()

    assert "CONNAME = 'CURSOS_CURSO_ORIGEN_ID_FKEY'" in texto
    assert (
        "ADD CONSTRAINT CURSOS_CURSO_ORIGEN_ID_FKEY "
        "FOREIGN KEY (CURSO_ORIGEN_ID) REFERENCES CURSOS (ID)"
    ) in texto


def test_tipo_pago_origen_es_clave_foranea_autorreferente():
    texto = sql_normalizado()

    assert "CONNAME = 'TIPOS_DE_PAGOS_TIPO_PAGO_ORIGEN_ID_FKEY'" in texto
    assert (
        "ADD CONSTRAINT TIPOS_DE_PAGOS_TIPO_PAGO_ORIGEN_ID_FKEY "
        "FOREIGN KEY (TIPO_PAGO_ORIGEN_ID) REFERENCES TIPOS_DE_PAGOS (ID)"
    ) in texto


def test_las_claves_no_borran_la_huella_del_origen_en_cascada():
    texto = sql_sin_comentarios().upper()

    assert "ON DELETE" not in texto


def test_crea_los_dos_indices_de_busqueda_por_origen():
    texto = sql_normalizado()

    assert (
        "CREATE INDEX IF NOT EXISTS IDX_CURSOS_CURSO_ORIGEN "
        "ON CURSOS (CURSO_ORIGEN_ID)"
    ) in texto
    assert (
        "CREATE INDEX IF NOT EXISTS IDX_TIPOS_DE_PAGOS_TIPO_PAGO_ORIGEN "
        "ON TIPOS_DE_PAGOS (TIPO_PAGO_ORIGEN_ID)"
    ) in texto


def test_es_reejecutable_si_una_ejecucion_anterior_quedo_incompleta():
    texto = " ".join(sql_sin_comentarios().upper().split())

    assert texto.count("ADD COLUMN IF NOT EXISTS") == 2
    assert texto.count("FROM PG_CONSTRAINT") == 2
    assert texto.count("ADD CONSTRAINT") == 2
    assert texto.count("CREATE INDEX IF NOT EXISTS") == 2


def test_no_rellena_ni_borra_datos_existentes():
    texto = sql_sin_comentarios().upper()

    for operacion in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "DROP"):
        assert not re.search(rf"\b{operacion}\b", texto)
