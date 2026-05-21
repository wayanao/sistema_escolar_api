import pytest
from fastapi import HTTPException

from app import dependencies
from app.globals import tenant_schema_var
from app.security import create_access_token


class FakeRequest:
    def __init__(self, cookies=None):
        self.cookies = cookies or {}


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

    token = create_access_token({"sub": "9", "rol": "profesor", "tenant": "tenant_demo"})
    user = await dependencies.get_current_user(FakeRequest(), token=token)

    assert user == {"id": 9, "rol": "profesor", "tenant": "tenant_demo"}
    assert calls == [(9, "profesor", "tenant_demo")]


@pytest.mark.anyio
async def test_get_current_user_rejects_user_removed_or_role_changed(monkeypatch):
    def fake_validar_usuario_en_bd(user_id, rol):
        raise ValueError("Usuario no valido")

    monkeypatch.setattr(dependencies, "_validar_usuario_en_bd", fake_validar_usuario_en_bd)

    token = create_access_token({"sub": "9", "rol": "profesor", "tenant": "tenant_demo"})

    with pytest.raises(HTTPException) as exc:
        await dependencies.get_current_user(FakeRequest(), token=token)

    assert exc.value.status_code == 401
