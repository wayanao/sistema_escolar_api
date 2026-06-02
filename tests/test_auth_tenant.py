import pytest
from fastapi import HTTPException

from app import dependencies
from app.controllers import auth_controller
from app.core import tenant_status
from app.globals import tenant_schema_var
from app.security import create_access_token


class FakeRequest:
    def __init__(self, cookies=None):
        self.cookies = cookies or {}


class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        if not self.rows:
            return None
        return self.rows.pop(0)

    def close(self):
        pass


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


@pytest.mark.anyio
async def test_get_current_user_rejects_missing_token():
    with pytest.raises(HTTPException) as exc:
        await dependencies.get_current_user(FakeRequest(), token=None)

    assert exc.value.status_code == 401


@pytest.mark.anyio
async def test_get_current_user_rejects_invalid_token():
    with pytest.raises(HTTPException) as exc:
        await dependencies.get_current_user(FakeRequest(), token="token-invalido")

    assert exc.value.status_code == 401


@pytest.mark.anyio
async def test_get_current_user_rejects_public_tenant():
    token = create_access_token({"sub": "1", "rol": "admin", "tenant": "public"})

    with pytest.raises(HTTPException) as exc:
        await dependencies.get_current_user(FakeRequest(), token=token)

    assert exc.value.status_code == 401


@pytest.mark.anyio
async def test_get_current_user_sets_tenant_and_revalidates_user(monkeypatch):
    calls = []

    def fake_validar_usuario_en_bd(user_id, rol):
        calls.append((user_id, rol, tenant_schema_var.get()))

    monkeypatch.setattr(dependencies, "_validar_usuario_en_bd", fake_validar_usuario_en_bd)
    monkeypatch.setattr(dependencies, "ensure_tenant_allowed_for_app", lambda tenant: {"estado": "activo"})

    token = create_access_token({"sub": "9", "rol": "profesor", "tenant": "tenant_demo"})
    user = await dependencies.get_current_user(FakeRequest(), token=token)

    assert user == {"id": 9, "rol": "profesor", "tenant": "tenant_demo"}
    assert calls == [(9, "profesor", "tenant_demo")]


@pytest.mark.anyio
async def test_get_current_user_rejects_user_removed_or_role_changed(monkeypatch):
    def fake_validar_usuario_en_bd(user_id, rol):
        raise ValueError("Usuario no valido")

    monkeypatch.setattr(dependencies, "_validar_usuario_en_bd", fake_validar_usuario_en_bd)
    monkeypatch.setattr(dependencies, "ensure_tenant_allowed_for_app", lambda tenant: {"estado": "activo"})

    token = create_access_token({"sub": "9", "rol": "profesor", "tenant": "tenant_demo"})

    with pytest.raises(HTTPException) as exc:
        await dependencies.get_current_user(FakeRequest(), token=token)

    assert exc.value.status_code == 401


@pytest.mark.anyio
async def test_get_current_user_rejects_suspended_tenant(monkeypatch):
    def fake_tenant_status(tenant):
        raise HTTPException(status_code=403, detail="Tenant no autorizado")

    def fail_validar_usuario_en_bd(user_id, rol):
        raise AssertionError("No debe validar usuario si el tenant esta suspendido")

    monkeypatch.setattr(dependencies, "ensure_tenant_allowed_for_app", fake_tenant_status)
    monkeypatch.setattr(dependencies, "_validar_usuario_en_bd", fail_validar_usuario_en_bd)

    token = create_access_token({"sub": "9", "rol": "profesor", "tenant": "tenant_demo"})

    with pytest.raises(HTTPException) as exc:
        await dependencies.get_current_user(FakeRequest(), token=token)

    assert exc.value.status_code == 403


def test_tenant_status_normalizes_allowed_states():
    assert tenant_status.normalize_tenant_status("Activo") == "activo"
    assert tenant_status.normalize_tenant_status(" en_mora ") == "en_mora"
    assert tenant_status.normalize_tenant_status("suspendido") == "suspendido"
    assert tenant_status.normalize_tenant_status("cancelado") == "cancelado"


def test_tenant_status_unknown_state_is_suspended():
    assert tenant_status.normalize_tenant_status("demo") == "suspendido"
    assert tenant_status.normalize_tenant_status(None) == "suspendido"
    assert tenant_status.normalize_tenant_status("") == "suspendido"


def test_tenant_status_calculates_subscription_grace_period():
    today = tenant_status.date.fromisoformat("2026-06-10")

    assert tenant_status.calculate_effective_tenant_status("activo", "2026-06-10", 5, today) == "activo"
    assert tenant_status.calculate_effective_tenant_status("activo", "2026-06-09", 5, today) == "en_mora"
    assert tenant_status.calculate_effective_tenant_status("activo", "2026-06-01", 5, today) == "suspendido"
    assert tenant_status.calculate_effective_tenant_status("cancelado", "2026-06-01", 5, today) == "cancelado"


def test_tenant_login_allows_active_and_past_due_only():
    assert tenant_status.is_tenant_allowed_for_login("activo") is True
    assert tenant_status.is_tenant_allowed_for_login("en_mora") is True
    assert tenant_status.is_tenant_allowed_for_login("suspendido") is False
    assert tenant_status.is_tenant_allowed_for_login("cancelado") is False


def test_tenant_login_block_message_is_specific():
    assert "suspendido" in tenant_status.get_tenant_login_block_message("suspendido")
    assert "cancelado" in tenant_status.get_tenant_login_block_message("cancelado")


def test_login_controller_raises_specific_block_for_suspended_tenant(monkeypatch):
    monkeypatch.setattr(
        auth_controller,
        "get_tenant_by_code",
        lambda codigo: {"estado": "suspendido", "esquema_db": "tenant_demo"},
    )

    with pytest.raises(tenant_status.TenantLoginBlocked) as exc:
        auth_controller.login_controller("admin@test.com", "secret", "demo")

    assert exc.value.estado == "suspendido"
    assert "suspendido" in exc.value.message


def test_tenant_status_response_for_past_due():
    response = tenant_status.build_tenant_status_response({"estado": "en_mora"})

    assert response["estado"] == "en_mora"
    assert response["mostrar_aviso"] is True
    assert "mora" in response["mensaje"]


def test_cambiar_password_actual_controller_updates_password_and_flag(monkeypatch):
    cursor = FakeCursor(rows=[("Temporal123",)])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(auth_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(auth_controller, "get_password_hash", lambda password: f"hash:{password}")

    response = auth_controller.cambiar_password_actual_controller(
        {"id": 5, "rol": "admin", "tenant": "tenant_demo"},
        "Temporal123",
        "NuevaClave123",
    )

    assert response == {"mensaje": "Password actualizada", "debe_cambiar_password": False}
    assert cursor.calls[1][1] == ("hash:NuevaClave123", 5)
    assert conn.committed is True


def test_cambiar_password_actual_controller_rejects_weak_password():
    with pytest.raises(HTTPException) as exc:
        auth_controller.cambiar_password_actual_controller(
            {"id": 5, "rol": "admin", "tenant": "tenant_demo"},
            "Temporal123",
            "nueva",
        )

    assert exc.value.status_code == 422
