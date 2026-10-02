import pytest
from fastapi import HTTPException

from app.controllers import boletin_controller
from app.routes import boletines


class FakeCursor:
    def __init__(self, estudiante, filas):
        self.estudiante = estudiante
        self.filas = filas
        self.calls = []
        self.closed = False

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.estudiante

    def fetchall(self):
        return self.filas

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.closed = False

    def cursor(self, **_kwargs):
        return self.cursor_obj

    def close(self):
        self.closed = True


def test_reporte_parcial_usa_planilla_vigente_y_conserva_descripciones(monkeypatch):
    cursor = FakeCursor(
        {
            "estudiante_nombre": "Sara",
            "estudiante_apellido": "López",
            "curso_nombre": "Quinto",
        },
        [
            {
                "asignacion_id": 44,
                "materia_id": 12,
                "materia": "Historia",
                "profesor_nombre": "Ana",
                "profesor_apellido": "Ruiz",
                "orden_boletin": 1,
                "nota_detalle_id": 101,
                "descripcion": "Evaluación oral",
                "nota": 4.0,
                "tipo_evaluacion": "numerica",
                "valoracion": None,
            },
            {
                "asignacion_id": 44,
                "materia_id": 12,
                "materia": "Historia",
                "profesor_nombre": "Ana",
                "profesor_apellido": "Ruiz",
                "orden_boletin": 1,
                "nota_detalle_id": 102,
                "descripcion": "Trabajo final",
                "nota": 5.0,
                "tipo_evaluacion": "numerica",
                "valoracion": None,
            },
            {
                "asignacion_id": 45,
                "materia_id": 13,
                "materia": "Convivencia",
                "profesor_nombre": "Luis",
                "profesor_apellido": "Paz",
                "orden_boletin": 2,
                "nota_detalle_id": 103,
                "descripcion": "Trabajo colaborativo",
                "nota": None,
                "tipo_evaluacion": "desarrollo",
                "valoracion": "Logrado",
            },
        ],
    )
    conn = FakeConnection(cursor)
    monkeypatch.setattr(boletin_controller, "get_connection", lambda: conn)

    resultado = boletin_controller.obtener_reporte_parcial_admin_controller(8, 2)

    assert resultado["periodo"] == 2
    assert resultado["materias"][0]["definitiva"] == 4.5
    assert resultado["materias"][0]["detalles"] == [
        {
            "descripcion": "Evaluación oral",
            "nota": 4.0,
            "periodo": 2,
            "tipo_evaluacion": "numerica",
            "valoracion": None,
        },
        {
            "descripcion": "Trabajo final",
            "nota": 5.0,
            "periodo": 2,
            "tipo_evaluacion": "numerica",
            "valoracion": None,
        },
    ]
    assert resultado["materias"][1]["definitiva"] is None
    assert resultado["materias"][1]["detalles"][0]["valoracion"] == "Logrado"
    assert "notas_detalle" in cursor.calls[1][0]
    assert "boletin_cabecera" not in cursor.calls[1][0]
    assert cursor.closed is True
    assert conn.closed is True


def test_ruta_reporte_parcial_conserva_guard_admin_y_respuesta(monkeypatch):
    esperado = {"estudiante_id": 8, "periodo": 2, "materias": []}
    monkeypatch.setattr(
        boletines,
        "obtener_reporte_parcial_admin_controller",
        # Año lectivo, fase 3 (paso 3.5a): sin año, None.
        lambda estudiante_id, periodo, anio_lectivo_id=None: esperado,
    )

    assert boletines.generar_reporte_parcial_admin(8, 2, {"rol": "admin"}) == esperado


def test_ruta_reporte_parcial_responde_404_si_no_existe_estudiante(monkeypatch):
    monkeypatch.setattr(
        boletines,
        "obtener_reporte_parcial_admin_controller",
        lambda estudiante_id, periodo, anio_lectivo_id=None: None,
    )

    with pytest.raises(HTTPException) as exc:
        boletines.generar_reporte_parcial_admin(999, 1, {"rol": "admin"})

    assert exc.value.status_code == 404
