from app.routes import estudiantes


def test_estudiantes_route_keeps_legacy_list_response(monkeypatch):
    calls = []

    def fake_listado(estado="activo"):
        calls.append(estado)
        return [{"id": 1}]

    monkeypatch.setattr(estudiantes, "obtener_estudiantes_controller", fake_listado)

    result = estudiantes.obtener_estudiantes()

    assert calls == ["activo"]
    assert result == [{"id": 1}]


def test_estudiantes_route_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake_paginado(limit, offset, busqueda, estado):
        calls.append((limit, offset, busqueda, estado))
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"id": 1}]}

    monkeypatch.setattr(estudiantes, "obtener_estudiantes_paginado_controller", fake_paginado)

    result = estudiantes.obtener_estudiantes(limit=25, offset=50, busqueda="ana", estado="retirado")

    assert calls == [(25, 50, "ana", "retirado")]
    assert result == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 1}]}


def test_estudiantes_route_rejects_invalid_estado_filter():
    try:
        estudiantes.obtener_estudiantes(estado="borrado")
    except Exception as exc:
        assert exc.status_code == 422
    else:
        raise AssertionError("Expected invalid estado filter to be rejected")


def test_actualizar_estado_estudiante_route_returns_controller_result(monkeypatch):
    calls = []

    def fake_update(estudiante_id, estado):
        calls.append((estudiante_id, estado))
        return {"id": estudiante_id, "estado": estado}

    monkeypatch.setattr(estudiantes, "actualizar_estado_estudiante_controller", fake_update)

    result = estudiantes.actualizar_estado_estudiante(
        7,
        estudiantes.EstudianteEstadoUpdate(estado="egresado"),
    )

    assert calls == [(7, "egresado")]
    assert result == {"id": 7, "estado": "egresado"}
