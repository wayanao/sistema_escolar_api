import pytest
from datetime import date, datetime, timezone
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
    cursor = FakeCursor(
        rows=[
            (
                1,
                "Colegio Demo",
                "demo",
                "tenant_demo",
                "Activo",
                date(2026, 6, 1),
                date(2026, 7, 1),
                5,
            )
        ]
    )
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
            "estado_manual": "activo",
            "fecha_inicio": "2026-06-01",
            "fecha_proximo_pago": "2026-07-01",
            "dias_gracia": 5,
        }
    ]
    assert "FROM public.colegios" in cursor.calls[0][0]
    assert conn.closed is True


def test_crear_tenant_controller_creates_school_admin_and_subscription(monkeypatch):
    cursor = FakeCursor(rows=[(9, "Colegio Nuevo", "nuevo", "tenant_nuevo", "activo")])
    conn = FakeConnection(cursor)

    monkeypatch.setattr(super_admin_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(super_admin_controller, "get_password_hash", lambda password: f"hash:{password}")

    tenant = super_admin_controller.crear_tenant_controller(
        data={
            "nombre": "Colegio Nuevo",
            "codigo": "nuevo",
            "admin_nombre": "Admin Nuevo",
            "admin_email": "ADMIN@COLEGIO.COM",
            "admin_password": "Temporal123",
            "fecha_inicio": "2026-06-01",
            "fecha_proximo_pago": "2026-07-01",
            "dias_gracia": 5,
            "notas": "Plan mensual",
        },
        super_admin_id=7,
    )

    assert tenant == {
        "id": 9,
        "nombre": "Colegio Nuevo",
        "subdominio": "nuevo",
        "esquema_db": "tenant_nuevo",
        "estado": "activo",
        "estado_manual": "activo",
        "fecha_inicio": "2026-06-01",
        "fecha_proximo_pago": "2026-07-01",
        "dias_gracia": 5,
    }
    params = [call[1] for call in cursor.calls]
    assert ("Colegio Nuevo", "nuevo", "tenant_nuevo") in params
    assert ("Admin Nuevo", "admin@colegio.com", "hash:Temporal123") in params
    assert (9, date(2026, 6, 1), date(2026, 7, 1), 5, "Plan mensual") in params
    assert (9, "tenant_creado", "Colegio creado con admin inicial admin@colegio.com", 7) in params
    assert conn.committed is True


def test_crear_tenant_controller_rejects_invalid_code():
    with pytest.raises(HTTPException) as exc:
        super_admin_controller.crear_tenant_controller(
            {
                "nombre": "Colegio Nuevo",
                "codigo": "Nuevo!",
                "admin_nombre": "Admin Nuevo",
                "admin_email": "admin@colegio.com",
                "admin_password": "Temporal123",
                "fecha_inicio": "2026-06-01",
                "fecha_proximo_pago": "2026-07-01",
                "dias_gracia": 5,
            }
        )

    assert exc.value.status_code == 422


def test_crear_tenant_controller_rejects_payment_before_start():
    with pytest.raises(HTTPException) as exc:
        super_admin_controller.crear_tenant_controller(
            {
                "nombre": "Colegio Nuevo",
                "codigo": "nuevo",
                "admin_nombre": "Admin Nuevo",
                "admin_email": "admin@colegio.com",
                "admin_password": "Temporal123",
                "fecha_inicio": "2026-07-01",
                "fecha_proximo_pago": "2026-06-01",
                "dias_gracia": 5,
            }
        )

    assert exc.value.status_code == 422


def test_actualizar_estado_tenant_controller_validates_status(monkeypatch):
    cursor = FakeCursor(
        rows=[
            (1, "Colegio Demo", "demo", "tenant_demo", "activo", date(2026, 6, 1), date(2026, 7, 1), 5),
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
    assert tenant["estado_manual"] == "en_mora"
    assert cursor.calls[1][1] == ("en_mora", 1)
    assert cursor.calls[2][1] == (1, "activo", "en_mora", "Pago vencido", 7)
    assert conn.committed is True


def test_actualizar_estado_tenant_controller_same_status_does_not_audit(monkeypatch):
    cursor = FakeCursor(rows=[(1, "Colegio Demo", "demo", "tenant_demo", "activo", date(2026, 6, 1), date(2026, 7, 1), 5)])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(super_admin_controller, "get_connection", lambda: conn)

    tenant = super_admin_controller.actualizar_estado_tenant_controller(
        1,
        "activo",
        super_admin_id=7,
        motivo="Sin cambio",
    )

    assert tenant["estado"] == "activo"
    assert tenant["estado_manual"] == "activo"
    assert len(cursor.calls) == 1
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
    assert "tenant_estado_auditoria" in cursor.calls[0][0]


def test_actualizar_estado_tenant_controller_rejects_unknown_status():
    with pytest.raises(HTTPException) as exc:
        super_admin_controller.actualizar_estado_tenant_controller(1, "demo", super_admin_id=7)

    assert exc.value.status_code == 422


def test_crear_tenant_controller_rejects_weak_initial_password():
    with pytest.raises(HTTPException) as exc:
        super_admin_controller.crear_tenant_controller(
            {
                "nombre": "Colegio Nuevo",
                "codigo": "nuevo",
                "admin_nombre": "Admin Nuevo",
                "admin_email": "admin@colegio.com",
                "admin_password": "secret",
                "fecha_inicio": "2026-06-01",
                "fecha_proximo_pago": "2026-07-01",
                "dias_gracia": 5,
            }
        )

    assert exc.value.status_code == 422
