"""Subnotas de la planilla, paso A1: lo que no debe cambiar sin subnotas.

Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`. Se escribio y se corrio
**antes** de tocar el codigo, contra la planilla de siempre, y paso. Despues
del cambio tiene que seguir pasando igual:

- la planilla sin `?con_subnotas=true` devuelve exactamente el mismo JSON, con
  las mismas dos consultas y sin mirar las tablas nuevas (Asistencia usa esta
  misma ruta);
- guardar una nota a mano y borrar un tipo escriben en `notas_detalle` lo
  mismo que hoy, con la misma respuesta.

Lo unico que el paso A1 agrega a esas dos escrituras es una consulta cada una
(la comprobacion del `409` y el borrado de las subnotas del tipo). Esas se
prueban en `test_subnotas_planilla.py`, no aqui.
"""

from contextlib import contextmanager
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.controllers import planilla_controller, planilla_excel_controller
from app.services import planilla_service


ADMIN = {"id": 1, "rol": "admin"}


class CursorGuionado:
    """Responde segun un fragmento del SQL y guarda todo lo que se ejecuta."""

    def __init__(self, guion):
        self.guion = guion
        self.consultas = []
        self._uno = None
        self._todos = []

    def execute(self, sql, params=None):
        texto = " ".join(str(sql).split())
        self.consultas.append((texto, params))
        self._uno, self._todos = None, []
        for fragmento, uno, todos in self.guion:
            if fragmento in texto:
                self._uno, self._todos = uno, list(todos)
                break

    def fetchone(self):
        return self._uno

    def fetchall(self):
        return list(self._todos)


GUARDIA = ("SELECT al.anio, al.estado", (2026, "activo"), [])
RESUELVE = ("AS asignacion_academica_id", (77,), [])
NIVEL = ("SELECT c.nivel", (None,), [])
ESTUDIANTE = ("SELECT e.id FROM estudiantes e", (11,), [])
INSERTA = ("INSERT INTO notas_detalle", (901,), [])

# (estudiante, nombre, apellido, materia, descripcion, nota, tipo, valoracion, id)
FILAS = [
    (1, "Ana", "Gómez", "Matemáticas", "Cognitivo", Decimal("4.50"), "numerica", None, 10),
    (1, "Ana", "Gómez", "Matemáticas", "Procedimental", Decimal("3.00"), "numerica", None, 11),
    (2, "Luis", "Pérez", "Matemáticas", "Cognitivo", None, "numerica", None, 12),
    (2, "Luis", "Pérez", "Matemáticas", "Desde React", Decimal("5.00"), "numerica", None, 9),
    (3, "Eva", "Ríos", "Matemáticas", "Cognitivo", None, "desarrollo", "logrado", 13),
    (4, "Leo", "Soto", "Matemáticas", None, None, "numerica", None, None),
]

PLANILLA_DE_HOY = {
    "columnas": ["Cognitivo", "Procedimental"],
    "data": [
        {
            "estudiante_id": 1, "nombre": "Ana", "apellido": "Gómez",
            "materia": "Matemáticas",
            "notas": {"Cognitivo": 4.5, "Procedimental": 3.0},
            "tipos_evaluacion": {"Cognitivo": "numerica", "Procedimental": "numerica"},
            "valoraciones": {"Cognitivo": None, "Procedimental": None},
            "promedio": 3.75,
        },
        {
            "estudiante_id": 2, "nombre": "Luis", "apellido": "Pérez",
            "materia": "Matemáticas",
            "notas": {"Cognitivo": None},
            "tipos_evaluacion": {"Cognitivo": "numerica"},
            "valoraciones": {"Cognitivo": None},
            "promedio": "",
        },
        {
            "estudiante_id": 3, "nombre": "Eva", "apellido": "Ríos",
            "materia": "Matemáticas",
            "notas": {"Cognitivo": None},
            "tipos_evaluacion": {"Cognitivo": "desarrollo"},
            "valoraciones": {"Cognitivo": "logrado"},
            "promedio": "",
        },
        {
            "estudiante_id": 4, "nombre": "Leo", "apellido": "Soto",
            "materia": "Matemáticas",
            "notas": {}, "tipos_evaluacion": {}, "valoraciones": {},
            "promedio": "",
        },
    ],
}


@pytest.fixture
def base(monkeypatch):
    def instalar(guion):
        cursor = CursorGuionado(guion)
        commits = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        for modulo in (planilla_controller, planilla_excel_controller, planilla_service):
            monkeypatch.setattr(modulo, "get_cursor", fake_get_cursor)
        return SimpleNamespace(cursor=cursor, commits=commits)

    return instalar


def _escrituras_de_notas(cursor):
    return [
        (texto, params)
        for texto, params in cursor.consultas
        if "notas_detalle" in texto and texto.split()[0] in ("DELETE", "INSERT")
    ]


def test_la_planilla_sin_parametro_devuelve_el_json_de_hoy(base):
    db = base([RESUELVE, ("FROM asignaciones a JOIN cursos c", None, FILAS)])

    respuesta = planilla_excel_controller.planilla_excel_controller(12, 2)

    assert respuesta == PLANILLA_DE_HOY
    assert len(db.cursor.consultas) == 2
    assert not any("planilla_subnotas" in texto for texto, _ in db.cursor.consultas)
    assert db.commits == [False]


def test_guardar_una_nota_a_mano_escribe_lo_mismo_de_hoy(base):
    db = base([GUARDIA, ESTUDIANTE, RESUELVE, NIVEL, INSERTA])
    datos = SimpleNamespace(
        estudiante_id=11, asignacion_id=12, periodo=2, nota=4.5,
        descripcion="Cognitivo", tipo_evaluacion="numerica", valoracion=None,
    )

    respuesta = planilla_controller.registrar_nota_planilla_controller(datos, usuario=ADMIN)

    assert respuesta == {"mensaje": "Nota registrada correctamente", "nota_id": 901}
    borrado, insercion = _escrituras_de_notas(db.cursor)
    assert borrado[0].startswith("DELETE FROM notas_detalle WHERE estudiante_id = %s")
    assert borrado[1] == (11, 77, 2, "Cognitivo")
    assert insercion[0].startswith("INSERT INTO notas_detalle")
    assert insercion[1] == (11, 77, 2, 4.5, "Cognitivo", "numerica", None)
    assert db.commits == [True]


def test_borrar_un_tipo_escribe_lo_mismo_de_hoy(base):
    db = base([GUARDIA, RESUELVE])

    respuesta = planilla_controller.eliminar_tipo_controller(12, "Cognitivo", 2, usuario=ADMIN)

    assert respuesta == {"mensaje": "Tipo eliminado correctamente"}
    (borrado,) = _escrituras_de_notas(db.cursor)
    assert borrado[0].startswith("DELETE FROM notas_detalle WHERE asignacion_id = %s")
    assert borrado[1] == (77, 2, "Cognitivo")
    assert db.commits == [True]
