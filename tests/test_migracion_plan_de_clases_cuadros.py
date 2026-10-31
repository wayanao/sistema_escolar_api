"""Nombres de los cuadros del plan de clase, paso 1: la migracion de la tabla nueva.

Estas pruebas leen el SQL porque CI no usa PostgreSQL. La validez real se
comprueba despues en una rama de Neon y solo entonces se regenera el esquema
base, como exige `docs/MIGRACIONES.md`. Diseño en
`docs/funcionalidades/NOMBRES_CUADROS_PLAN.md`.
"""

import re
from pathlib import Path

from app.core.cuadros_plan_de_clases import LARGO_AYUDA, LARGO_NOMBRE


RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20261031_plan_de_clases_cuadros.sql"
REPOSITORIO = RAIZ / "app" / "repositories" / "cuadros_plan_de_clases_repository.py"


def sql():
    assert MIGRACION.exists(), f"Falta la migración {MIGRACION.name}"
    return MIGRACION.read_text(encoding="utf-8")


def sql_normalizado():
    sin_comentarios = re.sub(r"--.*$", "", sql(), flags=re.MULTILINE)
    return " ".join(sin_comentarios.upper().split())


def _tabla():
    texto = sql_normalizado()
    inicio = texto.index("CREATE TABLE IF NOT EXISTS PLAN_DE_CLASES_CUADROS (")
    return texto[inicio:texto.rindex(");")]


def test_solo_crea_la_tabla_nueva_y_no_toca_ninguna_existente():
    texto = sql_normalizado()

    creadas = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", texto)
    assert creadas == ["PLAN_DE_CLASES_CUADROS"]
    sentencias = [s.strip() for s in texto.split(";") if s.strip()]
    assert [s.split()[0] for s in sentencias] == ["CREATE"]
    assert "ALTER TABLE" not in texto
    assert "DROP " not in texto
    assert "INDEX" not in texto


def test_un_nombre_por_cuadro_y_las_claves_no_van_en_la_base():
    """La lista de claves vive en `app/core/cuadros_plan_de_clases.py`."""
    tabla = _tabla()

    assert "CLAVE CHARACTER VARYING(30) PRIMARY KEY" in tabla
    assert "CLAVE IN" not in tabla


def test_los_largos_son_los_del_backend():
    tabla = _tabla()

    assert f"NOMBRE CHARACTER VARYING({LARGO_NOMBRE}) NOT NULL" in tabla
    assert "CHECK (CHAR_LENGTH(BTRIM(NOMBRE)) > 0)" in tabla
    assert f"AYUDA CHARACTER VARYING({LARGO_AYUDA}) DEFAULT '' NOT NULL" in tabla


def test_borrar_un_admin_no_borra_los_nombres():
    tabla = _tabla()

    assert "ACTUALIZADO_POR INTEGER REFERENCES USUARIOS(ID) ON DELETE SET NULL" in tabla
    assert (
        "ACTUALIZADO_EN TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL"
    ) in tabla


def test_el_insert_del_repositorio_nombra_columnas_de_la_tabla():
    repositorio = " ".join(REPOSITORIO.read_text(encoding="utf-8").split())
    tabla = _tabla()

    assert (
        "INSERT INTO plan_de_clases_cuadros (clave, nombre, ayuda, actualizado_por)"
    ) in repositorio
    for columna in ("CLAVE", "NOMBRE", "AYUDA", "ACTUALIZADO_POR"):
        assert f"{columna} " in tabla


def test_es_reejecutable():
    texto = sql_normalizado()

    assert texto.count("CREATE TABLE IF NOT EXISTS") == 1
    assert "CREATE TABLE PLAN" not in texto
