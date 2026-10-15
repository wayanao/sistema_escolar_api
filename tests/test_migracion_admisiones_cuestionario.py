"""Entrevista de admisión, paso E9: la columna ``admisiones.cuestionario``.

Guarda en un solo bloque (JSON) las respuestas a las preguntas del anexo del
colegio. Qué preguntas y qué respuestas son válidas lo revisa el backend en el
paso E10; la base solo exige que sea un bloque.

Estas pruebas leen el SQL porque CI no usa PostgreSQL. La validez real del SQL
y de su regla se comprueba después en una rama de Neon y solo entonces se
regenera el esquema base, como exige ``docs/MIGRACIONES.md``. Diseño en
``docs/funcionalidades/ENTREVISTA_ADMISION.md``, "Preguntas del anexo".
"""

import re
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20261014_admisiones_cuestionario.sql"


def sql():
    assert MIGRACION.exists(), f"Falta la migración {MIGRACION.name}"
    return MIGRACION.read_text(encoding="utf-8")


def sql_sin_comentarios():
    return re.sub(r"--.*$", "", sql(), flags=re.MULTILINE)


def sql_normalizado():
    return " ".join(sql_sin_comentarios().upper().split())


def test_agrega_el_bloque_de_respuestas_vacio_por_defecto():
    texto = sql_normalizado()

    sentencia = re.search(
        r"ALTER TABLE ADMISIONES ADD COLUMN IF NOT EXISTS CUESTIONARIO (.*?);",
        texto,
    )

    assert sentencia is not None
    # NOT NULL con un vacío por defecto: las admisiones que ya existen quedan
    # con el bloque vacío y "sin responder" nunca es NULL.
    assert sentencia.group(1) == "JSONB NOT NULL DEFAULT '{}'::JSONB"


def test_el_bloque_siempre_es_un_objeto():
    texto = sql_normalizado()

    assert "CONNAME = 'CHK_ADMISIONES_CUESTIONARIO_OBJETO'" in texto
    assert "CONRELID = 'ADMISIONES'::REGCLASS" in texto
    assert (
        "ADD CONSTRAINT CHK_ADMISIONES_CUESTIONARIO_OBJETO "
        "CHECK (JSONB_TYPEOF(CUESTIONARIO) = 'OBJECT')"
    ) in texto


def test_la_regla_se_agrega_despues_de_la_columna():
    texto = sql_normalizado()

    assert texto.index("ADD COLUMN IF NOT EXISTS CUESTIONARIO") < texto.index(
        "ADD CONSTRAINT CHK_ADMISIONES_CUESTIONARIO_OBJETO"
    )


def test_solo_toca_la_tabla_de_admisiones():
    texto = sql_normalizado()

    tablas = re.findall(r"ALTER TABLE ([A-Z_]+)", texto)
    assert tablas == ["ADMISIONES", "ADMISIONES"]
    assert "CREATE TABLE" not in texto
    # Nadie busca por una pregunta suelta: no hace falta un índice.
    assert "CREATE INDEX" not in texto
    assert "CREATE UNIQUE INDEX" not in texto


def test_es_reejecutable_sin_duplicar_estructura():
    texto = sql_normalizado()

    assert texto.count("ADD COLUMN IF NOT EXISTS") == 1
    assert texto.count("ADD COLUMN") == 1
    # PostgreSQL no ofrece ADD CONSTRAINT IF NOT EXISTS: se comprueba antes.
    assert texto.count("FROM PG_CONSTRAINT") == 1
    assert texto.count("ADD CONSTRAINT") == 1


def test_no_cambia_ni_borra_datos_existentes():
    texto = sql_sin_comentarios().upper()

    for operacion in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "DROP"):
        assert not re.search(rf"\b{operacion}\b", texto)
