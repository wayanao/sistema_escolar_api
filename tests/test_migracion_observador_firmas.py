"""La migracion de la firma del acudiente, fijada por sus decisiones.

Ver docs/funcionalidades/FIRMA_OBSERVADOR.md. Como la de la bitacora, cada
prueba protege algo que, si se deshace, no rompe nada visible: falla en
silencio el dia que hay que defender una firma.
"""
import re
from pathlib import Path

from app.core.firma_observador import MAX_BYTES_IMAGEN
from scripts import apply_tenant_indexes

RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20261027_observador_firmas.sql"


def sql_sin_comentarios():
    """El SQL de verdad: los comentarios nombran cosas (CASCADE, DEFAULT,
    INDEX) que no deben confundirse con codigo."""
    texto = MIGRACION.read_text(encoding="utf-8")
    return " ".join(re.sub(r"--.*$", "", texto, flags=re.MULTILINE).split())


def test_la_migracion_crea_la_tabla_de_firmas():
    assert "CREATE TABLE IF NOT EXISTS observador_firmas" in sql_sin_comentarios()


def test_una_anotacion_tiene_como_maximo_una_firma():
    """Invariante 1 y decision 2."""
    assert "UNIQUE (anotacion_id)" in sql_sin_comentarios()


def test_ningun_borrado_se_lleva_una_firma():
    assert "CASCADE" not in sql_sin_comentarios().upper()


def test_la_firma_cuelga_de_la_anotacion_y_de_quien_la_tomo():
    sql = sql_sin_comentarios()
    assert "REFERENCES observador_anotaciones(id)" in sql
    assert "REFERENCES profesor(id)" in sql
    assert "REFERENCES usuarios(id)" in sql


def test_la_toma_exactamente_una_persona():
    """Profesor o admin, nunca los dos ni ninguno: viven en tablas distintas."""
    assert (
        "CHECK ((tomada_por_profesor_id IS NULL) <> (tomada_por_usuario_id IS NULL))"
        in sql_sin_comentarios()
    )


def test_la_hora_de_la_firma_no_tiene_valor_por_defecto():
    """La pone el servidor en la misma transaccion en que calcula la huella.
    Un DEFAULT dejaria guardar una hora que la huella no cubre."""
    sql = sql_sin_comentarios()
    assert "firmada_en timestamptz NOT NULL," in sql
    assert "DEFAULT" not in sql.upper()


def test_la_base_y_el_codigo_aceptan_el_mismo_tamano_de_imagen():
    assert f"BETWEEN 1 AND {MAX_BYTES_IMAGEN}" in sql_sin_comentarios()


def test_no_crea_indices_aparte():
    """El UNIQUE ya crea el indice que usan la bitacora y la impresion. Un
    indice aqui ademas chocaria con el procedimiento de
    scripts/apply_tenant_indexes.py (ver la migracion de la bitacora)."""
    assert "CREATE INDEX" not in sql_sin_comentarios().upper()
    assert all(tabla != "observador_firmas" for tabla, _, _ in apply_tenant_indexes.INDEXES)
