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
MIGRACION_HISTORICAS = RAIZ / "migrations" / "20260908_observador_anotaciones_historicas.sql"
COPIA = RAIZ / "scripts" / "copiar_observaciones_al_observador.py"


def sin_comentarios(texto):
    return re.sub(r"--.*$", "", texto, flags=re.MULTILINE)


def sql_materia():
    return sin_comentarios(MIGRACION_MATERIA.read_text(encoding="utf-8"))


def sql_historicas():
    return sin_comentarios(MIGRACION_HISTORICAS.read_text(encoding="utf-8"))


def fuente_de_la_copia():
    return COPIA.read_text(encoding="utf-8")


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
    columnas eran nulables y se podian colar filas sin estudiante.

    `positiva` **ya no esta en esta lista**: nacio NOT NULL y dejo de serlo el
    2026-09-08, cuando se decidio copiar las anotaciones viejas sin inventarles
    una marca. Ver `test_las_heredadas_pueden_ir_sin_marca`. Las de identidad
    de verdad siguen intactas.
    """
    sql = sql_sin_comentarios()
    for columna in ("estudiante_id", "profesor_id", "periodo"):
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


# ---------------------------------------------------------------------------
# Fase 4: las anotaciones heredadas de la tabla vieja
# ---------------------------------------------------------------------------


def test_las_heredadas_pueden_ir_sin_marca():
    """El modelo viejo no distinguia positivo de negativo. Decidido con el
    usuario: no se les inventa una. Solo las nuevas la llevan, y ahi la exige
    el esquema de la API."""
    assert "ALTER COLUMN positiva DROP NOT NULL" in sql_historicas()


def test_las_heredadas_pueden_ir_sin_fecha():
    """`observaciones` nunca guardo cuando se escribio cada una. Poner la fecha
    de la copia las haria parecer escritas hoy y las mezclaria con las nuevas;
    NULL significa «no se sabe» y la lectura las manda al final."""
    assert "ALTER COLUMN creada_en DROP NOT NULL" in sql_historicas()


def test_la_copia_no_se_puede_duplicar():
    """El riesgo que el documento tenia anotado: ejecutar la copia dos veces
    duplicaria el historial de un alumno."""
    sql = sql_historicas()
    assert "observacion_origen_id" in sql
    assert "UNIQUE (observacion_origen_id)" in sql


def test_ninguna_migracion_del_observador_toca_la_tabla_vieja():
    """`observaciones` se jubila, no se elimina. Se conserva intacta como unica
    copia de ese historial."""
    for sql in (sql_sin_comentarios(), sql_materia(), sql_historicas()):
        mayus = sql.upper()
        assert "DROP TABLE" not in mayus
        assert "ALTER TABLE OBSERVACIONES" not in mayus
        assert "DELETE FROM" not in mayus


def test_el_script_de_copia_solo_lee_la_tabla_vieja():
    """Copiar no puede convertirse en mover. Si esto falla, alguien esta a un
    paso de borrar las unicas 68 filas de ese historial."""
    fuente = fuente_de_la_copia().upper()
    assert "DELETE FROM OBSERVACIONES" not in fuente
    assert "UPDATE OBSERVACIONES" not in fuente
    assert "DROP TABLE" not in fuente
    assert "TRUNCATE" not in fuente


def test_el_script_de_copia_es_repetible():
    assert "ON CONFLICT (observacion_origen_id) DO NOTHING" in fuente_de_la_copia()


def test_las_copiadas_van_sin_marca_y_sin_fecha():
    """Los dos NULL del INSERT no son un descuido: son las dos cosas que el
    modelo viejo no guardaba."""
    fuente = fuente_de_la_copia()
    assert "estudiante_id, profesor_id, periodo, positiva," in fuente
    assert "materia, creada_en, observacion_origen_id" in fuente


def test_la_copia_recupera_el_profesor_y_la_materia():
    """Lo unico que si se puede rescatar de la fila vieja, a traves de su
    asignacion. Sin esto las heredadas quedarian anonimas."""
    fuente = fuente_de_la_copia()
    assert "JOIN asignaciones a ON a.id = o.asignacion_id" in fuente
    assert "LEFT JOIN materias m ON m.id = a.materia_id" in fuente


def test_la_copia_descarta_lo_que_la_tabla_nueva_no_admite():
    """Y lo cuenta: 68 no pueden convertirse en 60 en silencio."""
    fuente = fuente_de_la_copia()
    assert "o.estudiante_id IS NOT NULL" in fuente
    assert "a.profesor_id IS NOT NULL" in fuente
    assert "o.periodo BETWEEN 1 AND 4" in fuente
    # El recuento informa de cada motivo por separado.
    for motivo in ("sin_estudiante", "sin_profesor", "periodo_invalido", "sin_texto"):
        assert motivo in fuente
