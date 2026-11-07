"""«Mi curso», paso 3: la tabla ``boletin_observacion_general``.

Como ``test_migracion_admisiones.py``, estas pruebas leen el SQL porque CI no
usa PostgreSQL. La validez real se comprueba en una rama de Neon y solo
entonces se regenera el esquema base (``docs/MIGRACIONES.md``). Diseño en
``docs/funcionalidades/MI_CURSO_DIRECTOR.md``.
"""

import re
from pathlib import Path

from app.schemas.director_grupo import LARGO_MAXIMO_OBSERVACION

RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20261107_boletin_observacion_general.sql"


def sql_sin_comentarios():
    assert MIGRACION.exists(), f"Falta la migración {MIGRACION.name}"
    texto = MIGRACION.read_text(encoding="utf-8")
    return "\n".join(linea.split("--")[0] for linea in texto.splitlines())


def compacto(texto):
    return re.sub(r"\s+", " ", texto).strip()


def test_crea_solo_una_tabla_nueva_y_su_indice_sin_tocar_las_demas():
    sql = compacto(sql_sin_comentarios())

    assert "CREATE TABLE IF NOT EXISTS boletin_observacion_general (" in sql
    assert "CREATE INDEX IF NOT EXISTS idx_boletin_observacion_general_periodo" in sql
    # Ninguna sentencia toca lo que ya existe ("ON DELETE CASCADE" es parte de
    # la clave foránea, no una sentencia).
    sentencias = [parte.strip().upper() for parte in sql.split(";") if parte.strip()]
    assert len(sentencias) == 2
    assert sentencias[0].startswith("CREATE TABLE IF NOT EXISTS")
    assert sentencias[1].startswith("CREATE INDEX IF NOT EXISTS")
    for palabra in ("ALTER TABLE", "DROP ", "UPDATE ", "DELETE FROM", "INSERT INTO", "TRUNCATE"):
        assert palabra not in sql.upper(), palabra
    # Sin nombres cualificados: el runner pone el search_path de cada colegio.
    assert "public." not in sql
    assert "tenant_" not in sql


def test_una_observacion_por_estudiante_anio_y_periodo():
    sql = compacto(sql_sin_comentarios())
    assert "UNIQUE (estudiante_id, anio_lectivo_id, periodo)" in sql
    assert "CHECK (periodo BETWEEN 1 AND 4)" in sql


def test_el_largo_maximo_es_el_mismo_del_backend():
    sql = compacto(sql_sin_comentarios())
    assert f"CHECK (char_length(btrim(texto)) BETWEEN 1 AND {LARGO_MAXIMO_OBSERVACION})" in sql
    assert LARGO_MAXIMO_OBSERVACION == 500


def test_se_va_con_el_estudiante_como_boletin_cabecera():
    sql = compacto(sql_sin_comentarios())
    assert "estudiante_id integer NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE" in sql
    assert "anio_lectivo_id integer NOT NULL REFERENCES anios_lectivos(id)," in sql


def test_quien_la_guardo_no_apunta_a_profesor_ni_a_usuarios():
    """El id es de profesor o de usuarios según el rol: sin clave foránea, y
    sin sumar referencias a `profesor` (ver la guardia de profesores)."""
    sql = compacto(sql_sin_comentarios())
    assert "REFERENCES profesor" not in sql
    assert "REFERENCES usuarios" not in sql
    assert "CHECK (actualizado_por_rol IN ('profesor', 'admin'))" in sql
