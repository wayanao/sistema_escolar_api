"""La migracion de la bitacora del observador, fijada por sus decisiones.

Ver docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md. Cada prueba de aqui protege
una decision tomada con el usuario que, si se deshace, no rompe nada visible:
falla en silencio y solo se nota cuando ya se perdio historial de un alumno.
"""
import re
from pathlib import Path

from scripts import apply_tenant_indexes


RAIZ = Path(__file__).resolve().parents[1]
MIGRACION = RAIZ / "migrations" / "20260908_observador_anotaciones.sql"
MIGRACION_MATERIA = RAIZ / "migrations" / "20260908_observador_anotaciones_materia.sql"


def sin_comentarios(texto):
    return re.sub(r"--.*$", "", texto, flags=re.MULTILINE)


def sql_materia():
    return sin_comentarios(MIGRACION_MATERIA.read_text(encoding="utf-8"))


def sql_sin_comentarios():
    """El SQL de verdad. Los comentarios explican decisiones y nombran cosas
    (CASCADE, UNIQUE, asignacion_id) que no deben confundirse con codigo."""
    return sin_comentarios(MIGRACION.read_text(encoding="utf-8"))


def test_la_migracion_crea_la_tabla_de_la_bitacora():
    assert "CREATE TABLE IF NOT EXISTS observador_anotaciones" in sql_sin_comentarios()


def test_ningun_borrado_administrativo_arrastra_anotaciones():
    """Invariante 6. En `observaciones`, borrar una asignacion borra sus filas
    por ON DELETE CASCADE. Un registro permanente del alumno no puede depender
    de que nadie quite una materia del horario."""
    assert "CASCADE" not in sql_sin_comentarios().upper()


def test_la_tabla_admite_varias_anotaciones_por_alumno():
    """Es una bitacora. El UNIQUE de `observaciones` es justo lo que impide
    guardar mas de una anotacion y hace que cada guardado pise el anterior."""
    assert "UNIQUE" not in sql_sin_comentarios().upper()


def test_la_bitacora_no_depende_de_la_materia():
    """El observador pasa a ser por estudiante. El autor se identifica por
    profesor_id, no por la asignacion."""
    assert "asignacion" not in sql_sin_comentarios()


def test_las_columnas_de_identidad_no_admiten_nulos():
    """Una clave foranea no restringe NULL: en `observaciones` todas las
    columnas eran nulables y se podian colar filas sin estudiante."""
    sql = sql_sin_comentarios()
    for columna in ("estudiante_id", "profesor_id", "periodo", "positiva"):
        assert re.search(rf"{columna}\s+\w+(\(\d+\))?\s+NOT NULL", sql), columna


def test_el_periodo_solo_admite_del_1_al_4():
    """Hoy el esquema acepta periodo = 99. La tabla nueva no lo hereda."""
    assert "CHECK (periodo BETWEEN 1 AND 4)" in sql_sin_comentarios()


def test_la_migracion_no_toca_la_tabla_vieja():
    """`observaciones` se jubila, no se elimina: la pantalla vieja sigue
    funcionando mientras se construye la nueva, y se puede volver atras."""
    sql = sql_sin_comentarios().upper()
    assert "DROP" not in sql
    assert "ALTER TABLE OBSERVACIONES" not in sql


def test_el_indice_no_se_crea_en_la_migracion():
    """Va en apply_tenant_indexes.py, que antepone el nombre del schema.
    Crearlo tambien aqui dejaria dos indices identicos con nombres distintos en
    cada colegio, como ya ocurre en tenant_2005 con `asistencia`."""
    assert "CREATE INDEX" not in sql_sin_comentarios().upper()


def test_el_indice_de_la_bitacora_esta_en_el_script_de_indices():
    """El otro lado de la decision anterior: si no esta aqui, no existe en
    ningun colegio."""
    indices = {
        (tabla, nombre, tuple(columnas))
        for tabla, nombre, columnas in apply_tenant_indexes.INDEXES
    }

    assert (
        "observador_anotaciones",
        "idx_observador_anotaciones_estudiante",
        ("estudiante_id", "creada_en"),
    ) in indices


def test_la_anotacion_guarda_de_que_materia_era():
    """La pantalla muestra «Prof. Ana - Matematicas - 20/mar»: sin esto, la
    columna del medio no se puede escribir."""
    sql = sql_materia()
    assert "ALTER TABLE observador_anotaciones" in sql
    assert "ADD COLUMN IF NOT EXISTS materia character varying(100)" in sql


def test_la_materia_es_una_etiqueta_copiada_y_no_un_vinculo():
    """Una clave foranea a materias(id) reintroduciria el defecto que esta tabla
    vino a corregir: borrar la materia del horario se llevaria por delante el
    dato, o la fila entera."""
    sql = sql_materia().upper()
    assert "REFERENCES" not in sql
    assert "CASCADE" not in sql


def test_la_materia_no_deja_filas_a_medias():
    """NOT NULL con DEFAULT '': las anotaciones que ya existieran quedan con la
    materia vacia, no con un nulo que luego haya que comprobar en cada lectura."""
    sql = sql_materia()
    assert "NOT NULL DEFAULT ''" in sql


def test_la_segunda_migracion_no_reescribe_la_primera():
    """La primera ya esta aplicada en produccion. El runner bloquea un archivo
    cuyo checksum cambie, asi que un cambio posterior va SIEMPRE en un archivo
    nuevo."""
    assert "materia" not in sql_sin_comentarios()
