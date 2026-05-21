import pytest
from fastapi import HTTPException

from app.core import permissions


class FakeCursor:
    def __init__(self, result):
        self.result = result
        self.closed = False
        self.executed_query = None
        self.executed_params = None

    def execute(self, query, params):
        self.executed_query = query
        self.executed_params = params

    def fetchone(self):
        return self.result

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, result):
        self.cursor_instance = FakeCursor(result)
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def close(self):
        self.closed = True


def test_require_estudiante_access_allows_admin_without_db(monkeypatch):
    def fail_get_connection():
        raise AssertionError("Admin no debe consultar DB para este permiso")

    monkeypatch.setattr(permissions, "get_connection", fail_get_connection)

    permissions.require_estudiante_access(10, {"id": 1, "rol": "admin", "tenant": "tenant_demo"})


def test_require_estudiante_access_allows_owner_profesor(monkeypatch):
    connection = FakeConnection((1,))
    monkeypatch.setattr(permissions, "get_connection", lambda: connection)

    permissions.require_estudiante_access(10, {"id": 7, "rol": "profesor", "tenant": "tenant_demo"})

    assert connection.cursor_instance.executed_params == (10, 7)
    assert connection.cursor_instance.closed is True
    assert connection.closed is True


def test_require_estudiante_access_blocks_non_owner_profesor(monkeypatch):
    connection = FakeConnection(None)
    monkeypatch.setattr(permissions, "get_connection", lambda: connection)

    with pytest.raises(HTTPException) as exc:
        permissions.require_estudiante_access(10, {"id": 7, "rol": "profesor", "tenant": "tenant_demo"})

    assert exc.value.status_code == 403
    assert connection.cursor_instance.closed is True
    assert connection.closed is True


def test_require_estudiante_access_blocks_unknown_role(monkeypatch):
    def fail_get_connection():
        raise AssertionError("Rol no autorizado no debe consultar DB")

    monkeypatch.setattr(permissions, "get_connection", fail_get_connection)

    with pytest.raises(HTTPException) as exc:
        permissions.require_estudiante_access(10, {"id": 3, "rol": "acudiente", "tenant": "tenant_demo"})

    assert exc.value.status_code == 403


def test_require_profesor_scope_allows_admin_without_db(monkeypatch):
    def fail_get_connection():
        raise AssertionError("Este permiso no debe consultar DB")

    monkeypatch.setattr(permissions, "get_connection", fail_get_connection)

    permissions.require_profesor_scope(7, {"id": 1, "rol": "admin", "tenant": "tenant_demo"})


def test_require_profesor_scope_allows_same_profesor():
    permissions.require_profesor_scope(7, {"id": 7, "rol": "profesor", "tenant": "tenant_demo"})


def test_require_profesor_scope_blocks_other_profesor():
    with pytest.raises(HTTPException) as exc:
        permissions.require_profesor_scope(8, {"id": 7, "rol": "profesor", "tenant": "tenant_demo"})

    assert exc.value.status_code == 403


def test_require_asignacion_access_allows_admin_without_db(monkeypatch):
    def fail_get_connection():
        raise AssertionError("Admin no debe consultar DB para este permiso")

    monkeypatch.setattr(permissions, "get_connection", fail_get_connection)

    permissions.require_asignacion_access(11, {"id": 1, "rol": "admin", "tenant": "tenant_demo"})


def test_require_asignacion_access_allows_owner_profesor(monkeypatch):
    connection = FakeConnection((1,))
    monkeypatch.setattr(permissions, "get_connection", lambda: connection)

    permissions.require_asignacion_access(11, {"id": 7, "rol": "profesor", "tenant": "tenant_demo"})

    assert connection.cursor_instance.executed_params == (11, 7)
    assert connection.cursor_instance.closed is True
    assert connection.closed is True


def test_require_asignacion_access_blocks_non_owner_profesor(monkeypatch):
    connection = FakeConnection(None)
    monkeypatch.setattr(permissions, "get_connection", lambda: connection)

    with pytest.raises(HTTPException) as exc:
        permissions.require_asignacion_access(11, {"id": 7, "rol": "profesor", "tenant": "tenant_demo"})

    assert exc.value.status_code == 403


def test_require_estudiante_in_asignacion_allows_matching_student(monkeypatch):
    connection = FakeConnection((1,))
    monkeypatch.setattr(permissions, "get_connection", lambda: connection)

    permissions.require_estudiante_in_asignacion(10, 11)

    assert connection.cursor_instance.executed_params == (10, 11)


def test_require_estudiante_in_asignacion_blocks_mismatch(monkeypatch):
    connection = FakeConnection(None)
    monkeypatch.setattr(permissions, "get_connection", lambda: connection)

    with pytest.raises(HTTPException) as exc:
        permissions.require_estudiante_in_asignacion(10, 11)

    assert exc.value.status_code == 403


def test_require_plan_de_clases_access_allows_owner_profesor(monkeypatch):
    connection = FakeConnection((1,))
    monkeypatch.setattr(permissions, "get_connection", lambda: connection)

    permissions.require_plan_de_clases_access(15, {"id": 7, "rol": "profesor", "tenant": "tenant_demo"})

    assert connection.cursor_instance.executed_params == (15, 7)


def test_require_plan_de_clases_access_blocks_non_owner_profesor(monkeypatch):
    connection = FakeConnection(None)
    monkeypatch.setattr(permissions, "get_connection", lambda: connection)

    with pytest.raises(HTTPException) as exc:
        permissions.require_plan_de_clases_access(15, {"id": 7, "rol": "profesor", "tenant": "tenant_demo"})

    assert exc.value.status_code == 403
