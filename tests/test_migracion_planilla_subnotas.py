"""Subnotas de la planilla, paso A1: la migracion de las dos tablas nuevas.

Estas pruebas leen el SQL porque CI no usa PostgreSQL. La validez real se
comprueba despues en una rama de Neon (paso A2) y solo entonces se regenera el
esquema base, como exige `docs/MIGRACIONES.md`. Diseño en
`docs/funcionalidades/SUBNOTAS_PLANILLA.md`.
"""

import re
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20261021_planilla_subnotas.sql"
REPOSITORIO = RAIZ / "app" / "repositories" / "subnotas_planilla_repository.py"


def sql():
    assert MIGRACION.exists(), f"Falta la migración {MIGRACION.name}"
    return MIGRACION.read_text(encoding="utf-8")


def sql_normalizado():
    sin_comentarios = re.sub(r"--.*$", "", sql(), flags=re.MULTILINE)
    return " ".join(sin_comentarios.upper().split())


def _tabla(nombre):
    texto = sql_normalizado()
    inicio = texto.index(f"CREATE TABLE IF NOT EXISTS {nombre} (")
    return texto[inicio:texto.index(");", inicio)]


def test_solo_crea_las_dos_tablas_nuevas_y_no_toca_ninguna_existente():
    texto = sql_normalizado()

    creadas = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", texto)
    assert creadas == ["PLANILLA_SUBNOTAS", "PLANILLA_SUBNOTAS_VALORES"]
    sentencias = [s.strip() for s in texto.split(";") if s.strip()]
    assert [s.split()[0] for s in sentencias] == ["CREATE", "CREATE", "CREATE"]
    assert "ALTER TABLE" not in texto
    assert "DROP " not in texto


def test_las_subnotas_cuelgan_de_la_asignacion_y_se_borran_con_ella():
    tabla = _tabla("PLANILLA_SUBNOTAS")

    assert "ASIGNACION_ID INTEGER NOT NULL REFERENCES ASIGNACIONES(ID) ON DELETE CASCADE" in tabla
    assert "PERIODO INTEGER NOT NULL" in tabla
    # El mismo largo que notas_detalle.descripcion, que es el nombre del tipo.
    assert "TIPO_NOTA CHARACTER VARYING(100) NOT NULL" in tabla
    assert "NOMBRE CHARACTER VARYING(60) NOT NULL" in tabla
    assert "CHECK (CHAR_LENGTH(TRIM(NOMBRE)) > 0)" in tabla
    assert "CHECK (CHAR_LENGTH(TRIM(TIPO_NOTA)) > 0)" in tabla


def test_las_calificaciones_se_borran_con_su_subnota_pero_no_con_el_estudiante():
    tabla = _tabla("PLANILLA_SUBNOTAS_VALORES")

    assert (
        "SUBNOTA_ID INTEGER NOT NULL REFERENCES PLANILLA_SUBNOTAS(ID) ON DELETE CASCADE"
        in tabla
    )
    # Igual que notas_detalle: un estudiante con notas no desaparece sin aviso.
    assert "ESTUDIANTE_ID INTEGER NOT NULL REFERENCES ESTUDIANTES(ID)," in tabla
    assert "UNIQUE (SUBNOTA_ID, ESTUDIANTE_ID)" in tabla


def test_una_calificacion_es_una_nota_de_uno_a_cinco_o_una_carita_nunca_las_dos():
    tabla = _tabla("PLANILLA_SUBNOTAS_VALORES")

    assert "NOTA NUMERIC(3,2)," in tabla
    assert "VALORACION CHARACTER VARYING(30)," in tabla
    assert "CHECK (NOTA IS NULL OR (NOTA >= 1 AND NOTA <= 5))" in tabla
    assert "CHECK ((NOTA IS NULL) <> (VALORACION IS NULL))" in tabla


def test_el_nombre_es_unico_por_tipo_con_la_misma_expresion_del_repositorio():
    texto = sql_normalizado()

    assert (
        "CREATE UNIQUE INDEX IF NOT EXISTS IDX_PLANILLA_SUBNOTAS_NOMBRE_UNICO "
        "ON PLANILLA_SUBNOTAS ( ASIGNACION_ID, PERIODO, (LOWER(TRIM(TIPO_NOTA))), "
        "(LOWER(TRIM(NOMBRE))) )"
    ) in texto
    # Si el conteo del controlador comparara distinto que el indice, el 409
    # legible dejaria de coincidir con lo que la base rechaza.
    repositorio = REPOSITORIO.read_text(encoding="utf-8")
    assert "LOWER(TRIM(nombre)) = LOWER(TRIM(%s))" in repositorio
    assert "LOWER(TRIM(tipo_nota)) = LOWER(TRIM(%s))" in repositorio


def test_es_reejecutable():
    texto = sql_normalizado()

    assert texto.count("CREATE TABLE IF NOT EXISTS") == 2
    assert texto.count("CREATE UNIQUE INDEX IF NOT EXISTS") == 1
    assert "CREATE TABLE PLANILLA" not in texto
    assert "CREATE INDEX PLANILLA" not in texto
