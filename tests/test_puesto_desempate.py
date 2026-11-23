"""El puesto del curso no se repite (2026-11-23, pedido del usuario).

En preescolar las caritas valen 5, 4, 3 o 2 y muchos estudiantes empataban en
el promedio, asi que `RANK()` les daba el mismo puesto. Ahora el orden es:

1. mayor promedio de las definitivas guardadas del periodo;
2. menos inasistencias del periodo;
3. apellido y nombre, como las listas.

Las dos consultas que calculan el puesto -el boletin del admin
(`boletin_repository.leer_puesto_en_el_curso`) y "Mi curso" del director
(`director_grupo_repository.leer_estudiantes_con_puesto`)- se ejecutan aqui de
verdad, sobre SQLite en memoria: no hay PostgreSQL en CI. Del SQL solo se
cambia `%s` por `?` e `ILIKE` por `LIKE` (en SQLite ya ignora mayusculas en
ASCII). Los datos usan nombres sin tildes para que el orden alfabetico no
dependa de la intercalacion.
"""

import sqlite3

import pytest

from app.repositories import boletin_repository
from app.repositories import director_grupo_repository


ESQUEMA = """
CREATE TABLE anios_lectivos (id INTEGER PRIMARY KEY, estado TEXT);
CREATE TABLE cursos (id INTEGER PRIMARY KEY, anio_lectivo_id INTEGER);
CREATE TABLE asignaciones (id INTEGER PRIMARY KEY, curso_id INTEGER);
CREATE TABLE estudiantes (
    id INTEGER PRIMARY KEY, nombre TEXT, apellido TEXT, curso_id INTEGER, estado TEXT
);
CREATE TABLE matriculas (estudiante_id INTEGER, anio_lectivo_id INTEGER, curso_id INTEGER);
CREATE TABLE boletin_cabecera (
    estudiante_id INTEGER, asignacion_id INTEGER, periodo INTEGER, definitiva REAL
);
CREATE TABLE asistencia (
    estudiante_id INTEGER, asignacion_id INTEGER, periodo INTEGER, estado TEXT
);
"""

# Año 1 cerrado (curso 3, clase 300); año 2 activo (curso 10, clases 100 y 101).
ANIOS = [(1, "cerrado"), (2, "activo")]
CURSOS = [(3, 1), (10, 2)]
ASIGNACIONES = [(300, 3), (100, 10), (101, 10)]

# Jardin A del año activo, periodo 1.
ESTUDIANTES = [
    (1, "Ana", "Zea", 10, "activo"),
    (2, "Luis", "Alba", 10, "activo"),
    (3, "Eva", "Mora", 10, "activo"),
    (4, "Leo", "Pinto", 10, "activo"),
    (5, "Sol", "Rey", 10, "activo"),  # sin nada guardado
]
DEFINITIVAS = [
    # Ana, Luis y Eva: todo "Logrado" (4) -> empatan en 4.0.
    (1, 100, 1, 4.0), (1, 101, 1, 4.0),
    (2, 100, 1, 4.0), (2, 101, 1, 4.0),
    (3, 100, 1, 4.0), (3, 101, 1, 4.0),
    # Leo: todo "Destacado" -> 5.0; sus faltas no lo bajan del primer puesto.
    (4, 100, 1, 5.0), (4, 101, 1, 5.0),
    # Otro periodo: no cuenta.
    (2, 100, 2, 5.0),
]
ASISTENCIA = [
    # Luis: 2 faltas en el periodo 1 (una sin clase, que en el año activo cuenta).
    (2, 100, 1, "ausente"), (2, None, 1, "Ausente"), (2, 101, 1, "presente"),
    # Ana: sus faltas son del periodo 2; en el periodo 1 tiene 0.
    (1, 100, 2, "ausente"), (1, 101, 2, "ausente"),
    # Eva: una falta del periodo 1, pero de una clase del año cerrado; no cuenta.
    (3, 300, 1, "ausente"),
    # Un periodo vacio es el 1.
    (4, 100, None, "ausente"), (4, 101, 1, "ausente"), (4, 100, 1, "ausente"),
]


class CursorSqlite:
    """Cursor de diccionarios, como `RealDictCursor`, sobre SQLite."""

    def __init__(self, conexion):
        self._cursor = conexion.cursor()

    def execute(self, sql, params=None):
        sql = sql.replace("%s", "?").replace("ILIKE", "LIKE")
        self._cursor.execute(sql, tuple(params or ()))

    def _fila(self, fila):
        return None if fila is None else dict(fila)

    def fetchone(self):
        return self._fila(self._cursor.fetchone())

    def fetchall(self):
        return [dict(fila) for fila in self._cursor.fetchall()]


@pytest.fixture
def base():
    conexion = sqlite3.connect(":memory:")
    conexion.row_factory = sqlite3.Row
    conexion.executescript(ESQUEMA)
    conexion.executemany("INSERT INTO anios_lectivos VALUES (?, ?)", ANIOS)
    conexion.executemany("INSERT INTO cursos VALUES (?, ?)", CURSOS)
    conexion.executemany("INSERT INTO asignaciones VALUES (?, ?)", ASIGNACIONES)
    conexion.executemany("INSERT INTO estudiantes VALUES (?, ?, ?, ?, ?)", ESTUDIANTES)
    conexion.executemany("INSERT INTO boletin_cabecera VALUES (?, ?, ?, ?)", DEFINITIVAS)
    conexion.executemany("INSERT INTO asistencia VALUES (?, ?, ?, ?)", ASISTENCIA)
    yield conexion
    conexion.close()


# Leo (5.0) primero. Empatados en 4.0: Eva y Ana sin faltas -> Mora antes que
# Zea; Luis, con 2 faltas, de ultimo.
PUESTOS_ESPERADOS = {4: 1, 3: 2, 1: 3, 2: 4}


@pytest.mark.parametrize("estudiante_id, puesto", sorted(PUESTOS_ESPERADOS.items()))
def test_el_boletin_no_repite_puestos_y_desempata_por_faltas_y_apellido(
    base, estudiante_id, puesto
):
    fila = boletin_repository.leer_puesto_en_el_curso(CursorSqlite(base), estudiante_id, 1)

    assert fila == {"puesto": puesto, "total": 4}


def test_el_boletin_deja_sin_puesto_a_quien_no_tiene_nada_guardado(base):
    fila = boletin_repository.leer_puesto_en_el_curso(CursorSqlite(base), 5, 1)

    assert fila == {"puesto": None, "total": 4}


def test_mi_curso_da_los_mismos_puestos_que_el_boletin(base):
    filas = director_grupo_repository.leer_estudiantes_con_puesto(CursorSqlite(base), 10, 1)

    assert [(f["estudiante_id"], f["puesto"]) for f in filas] == [
        (4, 1), (3, 2), (1, 3), (2, 4), (5, None),
    ]
    assert {f["total_rankeados"] for f in filas} == {4}


def test_en_un_anio_cerrado_desempata_con_las_faltas_de_ese_anio(base):
    """Con `anio_lectivo_id`: los compañeros son los de la matricula de ese
    año, y solo cuentan las faltas de sus clases (las filas sin clase no, porque
    no se sabe de que año son)."""
    base.executemany("INSERT INTO matriculas VALUES (?, ?, ?)", [(1, 1, 3), (2, 1, 3)])
    base.executemany("INSERT INTO boletin_cabecera VALUES (?, ?, ?, ?)", [
        (1, 300, 1, 3.0), (2, 300, 1, 3.0),
    ])
    base.executemany("INSERT INTO asistencia VALUES (?, ?, ?, ?)", [
        (1, 300, 1, "ausente"),  # Ana (Zea): 1 falta del año 1
        (2, None, 1, "ausente"), (2, None, 1, "ausente"),  # Luis: sin clase, no cuentan
    ])
    cursor = CursorSqlite(base)

    luis = boletin_repository.leer_puesto_en_el_curso(cursor, 2, 1, anio_lectivo_id=1)
    ana = boletin_repository.leer_puesto_en_el_curso(cursor, 1, 1, anio_lectivo_id=1)

    assert (luis, ana) == ({"puesto": 1, "total": 2}, {"puesto": 2, "total": 2})
