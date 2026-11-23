"""Cambiar una nota de la planilla no la mueve (2026-11-23).

Antes, guardar una nota la borraba y la volvia a insertar: recibia un `id`
nuevo y pasaba al final. Boletin final ordena las tarjetas por `nd.id` y
empareja los textos guardados por posicion, asi que los textos se corrian una
tarjeta (asi paso en Jardin A, periodo 4). Ahora la nota que existe se cambia
en su lugar (`planilla_service.guardar_celda`).

Las sentencias de `planilla_repository` se ejecutan de verdad sobre SQLite en
memoria (no hay PostgreSQL en CI); del SQL solo se cambia `%s` por `?`. El
recalculo en lote de subnotas usa `UNNEST`, que SQLite no tiene: ese lo cubre
`test_subnotas_planilla.py`.
"""

import sqlite3

import pytest

from app.services.planilla_service import guardar_celda


class CursorSqlite:
    def __init__(self, conexion):
        self._cursor = conexion.cursor()

    def execute(self, sql, params=None):
        self._cursor.execute(sql.replace("%s", "?"), tuple(params or ()))

    def fetchone(self):
        return self._cursor.fetchone()


@pytest.fixture
def base():
    conexion = sqlite3.connect(":memory:")
    conexion.execute("""
        CREATE TABLE notas_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT, estudiante_id INTEGER, asignacion_id INTEGER,
            descripcion TEXT, nota REAL, fecha TEXT, periodo INTEGER DEFAULT 1,
            tipo_evaluacion TEXT DEFAULT 'numerica', valoracion TEXT
        )
    """)
    # Pre-matematica de un estudiante de preescolar, en el orden en que se
    # crearon las columnas.
    for descripcion, valoracion in (
        ("Del 1al9", "destacado"),
        ("Fam 10", "logrado"),
        ("Conteo verbal", "destacado"),
        ("Numero cantidad", "destacado"),
        ("Sumas", "destacado"),
    ):
        conexion.execute(
            "INSERT INTO notas_detalle (estudiante_id, asignacion_id, periodo, descripcion,"
            " tipo_evaluacion, valoracion) VALUES (608, 147, 4, ?, 'desarrollo', ?)",
            (descripcion, valoracion),
        )
    yield conexion
    conexion.close()


def _tarjetas(conexion):
    """Como las ordena Boletin final: por `id`."""
    return conexion.execute(
        "SELECT id, descripcion, valoracion FROM notas_detalle"
        " WHERE estudiante_id = 608 AND asignacion_id = 147 AND periodo = 4 ORDER BY id"
    ).fetchall()


def test_cambiar_una_carita_no_mueve_la_tarjeta(base):
    antes = _tarjetas(base)

    nota_id = guardar_celda(CursorSqlite(base), 608, 147, 4, None, "Fam 10", "desarrollo", "destacado")

    despues = _tarjetas(base)
    assert nota_id == antes[1][0]
    # Mismo id y mismo lugar (2a tarjeta); solo cambia la carita.
    assert [(i, d) for i, d, _ in despues] == [(i, d) for i, d, _ in antes]
    assert despues[1] == (antes[1][0], "Fam 10", "destacado")


def test_la_descripcion_se_reconoce_sin_mayusculas_ni_espacios(base):
    """La misma clave de siempre: `LOWER(TRIM(...))`. Queda escrita como llega,
    recortada, igual que al insertar."""
    antes = _tarjetas(base)

    guardar_celda(CursorSqlite(base), 608, 147, 4, None, "  fam 10 ", "desarrollo", "proceso")

    despues = _tarjetas(base)
    assert len(despues) == 5
    assert despues[1] == (antes[1][0], "fam 10", "proceso")


def test_una_nota_nueva_se_inserta_al_final(base):
    nota_id = guardar_celda(CursorSqlite(base), 608, 147, 4, None, "Figuras", "desarrollo", "logrado")

    despues = _tarjetas(base)
    assert len(despues) == 6
    assert despues[-1] == (nota_id, "Figuras", "logrado")


def test_las_repetidas_se_quitan_y_queda_la_mas_antigua(base):
    """Antes el borrado previo dejaba una sola; ahora tambien, pero la que
    queda es la original, con su lugar."""
    base.execute(
        "INSERT INTO notas_detalle (estudiante_id, asignacion_id, periodo, descripcion,"
        " tipo_evaluacion, valoracion) VALUES (608, 147, 4, 'Fam 10', 'desarrollo', 'apoyo')"
    )
    original = _tarjetas(base)[1][0]

    nota_id = guardar_celda(CursorSqlite(base), 608, 147, 4, None, "Fam 10", "desarrollo", "destacado")

    despues = _tarjetas(base)
    assert nota_id == original
    assert [d for _, d, _ in despues] == ["Del 1al9", "Fam 10", "Conteo verbal", "Numero cantidad", "Sumas"]
    assert despues[1] == (original, "Fam 10", "destacado")


def test_no_toca_otro_periodo_ni_otro_estudiante(base):
    base.execute(
        "INSERT INTO notas_detalle (estudiante_id, asignacion_id, periodo, descripcion,"
        " tipo_evaluacion, valoracion) VALUES (608, 147, 3, 'Fam 10', 'desarrollo', 'apoyo')"
    )
    base.execute(
        "INSERT INTO notas_detalle (estudiante_id, asignacion_id, periodo, descripcion,"
        " tipo_evaluacion, valoracion) VALUES (560, 147, 4, 'Fam 10', 'desarrollo', 'apoyo')"
    )

    guardar_celda(CursorSqlite(base), 608, 147, 4, None, "Fam 10", "desarrollo", "destacado")

    otras = base.execute(
        "SELECT estudiante_id, periodo, valoracion FROM notas_detalle"
        " WHERE descripcion = 'Fam 10' AND NOT (estudiante_id = 608 AND periodo = 4)"
        " ORDER BY estudiante_id"
    ).fetchall()
    assert otras == [(560, 4, "apoyo"), (608, 3, "apoyo")]
