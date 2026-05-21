from app.routes import estudiantes


def test_estudiantes_route_keeps_legacy_list_response(monkeypatch):
    monkeypatch.setattr(estudiantes, "obtener_estudiantes_controller", lambda: [{"id": 1}])

    result = estudiantes.obtener_estudiantes()

    assert result == [{"id": 1}]


def test_estudiantes_route_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake_paginado(limit, offset, busqueda):
        calls.append((limit, offset, busqueda))
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"id": 1}]}

    monkeypatch.setattr(estudiantes, "obtener_estudiantes_paginado_controller", fake_paginado)

    result = estudiantes.obtener_estudiantes(limit=25, offset=50, busqueda="ana")

    assert calls == [(25, 50, "ana")]
    assert result == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 1}]}
