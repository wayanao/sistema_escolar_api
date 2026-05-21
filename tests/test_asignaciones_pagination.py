from app.routes import asignaciones


def test_asignaciones_lista_keeps_legacy_list_response(monkeypatch):
    monkeypatch.setattr(
        asignaciones,
        "obtener_todas_asignaciones_controller",
        lambda: [{"id": 1}],
    )

    response = asignaciones.obtener_todas_asignaciones(_admin={"rol": "admin"})

    assert response == [{"id": 1}]


def test_asignaciones_lista_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake_obtener_todas_asignaciones_paginado_controller(
        limit,
        offset,
        profesor_id,
        curso_id,
        materia_id,
        busqueda,
    ):
        calls.append({
            "limit": limit,
            "offset": offset,
            "profesor_id": profesor_id,
            "curso_id": curso_id,
            "materia_id": materia_id,
            "busqueda": busqueda,
        })
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"id": 9}]}

    monkeypatch.setattr(
        asignaciones,
        "obtener_todas_asignaciones_paginado_controller",
        fake_obtener_todas_asignaciones_paginado_controller,
    )

    response = asignaciones.obtener_todas_asignaciones(
        limit=25,
        offset=50,
        profesor_id=3,
        curso_id=4,
        materia_id=5,
        busqueda="matematicas",
        _admin={"rol": "admin"},
    )

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 9}]}
    assert calls == [{
        "limit": 25,
        "offset": 50,
        "profesor_id": 3,
        "curso_id": 4,
        "materia_id": 5,
        "busqueda": "matematicas",
    }]
