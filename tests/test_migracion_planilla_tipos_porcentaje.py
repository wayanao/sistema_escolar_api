"""Porcentajes por tipo de nota, paso B2b: la migracion de la tabla nueva.

Estas pruebas leen el SQL porque CI no usa PostgreSQL. La validez real se
comprueba despues en una rama de Neon (paso B3) y solo entonces se regenera el
esquema base, como exige `docs/MIGRACIONES.md`. Diseño en
`docs/funcionalidades/SUBNOTAS_PLANILLA.md` (PB1 a PB3).
"""

import re
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20261022_planilla_tipos_porcentaje.sql"
REPOSITORIO = RAIZ / "app" / "repositories" / "porcentajes_planilla_repository.py"


def sql():
    assert MIGRACION.exists(), f"Falta la migración {MIGRACION.name}"
    return MIGRACION.read_text(encoding="utf-8")


def sql_normalizado():
    sin_comentarios = re.sub(r"--.*$", "", sql(), flags=re.MULTILINE)
    return " ".join(sin_comentarios.upper().split())


def _tabla():
    texto = sql_normalizado()
    inicio = texto.index("CREATE TABLE IF NOT EXISTS PLANILLA_TIPOS_PORCENTAJE (")
    return texto[inicio:texto.index(");", inicio)]


def test_solo_crea_la_tabla_nueva_y_no_toca_ninguna_existente():
    texto = sql_normalizado()

    creadas = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", texto)
    assert creadas == ["PLANILLA_TIPOS_PORCENTAJE"]
    sentencias = [s.strip() for s in texto.split(";") if s.strip()]
    assert [s.split()[0] for s in sentencias] == ["CREATE", "CREATE"]
    assert "ALTER TABLE" not in texto
    assert "DROP " not in texto


def test_cuelga_de_la_asignacion_y_se_borra_con_ella():
    tabla = _tabla()

    assert "ASIGNACION_ID INTEGER NOT NULL REFERENCES ASIGNACIONES(ID) ON DELETE CASCADE" in tabla
    assert "PERIODO INTEGER NOT NULL" in tabla
    # El mismo largo que notas_detalle.descripcion, que es el nombre del tipo.
    assert "TIPO_NOTA CHARACTER VARYING(100) NOT NULL" in tabla
    assert "CHECK (CHAR_LENGTH(TRIM(TIPO_NOTA)) > 0)" in tabla


def test_el_porcentaje_es_un_entero_de_1_a_100():
    """PB2. La suma de 100 no puede ser un CHECK (mira varias filas): la
    cuida el controlador, con la clase bloqueada."""
    tabla = _tabla()

    assert "PORCENTAJE SMALLINT NOT NULL" in tabla
    assert "CHECK (PORCENTAJE >= 1 AND PORCENTAJE <= 100)" in tabla


def test_un_porcentaje_por_tipo_con_la_misma_expresion_del_repositorio():
    texto = sql_normalizado()

    assert (
        "CREATE UNIQUE INDEX IF NOT EXISTS IDX_PLANILLA_TIPOS_PORCENTAJE_TIPO_UNICO "
        "ON PLANILLA_TIPOS_PORCENTAJE ( ASIGNACION_ID, PERIODO, (LOWER(TRIM(TIPO_NOTA))) )"
    ) in texto
    # El ON CONFLICT del guardado tiene que nombrar exactamente esas columnas,
    # o PostgreSQL no encuentra el indice y la sentencia falla.
    repositorio = " ".join(REPOSITORIO.read_text(encoding="utf-8").split())
    assert "ON CONFLICT (asignacion_id, periodo, (LOWER(TRIM(tipo_nota))))" in repositorio
    assert "LOWER(TRIM(tipo_nota)) = LOWER(TRIM(%s))" in repositorio


def test_es_reejecutable():
    texto = sql_normalizado()

    assert texto.count("CREATE TABLE IF NOT EXISTS") == 1
    assert texto.count("CREATE UNIQUE INDEX IF NOT EXISTS") == 1
    assert "CREATE TABLE PLANILLA" not in texto
    assert "CREATE INDEX PLANILLA" not in texto
