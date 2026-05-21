import pytest
from fastapi import HTTPException

from app.routes import notas


def test_notas_estudiante_requires_estudiante_access(monkeypatch):
    calls = []

    def fake_require_estudiante_access(estudiante_id, current_user):
        calls.append((estudiante_id, current_user))

    monkeypatch.setattr(notas, "require_estudiante_access", fake_require_estudiante_access)
    monkeypatch.setattr(notas, "notas_estudiante_controller", lambda estudiante_id: {"id": estudiante_id})

    current_user = {"id": 7, "rol": "profesor", "tenant": "tenant_demo"}
    result = notas.notas_estudiante(3, current_user)

    assert calls == [(3, current_user)]
    assert result == {"id": 3}


def test_boletin_requires_estudiante_access(monkeypatch):
    calls = []

    def fake_require_estudiante_access(estudiante_id, current_user):
        calls.append((estudiante_id, current_user))

    monkeypatch.setattr(notas, "require_estudiante_access", fake_require_estudiante_access)
    monkeypatch.setattr(notas, "boletin_estudiante_controller", lambda estudiante_id: {"id": estudiante_id})

    current_user = {"id": 7, "rol": "profesor", "tenant": "tenant_demo"}
    result = notas.boletin(3, current_user)

    assert calls == [(3, current_user)]
    assert result == {"id": 3}


def test_boletin_detallado_requires_estudiante_access(monkeypatch):
    calls = []

    def fake_require_estudiante_access(estudiante_id, current_user):
        calls.append((estudiante_id, current_user))

    monkeypatch.setattr(notas, "require_estudiante_access", fake_require_estudiante_access)
    monkeypatch.setattr(
        notas,
        "boletin_detallado_controller",
        lambda estudiante_id, periodo: {"id": estudiante_id, "periodo": periodo},
    )

    current_user = {"id": 7, "rol": "profesor", "tenant": "tenant_demo"}
    result = notas.boletin_detallado(3, 2, current_user)

    assert calls == [(3, current_user)]
    assert result == {"id": 3, "periodo": 2}


def test_notas_estudiante_stops_when_permission_fails(monkeypatch):
    def fake_require_estudiante_access(estudiante_id, current_user):
        raise HTTPException(status_code=403, detail="No autorizado")

    def fail_controller(estudiante_id):
        raise AssertionError("No debe consultar datos si el permiso falla")

    monkeypatch.setattr(notas, "require_estudiante_access", fake_require_estudiante_access)
    monkeypatch.setattr(notas, "notas_estudiante_controller", fail_controller)

    with pytest.raises(HTTPException) as exc:
        notas.notas_estudiante(3, {"id": 7, "rol": "profesor", "tenant": "tenant_demo"})

    assert exc.value.status_code == 403
