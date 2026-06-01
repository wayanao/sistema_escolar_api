import pytest
from datetime import datetime, timezone
from fastapi import HTTPException

from app.controllers import auth_controller, super_admin_controller
from app.core import super_admin
from app.security import create_access_token


class FakeRequest:
    def __init__(self, cookies=None):
        self.cookies = cookies or {}


class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.calls = []
        self.closed = False

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        if not self.rows:
            return None
        return self.rows.pop(0)

    def fetchall(self):
        return self.rows

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_login_controller_uses_super_admin_flow(monkeypatch):
    def fake_authenticate(email, password, verify_password):
        assert email == "owner@app.com"
        assert password == "secret"
        return {"id": 1, "nombre": "Owner", "rol": "super_admin", "tenant": "public"}

    monkeypatch.setattr(auth_controller, "authenticate_super_admin", fake_authenticate)

    user = auth_controller.login_controller("owner@app.com", "secret", "super_admin")

    assert user["rol"] == "super_admin"
    assert user["tenant"] == "public"


@pytest.mark.anyio
async def test_get_current_super_admin_accepts_public_platform_token(monkeypatch):
    calls = []

    def fake_validate(user_id):
        calls.append(user_id)

    monkeypatch.setattr(super_admin, "validate_super_admin", fake_validate)

    token = create_access_token({"sub": "7", "rol": "super_admin", "tenant": "public"})
    user = await super_admin.get_current_super_admin(FakeRequest(), token=token)

    assert user == {"id": 7, "rol": "super_admin", "tenant": "public"}
    assert calls == [7]


@pytest.mark.anyio
async def test_get_current_super_admin_rejects_tenant_admin_token(monkeypatch):
    monkeypatch.setattr(super_admin, "validate_super_admin", lambda user_id: None)

    token = create_access_token({"sub": "7", "rol": "admin", "tenant": "tenant_demo"})

    with pytest.raises(HTTPException) as exc:
        await super_admin.get_current_super_admin(FakeRequest(), token=token)

    assert exc.value.status_code == 401


def test_listar_tenants_controller_reads_public_colegios(monkeypatch):
    cursor = FakeCursor(rows=[(1, "Colegio Demo", "demo", "tenant_demo", "Activo")])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(super_admin_controller, "get_connection", lambda: conn)

    tenants = super_admin_controller.listar_tenants_controller()

    assert tenants == [
        {
            "id": 1,
            "nombre": "Colegio Demo",
            "subdominio": "demo",
            "esquema_db": "tenant_demo",
            "estado": "activo",
        }
    ]
    assert "FROM public.colegios" in cursor.calls[0][0]
    assert conn.closed is True


def test_actualizar_estado_tenant_controller_validates_status(monkeypatch):
    cursor = FakeCursor(
        rows=[
            (1, "Colegio Demo", "demo", "tenant_demo", "activo"),
            (1, "Colegio Demo", "demo", "tenant_demo", "en_mora"),
        ]
    )
    conn = FakeConnection(cursor)
    monkeypatch.setattr(super_admin_controller, "get_connection", lambda: conn)

    tenant = super_admin_controller.actualizar_estado_tenant_controller(
        1,
        "en_mora",
        super_admin_id=7,
        motivo="Pago vencido",
    )

    assert tenant["estado"] == "en_mora"
    assert cursor.calls[2][1] == ("en_mora", 1)
    assert cursor.calls[3][1] == (1, "activo", "en_mora", "Pago vencido", 7)
    assert conn.committed is True


def test_actualizar_estado_tenant_controller_same_status_does_not_audit(monkeypatch):
    cursor = FakeCursor(rows=[(1, "Colegio Demo", "demo", "tenant_demo", "activo")])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(super_admin_controller, "get_connection", lambda: conn)

    tenant = super_admin_controller.actualizar_estado_tenant_controller(
        1,
        "activo",
        super_admin_id=7,
        motivo="Sin cambio",
    )

    assert tenant["estado"] == "activo"
    assert len(cursor.calls) == 2
    assert conn.rolled_back is True


def test_listar_auditoria_tenant_controller_returns_history(monkeypatch):
    created_at = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    cursor = FakeCursor(
        rows=[
            (10, "activo", "en_mora", "Pago vencido", created_at, "David", "owner@app.com"),
        ]
    )
    conn = FakeConnection(cursor)
    monkeypatch.setattr(super_admin_controller, "get_connection", lambda: conn)

    history = super_admin_controller.listar_auditoria_tenant_controller(1)

    assert history == [
        {
            "id": 10,
            "estado_anterior": "activo",
            "estado_nuevo": "en_mora",
            "motivo": "Pago vencido",
            "creado_en": "2026-06-01T12:00:00+00:00",
            "super_admin_nombre": "David",
            "super_admin_email": "owner@app.com",
        }
    ]
    assert "tenant_estado_auditoria" in cursor.calls[1][0]


def test_actualizar_estado_tenant_controller_rejects_unknown_status():
    with pytest.raises(HTTPException) as exc:
        super_admin_controller.actualizar_estado_tenant_controller(1, "demo", super_admin_id=7)

    assert exc.value.status_code == 422
