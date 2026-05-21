from app.routes import ventas


def test_ventas_route_keeps_legacy_list_response(monkeypatch):
    monkeypatch.setattr(ventas, "obtener_ventas", lambda: [{"id": 1}])

    response = ventas.get_ventas(current_admin={"rol": "admin"})

    assert response == [{"id": 1}]


def test_ventas_route_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake_obtener_ventas_paginado(limit, offset, busqueda, estudiante_id, estado):
        calls.append({
            "limit": limit,
            "offset": offset,
            "busqueda": busqueda,
            "estudiante_id": estudiante_id,
            "estado": estado,
        })
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"id": 7}]}

    monkeypatch.setattr(ventas, "obtener_ventas_paginado", fake_obtener_ventas_paginado)

    response = ventas.get_ventas(
        limit=25,
        offset=50,
        busqueda="ana",
        estudiante_id=3,
        estado="Pendiente",
        current_admin={"rol": "admin"},
    )

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 7}]}
    assert calls == [{
        "limit": 25,
        "offset": 50,
        "busqueda": "ana",
        "estudiante_id": 3,
        "estado": "Pendiente",
    }]
