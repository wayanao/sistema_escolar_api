"""Paso 2 de "Listas de Seguimiento por Curso": el repositorio.

Ver `docs/funcionalidades/LISTAS_SEGUIMIENTO.md`. Fija lo que puede romperse
sin que nadie lo note, no el texto exacto de cada consulta:

- que el modulo **no es dueno de la conexion**: recibe el cursor y no abre,
  cierra ni confirma nada;
- que la comprobacion de nombre duplicado usa **la misma expresion** que el
  indice unico de la migracion, que es lo unico que hace coincidir el 409 con
  lo que la base acepta de verdad;
- que guardar un lote cuesta **una sola** ida y vuelta, cueste lo que cueste el
  lote, y que una lista vacia no gasta ninguna;
- que borrar una columna acota por curso **en la misma sentencia**, sin ventana
  entre comprobar y escribir.

No hay base de datos aqui: el cursor es falso y lo que se mira es que SQL
recibe y con que parametros, igual que en `test_observador_mis_estudiantes.py`.
"""
import inspect
import re
from pathlib import Path

import pytest

from app.repositories import listas_seguimiento_repository as repo


MIGRACION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "20260921_listas_seguimiento.sql"
)

# La normalizacion de nombre, tal cual. Si alguien la cambia en un sitio y no en
# el otro, `test_el_duplicado_usa_la_misma_expresion_que_el_indice` lo caza.
NORMALIZACION = "UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g'))"


class CursorFalso:
    """Anota cada `execute` y devuelve lo que el test le haya puesto."""

    def __init__(self, fila=None, filas=(), rowcount=0):
        self.fila = fila
        self.filas = list(filas)
        self.rowcount = rowcount
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.fila

    def fetchall(self):
        return self.filas


def sql_de(cursor, indice=0):
    """El SQL de la llamada, con los espacios colapsados para poder buscar."""
    return re.sub(r"\s+", " ", cursor.calls[indice][0]).strip()


def params_de(cursor, indice=0):
    return cursor.calls[indice][1]


# ---------------------------------------------------------------------------
# La capa: quien manda en la conexion.
# ---------------------------------------------------------------------------


def test_no_es_dueno_de_la_conexion():
    """No importa nada de `app.db`: el cursor se lo dan hecho.

    Si alguien importa `get_cursor` aqui, el repositorio empieza a abrir
    conexiones por su cuenta y el `commit` deja de estar en un solo sitio.
    """
    prohibidos = {"get_cursor", "get_connection", "get_pool", "settings"}
    assert not (prohibidos & set(dir(repo)))


@pytest.mark.parametrize(
    "nombre",
    [
        "existe_curso",
        "leer_columnas_del_curso",
        "leer_estudiantes_del_curso",
        "leer_marcas_de_columnas",
        "existe_columna_con_ese_nombre",
        "crear_columna",
        "eliminar_columna",
        "guardar_marcas",
    ],
)
def test_toda_funcion_recibe_el_cursor_como_primer_argumento(nombre):
    parametros = list(inspect.signature(getattr(repo, nombre)).parameters)
    assert parametros[0] == "cursor"


# ---------------------------------------------------------------------------
# Lecturas.
# ---------------------------------------------------------------------------


def test_existe_curso_distingue_el_que_esta_del_que_no():
    presente = CursorFalso(fila=(1,))
    ausente = CursorFalso(fila=None)

    assert repo.existe_curso(presente, 12) is True
    assert repo.existe_curso(ausente, 999) is False
    assert params_de(presente) == (12,)


def test_las_columnas_salen_en_orden_de_creacion():
    """Por `id`, no por `created_at`: dos columnas creadas en la misma
    transaccion comparten el timestamp al milisegundo."""
    cursor = CursorFalso(filas=[(5, "Asistio a la cumbre"), (6, "Compro el libro")])

    assert repo.leer_columnas_del_curso(cursor, 12) == [
        (5, "Asistio a la cumbre"),
        (6, "Compro el libro"),
    ]
    sql = sql_de(cursor)
    assert "FROM listas_seguimiento_columnas" in sql
    assert "ORDER BY id" in sql
    assert "created_at" not in sql
    assert params_de(cursor) == (12,)


def test_el_roster_va_por_apellido_y_nombre():
    cursor = CursorFalso(filas=[(101, "Juan", "Perez")])

    assert repo.leer_estudiantes_del_curso(cursor, 12) == [(101, "Juan", "Perez")]
    sql = sql_de(cursor)
    assert "FROM estudiantes" in sql
    assert "WHERE curso_id = %s" in sql
    assert "ORDER BY apellido, nombre" in sql
    assert params_de(cursor) == (12,)


def test_el_roster_no_filtra_por_estado():
    """La lista de seguimiento muestra el curso completo, como el estado de
    cuenta por curso del que esta copiada. Filtrar seria una decision de
    producto que el documento no toma."""
    cursor = CursorFalso()

    repo.leer_estudiantes_del_curso(cursor, 12)

    assert "estado" not in sql_de(cursor)


def test_sin_columnas_no_se_pregunta_por_las_marcas():
    """Un curso sin columnas no tiene marcas posibles: la ida y vuelta no
    cambiaria la respuesta, y cada una cuesta ~180 ms contra Neon."""
    cursor = CursorFalso()

    assert repo.leer_marcas_de_columnas(cursor, []) == []
    assert cursor.calls == []


def test_las_marcas_de_varias_columnas_salen_en_una_sola_consulta():
    cursor = CursorFalso(filas=[(5, 101, True, "Llego tarde")])

    assert repo.leer_marcas_de_columnas(cursor, [5, 6]) == [(5, 101, True, "Llego tarde")]
    assert len(cursor.calls) == 1
    assert "WHERE columna_id = ANY(%s)" in sql_de(cursor)
    assert params_de(cursor) == ([5, 6],)


# ---------------------------------------------------------------------------
# Nombre duplicado: el 409 y el indice tienen que decir lo mismo.
# ---------------------------------------------------------------------------


def test_el_duplicado_usa_la_misma_expresion_que_el_indice():
    """La consulta del 409 y el indice unico normalizan **igual**.

    Si se separan, la pantalla aceptaria un nombre que la base despues rechaza
    -o al reves-, y el fallo solo aparece con un nombre escrito con otras
    mayusculas o con espacios de sobra.
    """
    cursor = CursorFalso(fila=None)

    repo.existe_columna_con_ese_nombre(cursor, 12, "Asistio a la cumbre")

    assert NORMALIZACION in sql_de(cursor)
    assert NORMALIZACION in MIGRACION.read_text(encoding="utf-8")


def test_el_duplicado_normaliza_tambien_el_nombre_que_llega():
    """Los dos lados de la comparacion, no solo el guardado."""
    cursor = CursorFalso(fila=None)

    repo.existe_columna_con_ese_nombre(cursor, 12, "  asistio  a la CUMBRE ")

    sql = sql_de(cursor)
    assert "UPPER(REGEXP_REPLACE(TRIM(%s), '[[:space:]]+', ' ', 'g'))" in sql
    # El nombre viaja sin tocar: quien normaliza es PostgreSQL, no Python.
    assert params_de(cursor) == (12, "  asistio  a la CUMBRE ")


def test_el_duplicado_responde_si_o_no():
    ocupado = CursorFalso(fila=(1,))
    libre = CursorFalso(fila=None)

    assert repo.existe_columna_con_ese_nombre(ocupado, 12, "Ya existe") is True
    assert repo.existe_columna_con_ese_nombre(libre, 12, "Nueva") is False


# ---------------------------------------------------------------------------
# Escrituras.
# ---------------------------------------------------------------------------


def test_crear_columna_devuelve_el_id_nuevo():
    cursor = CursorFalso(fila=(7,))

    assert repo.crear_columna(cursor, 12, "Compro el libro") == 7
    assert "INSERT INTO listas_seguimiento_columnas" in sql_de(cursor)
    assert "RETURNING id" in sql_de(cursor)
    assert params_de(cursor) == (12, "Compro el libro")


def test_crear_columna_guarda_el_nombre_tal_como_llega():
    """Recortar es cosa del controlador. Si el repositorio recortara tambien,
    habria dos sitios decidiendo que es un nombre valido."""
    cursor = CursorFalso(fila=(7,))

    repo.crear_columna(cursor, 12, "  Con espacios  ")

    assert params_de(cursor) == (12, "  Con espacios  ")
    assert "TRIM" not in sql_de(cursor)


def test_borrar_acota_por_curso_en_la_misma_sentencia():
    """Sin un `if` previo: comprobar y borrar son una sola sentencia, asi que
    no hay ventana en la que la columna cambie de curso entre las dos."""
    cursor = CursorFalso(fila=(5,))

    assert repo.eliminar_columna(cursor, 12, 5) is True
    sql = sql_de(cursor)
    assert "DELETE FROM listas_seguimiento_columnas" in sql
    assert "WHERE id = %s AND curso_id = %s" in sql
    assert params_de(cursor) == (5, 12)
    assert len(cursor.calls) == 1


def test_borrar_una_columna_de_otro_curso_no_borra_nada():
    cursor = CursorFalso(fila=None)

    assert repo.eliminar_columna(cursor, 12, 5) is False


def test_un_lote_vacio_no_gasta_una_consulta():
    cursor = CursorFalso()

    assert repo.guardar_marcas(cursor, []) == 0
    assert cursor.calls == []


def test_el_lote_entero_va_en_una_sola_sentencia():
    """Es el motivo de que este modulo use UNNEST.

    Con una sentencia por celda, marcar una columna de 30 alumnos serian 30
    idas y vueltas: ~5,4 s contra Neon. Aqui es una, sea el lote de 3 o de 300.
    """
    cursor = CursorFalso(rowcount=3)
    marcas = [
        (5, 101, True, "Llego tarde"),
        (5, 102, False, None),
        (6, 101, True, ""),
    ]

    assert repo.guardar_marcas(cursor, marcas) == 3
    assert len(cursor.calls) == 1


def test_el_lote_viaja_como_cuatro_arrays_en_paralelo():
    cursor = CursorFalso(rowcount=3)
    marcas = [
        (5, 101, True, "Llego tarde"),
        (5, 102, False, None),
        (6, 101, True, ""),
    ]

    repo.guardar_marcas(cursor, marcas)

    assert params_de(cursor) == (
        [5, 5, 6],
        [101, 102, 101],
        [True, False, True],
        ["Llego tarde", None, ""],
    )


def test_el_lote_se_guarda_con_upsert_sobre_la_celda():
    """`ON CONFLICT (columna_id, estudiante_id)` se apoya en el UNIQUE de la
    migracion: una celda nueva se inserta y una que ya existia se pisa."""
    cursor = CursorFalso(rowcount=1)

    repo.guardar_marcas(cursor, [(5, 101, True, "x")])

    sql = sql_de(cursor)
    assert "INSERT INTO listas_seguimiento_marcas" in sql
    assert "UNNEST(%s::int[], %s::int[], %s::boolean[], %s::text[])" in sql
    assert "ON CONFLICT (columna_id, estudiante_id) DO UPDATE" in sql
    assert "updated_at = CURRENT_TIMESTAMP" in sql


def test_la_nota_se_guarda_tal_cual_sin_convertir_vacio_en_nulo():
    """Ni recorta ni convierte: si la nota vacia debe ser NULL, lo decide el
    controlador. Dos capas normalizando lo mismo es como se separan."""
    cursor = CursorFalso(rowcount=2)

    repo.guardar_marcas(cursor, [(5, 101, False, ""), (5, 102, False, None)])

    assert params_de(cursor)[3] == ["", None]
