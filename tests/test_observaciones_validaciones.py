import pytest
from pydantic import ValidationError

from app.controllers import observacion_controller
from app.routes import observaciones
from app.schemas.observacion import ObservacionCreate


def test_observacion_permite_una_sola_dimension():
    observacion = ObservacionCreate(
        estudiante_id=1,
        asignacion_id=10,
        periodo=2,
        cognitivo="  Avanza en lectura.  ",
    )

    assert observacion.conductual == ""
    assert observacion.cognitivo == "Avanza en lectura."
    assert observacion.lenguaje == ""


def test_observacion_rechaza_todas_las_dimensiones_vacias():
    with pytest.raises(ValidationError, match="al menos una observación"):
        ObservacionCreate(
            estudiante_id=1,
            asignacion_id=10,
            periodo=2,
            conductual="  ",
        )


def test_ruta_observacion_valida_permisos_y_envia_campos_vacios(monkeypatch):
    asignaciones = []
    estudiantes = []
    payloads = []
    data = ObservacionCreate(
        estudiante_id=1,
        asignacion_id=10,
        periodo=2,
        lenguaje="Se comunica con claridad.",
    )

    monkeypatch.setattr(
        observaciones,
        "require_asignacion_access",
        lambda asignacion_id, current_user: asignaciones.append((asignacion_id, current_user["id"])),
    )
    monkeypatch.setattr(
        observaciones,
        "require_estudiante_in_asignacion",
        lambda estudiante_id, asignacion_id: estudiantes.append((estudiante_id, asignacion_id)),
    )
    monkeypatch.setattr(
        observaciones,
        "guardar_observacion_controller",
        lambda payload: payloads.append(payload) or {"mensaje": "ok"},
    )

    response = observaciones.guardar_observacion(data, current_user={"id": 3, "rol": "profesor"})

    assert response == {"mensaje": "ok"}
    assert asignaciones == [(10, 3)]
    assert estudiantes == [(1, 10)]
    assert payloads[0]["conductual"] == ""
    assert payloads[0]["cognitivo"] == ""
    assert payloads[0]["lenguaje"] == "Se comunica con claridad."


class FakeCursor:
    def __init__(self):
        self.calls = []
        self.closed = False

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_controller_guarda_dimensiones_no_diligenciadas_como_vacias(monkeypatch):
    cursor = FakeCursor()
    conn = FakeConnection(cursor)
    monkeypatch.setattr(observacion_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        observacion_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, _asignacion_id: 77,
    )

    response = observacion_controller.guardar_observacion_controller({
        "estudiante_id": 1,
        "asignacion_id": 10,
        "periodo": 2,
        "cognitivo": "Avanza en lectura.",
    })

    assert response == {"mensaje": "Observación guardada/actualizada"}
    assert cursor.calls[0][1] == (1, 77, 2, "", "Avanza en lectura.", "")
    assert conn.committed is True
    assert conn.rolled_back is False
    assert cursor.closed is True
    assert conn.closed is True
