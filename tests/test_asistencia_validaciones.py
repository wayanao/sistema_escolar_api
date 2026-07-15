from datetime import date

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.controllers import asistencia_controller
from app.routes import asistencia
from app.schemas.asistencia import AsistenciaCreate


def crear_registro(estudiante_id=1, asignacion_id=10, fecha=date(2026, 7, 15), periodo=2, estado="presente"):
    return AsistenciaCreate(
        estudiante_id=estudiante_id,
        asignacion_id=asignacion_id,
        fecha=fecha,
        periodo=periodo,
        estado=estado,
    )


def test_schema_asistencia_rechaza_estado_desconocido():
    with pytest.raises(ValidationError):
        crear_registro(estado="excusa")


def test_guardar_asistencia_rechaza_lote_vacio():
    with pytest.raises(HTTPException) as exc:
        asistencia.guardar_asistencia([], current_user={"id": 3, "rol": "profesor"})

    assert exc.value.status_code == 422
    assert "al menos un estudiante" in exc.value.detail


def test_guardar_asistencia_rechaza_contextos_mezclados():
    data = [
        crear_registro(estudiante_id=1),
        crear_registro(estudiante_id=2, asignacion_id=11),
    ]

    with pytest.raises(HTTPException) as exc:
        asistencia.guardar_asistencia(data, current_user={"id": 3, "rol": "profesor"})

    assert exc.value.status_code == 422
    assert "misma asignación" in exc.value.detail


def test_guardar_asistencia_rechaza_estudiantes_duplicados():
    data = [crear_registro(estudiante_id=1), crear_registro(estudiante_id=1, estado="ausente")]

    with pytest.raises(HTTPException) as exc:
        asistencia.guardar_asistencia(data, current_user={"id": 3, "rol": "profesor"})

    assert exc.value.status_code == 422
    assert "duplicados" in exc.value.detail


def test_guardar_asistencia_valida_permisos_y_envia_lote(monkeypatch):
    asignaciones_validadas = []
    estudiantes_validados = []
    data = [crear_registro(estudiante_id=1), crear_registro(estudiante_id=2, estado="ausente")]

    monkeypatch.setattr(
        asistencia,
        "require_asignacion_access",
        lambda asignacion_id, current_user: asignaciones_validadas.append((asignacion_id, current_user["id"])),
    )
    monkeypatch.setattr(
        asistencia,
        "require_estudiante_in_asignacion",
        lambda estudiante_id, asignacion_id: estudiantes_validados.append((estudiante_id, asignacion_id)),
    )
    monkeypatch.setattr(
        asistencia,
        "guardar_asistencia_controller",
        lambda lote: {"mensaje": f"{len(lote)} registros"},
    )

    response = asistencia.guardar_asistencia(data, current_user={"id": 3, "rol": "profesor"})

    assert response == {"mensaje": "2 registros"}
    assert asignaciones_validadas == [(10, 3), (10, 3)]
    assert estudiantes_validados == [(1, 10), (2, 10)]


class FakeCursor:
    def __init__(self, fallar_insert=False):
        self.calls = []
        self.fallar_insert = fallar_insert
        self.closed = False

    def execute(self, query, params=None):
        self.calls.append((query, params))
        if self.fallar_insert and "INSERT INTO asistencia" in query:
            raise RuntimeError("insert fallido")

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


def test_controller_actualiza_solo_estudiantes_enviados(monkeypatch):
    cursor = FakeCursor()
    conn = FakeConnection(cursor)
    data = [crear_registro(estudiante_id=1), crear_registro(estudiante_id=2, estado="ausente")]

    monkeypatch.setattr(asistencia_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        asistencia_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, _asignacion_id: 77,
    )

    response = asistencia_controller.guardar_asistencia_controller(data)

    delete_query, delete_params = cursor.calls[0]
    assert response == {"mensaje": "Asistencia guardada"}
    assert "estudiante_id = ANY" in delete_query
    assert delete_params == (77, date(2026, 7, 15), 2, [1, 2])
    assert conn.committed is True
    assert conn.rolled_back is False
    assert cursor.closed is True
    assert conn.closed is True


def test_controller_hace_rollback_si_falla_actualizacion(monkeypatch):
    cursor = FakeCursor(fallar_insert=True)
    conn = FakeConnection(cursor)

    monkeypatch.setattr(asistencia_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        asistencia_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, _asignacion_id: 77,
    )

    with pytest.raises(RuntimeError, match="insert fallido"):
        asistencia_controller.guardar_asistencia_controller([crear_registro()])

    assert conn.committed is False
    assert conn.rolled_back is True
    assert cursor.closed is True
    assert conn.closed is True
