"""Año lectivo, fase 6.1: decisiones de salida y materias ocultas.

Estas pruebas leen el SQL porque CI no usa PostgreSQL. La validez real del SQL
se comprueba después en una rama de Neon y solo entonces se regenera el esquema
base, como exige ``docs/MIGRACIONES.md``.
"""

import re
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20261008_anios_lectivos_activacion.sql"


def sql():
    assert MIGRACION.exists(), f"Falta la migración {MIGRACION.name}"
    return MIGRACION.read_text(encoding="utf-8")


def sql_normalizado():
    return " ".join(sql().upper().split())


def sql_sin_comentarios():
    return re.sub(r"--.*$", "", sql(), flags=re.MULTILINE)


def test_agrega_una_decision_de_salida_opcional_a_matriculas():
    texto = sql_normalizado()

    sentencia = re.search(
        r"ALTER TABLE MATRICULAS ADD COLUMN IF NOT EXISTS "
        r"ESTADO_SALIDA (.*?);",
        texto,
    )

    assert sentencia is not None
    definicion = sentencia.group(1)
    assert definicion == "VARCHAR(20)"
    assert "NOT NULL" not in definicion
    assert "DEFAULT" not in definicion


def test_la_decision_de_salida_solo_admite_retirado_o_egresado():
    texto = sql_normalizado()

    assert "CONNAME = 'CHK_MATRICULAS_ESTADO_SALIDA'" in texto
    assert (
        "ADD CONSTRAINT CHK_MATRICULAS_ESTADO_SALIDA "
        "CHECK (ESTADO_SALIDA IN ('RETIRADO', 'EGRESADO'))"
    ) in texto


def test_crea_la_tabla_de_materias_ocultas_del_anio():
    texto = sql_normalizado()

    tabla = re.search(
        r"CREATE TABLE IF NOT EXISTS ANIOS_LECTIVOS_MATERIAS_OCULTAS "
        r"\((.*?)\);",
        texto,
    )

    assert tabla is not None
    definicion = tabla.group(1)
    assert "ANIO_LECTIVO_ID INTEGER NOT NULL" in definicion
    assert "MATERIA_ID INTEGER NOT NULL" in definicion
    assert "SERIAL" not in definicion
    assert "TIMESTAMP" not in definicion


def test_una_materia_se_guarda_una_sola_vez_por_anio():
    texto = sql_normalizado()

    assert (
        "CONSTRAINT ANIOS_LECTIVOS_MATERIAS_OCULTAS_PKEY "
        "PRIMARY KEY (ANIO_LECTIVO_ID, MATERIA_ID)"
    ) in texto


def test_las_materias_ocultas_referencian_el_anio_y_la_materia():
    texto = sql_normalizado()

    assert (
        "CONSTRAINT ANIOS_LECTIVOS_MATERIAS_OCULTAS_ANIO_FKEY "
        "FOREIGN KEY (ANIO_LECTIVO_ID) REFERENCES ANIOS_LECTIVOS (ID)"
    ) in texto
    assert (
        "CONSTRAINT ANIOS_LECTIVOS_MATERIAS_OCULTAS_MATERIA_FKEY "
        "FOREIGN KEY (MATERIA_ID) REFERENCES MATERIAS (ID)"
    ) in texto


def test_la_huella_historica_no_se_borra_en_cascada():
    texto = sql_normalizado()

    assert "ON DELETE" not in texto


def test_crea_indice_para_buscar_la_huella_por_materia():
    texto = sql_normalizado()

    assert (
        "CREATE INDEX IF NOT EXISTS "
        "IDX_ANIOS_LECTIVOS_MATERIAS_OCULTAS_MATERIA "
        "ON ANIOS_LECTIVOS_MATERIAS_OCULTAS (MATERIA_ID)"
    ) in texto


def test_es_reejecutable_sin_duplicar_estructura():
    texto = sql_normalizado()

    assert texto.count("ADD COLUMN IF NOT EXISTS") == 1
    assert texto.count("FROM PG_CONSTRAINT") == 1
    assert texto.count("CREATE TABLE IF NOT EXISTS") == 1
    assert texto.count("CREATE INDEX IF NOT EXISTS") == 1


def test_no_cambia_datos_existentes():
    texto = sql_sin_comentarios().upper()

    for operacion in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "DROP"):
        assert not re.search(rf"\b{operacion}\b", texto)
