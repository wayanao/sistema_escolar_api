"""La migracion de las firmas guardadas para el boletin, fijada por sus
decisiones. Ver docs/funcionalidades/FIRMAS_BOLETIN.md.

Cada prueba protege algo que, si se deshace, no rompe nada visible: una firma
de rector(a) que se duplica, una imagen que crece sin limite o una tabla
existente que cambia sin que nadie lo decida.
"""
import re
from pathlib import Path

from app.core.firma_observador import MAX_BYTES_IMAGEN
from scripts import apply_tenant_indexes

RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20261112_firmas_boletin.sql"


def sql_sin_comentarios():
    """El SQL de verdad: los comentarios nombran cosas (CASCADE, usuarios,
    ALTER) que no deben confundirse con codigo."""
    texto = MIGRACION.read_text(encoding="utf-8")
    return " ".join(re.sub(r"--.*$", "", texto, flags=re.MULTILINE).split())


def test_crea_las_dos_tablas_y_no_toca_ninguna_existente():
    sql = sql_sin_comentarios()
    assert "CREATE TABLE IF NOT EXISTS firma_institucional" in sql
    assert "CREATE TABLE IF NOT EXISTS firmas_profesores" in sql
    assert sql.count("CREATE TABLE") == 2
    assert "ALTER TABLE" not in sql.upper()
    assert "DROP" not in sql.upper()


def test_el_colegio_tiene_una_sola_firma_institucional():
    sql = sql_sin_comentarios()
    assert "CONSTRAINT firma_institucional_pkey PRIMARY KEY (id)" in sql
    assert "CHECK (id = 1)" in sql


def test_cada_profesor_tiene_como_maximo_una_firma_y_se_va_con_el():
    sql = sql_sin_comentarios()
    assert "CONSTRAINT firmas_profesores_pkey PRIMARY KEY (profesor_id)" in sql
    assert (
        "FOREIGN KEY (profesor_id) REFERENCES profesor(id) ON DELETE CASCADE" in sql
    )


def test_quien_subio_la_firma_institucional_no_bloquea_borrar_un_usuario():
    """Igual que boletin_observacion_general: el id se guarda sin clave
    foranea."""
    sql = sql_sin_comentarios()
    assert "actualizado_por_id integer NOT NULL" in sql
    assert "REFERENCES usuarios" not in sql


def test_la_base_y_el_codigo_aceptan_el_mismo_tamano_de_imagen():
    assert MAX_BYTES_IMAGEN == 102400
    assert sql_sin_comentarios().count(f"BETWEEN 1 AND {MAX_BYTES_IMAGEN}") == 2


def test_no_crea_indices_aparte():
    """Las claves primarias ya crean los indices que se usan (id = 1 y
    profesor_id)."""
    assert "CREATE INDEX" not in sql_sin_comentarios().upper()
    assert all(
        tabla not in ("firma_institucional", "firmas_profesores")
        for tabla, _, _ in apply_tenant_indexes.INDEXES
    )
