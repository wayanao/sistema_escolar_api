from pathlib import Path

import pytest
from fastapi import HTTPException

from app import main


class FakeCursor:
    def __init__(self, result):
        self.result = result
        self.closed = False
        self.executed_params = None

    def execute(self, query, params):
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


def crear_archivo_upload(tmp_path, relative_path):
    file_path = tmp_path / Path(relative_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(b"imagen")
    return file_path


def test_upload_branding_allows_same_tenant(tmp_path, monkeypatch):
    archivo = crear_archivo_upload(tmp_path, "branding/tenant_demo/logo.png")
    monkeypatch.setattr(main, "UPLOADS_ROOT", tmp_path.resolve())

    result = main._validar_acceso_archivo_upload(
        "branding/tenant_demo/logo.png",
        {"id": 1, "rol": "profesor", "tenant": "tenant_demo"},
    )

    assert result == archivo.resolve()


def test_upload_branding_blocks_other_tenant(tmp_path, monkeypatch):
    crear_archivo_upload(tmp_path, "branding/tenant_otro/logo.png")
    monkeypatch.setattr(main, "UPLOADS_ROOT", tmp_path.resolve())

    with pytest.raises(HTTPException) as exc:
        main._validar_acceso_archivo_upload(
            "branding/tenant_otro/logo.png",
            {"id": 1, "rol": "profesor", "tenant": "tenant_demo"},
        )

    assert exc.value.status_code == 403


def test_upload_blocks_path_traversal(tmp_path, monkeypatch):
    outside_file = tmp_path.parent / "fuera.png"
    outside_file.write_bytes(b"imagen")
    monkeypatch.setattr(main, "UPLOADS_ROOT", tmp_path.resolve())

    with pytest.raises(HTTPException) as exc:
        main._validar_acceso_archivo_upload("../fuera.png", {"id": 1, "rol": "admin", "tenant": "tenant_demo"})

    assert exc.value.status_code == 404


def test_upload_plan_de_clases_allows_admin_same_tenant(tmp_path, monkeypatch):
    archivo = crear_archivo_upload(tmp_path, "tenant_demo/plan_de_clases/plan.png")
    monkeypatch.setattr(main, "UPLOADS_ROOT", tmp_path.resolve())

    result = main._validar_acceso_archivo_upload(
        "tenant_demo/plan_de_clases/plan.png",
        {"id": 1, "rol": "admin", "tenant": "tenant_demo"},
    )

    assert result == archivo.resolve()


def test_upload_plan_de_clases_allows_owner_profesor(tmp_path, monkeypatch):
    archivo = crear_archivo_upload(tmp_path, "tenant_demo/plan_de_clases/plan.png")
    connection = FakeConnection((1,))

    monkeypatch.setattr(main, "UPLOADS_ROOT", tmp_path.resolve())
    monkeypatch.setattr("app.database.get_connection", lambda: connection)

    result = main._validar_acceso_archivo_upload(
        "tenant_demo/plan_de_clases/plan.png",
        {"id": 7, "rol": "profesor", "tenant": "tenant_demo"},
    )

    assert result == archivo.resolve()
    assert connection.cursor_instance.executed_params == (
        "uploads/tenant_demo/plan_de_clases/plan.png",
        "uploads/tenant_demo/plan_de_clases/plan.png",
        7,
    )
    assert connection.cursor_instance.closed is True
    assert connection.closed is True


def test_upload_plan_de_clases_blocks_non_owner_profesor(tmp_path, monkeypatch):
    crear_archivo_upload(tmp_path, "tenant_demo/plan_de_clases/plan.png")
    connection = FakeConnection(None)

    monkeypatch.setattr(main, "UPLOADS_ROOT", tmp_path.resolve())
    monkeypatch.setattr("app.database.get_connection", lambda: connection)

    with pytest.raises(HTTPException) as exc:
        main._validar_acceso_archivo_upload(
            "tenant_demo/plan_de_clases/plan.png",
            {"id": 7, "rol": "profesor", "tenant": "tenant_demo"},
        )

    assert exc.value.status_code == 403
    assert connection.cursor_instance.closed is True
    assert connection.closed is True
