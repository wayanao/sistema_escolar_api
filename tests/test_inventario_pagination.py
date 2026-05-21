from app.routes import inventario


def test_inventario_route_keeps_legacy_list_response(monkeypatch):
    monkeypatch.setattr(inventario, "obtener_inventario_controller", lambda: [{"id": 1}])

    response = inventario.obtener_inventario()

    assert response == [{"id": 1}]


def test_inventario_route_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake_obtener_inventario_paginado_controller(limit, offset, busqueda, solo_con_stock):
        calls.append({
            "limit": limit,
            "offset": offset,
            "busqueda": busqueda,
            "solo_con_stock": solo_con_stock,
        })
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"id": 9}]}

    monkeypatch.setattr(
        inventario,
        "obtener_inventario_paginado_controller",
        fake_obtener_inventario_paginado_controller,
    )

    response = inventario.obtener_inventario(
        limit=25,
        offset=50,
        busqueda="uniforme",
        solo_con_stock=True,
    )

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 9}]}
    assert calls == [{
        "limit": 25,
        "offset": 50,
        "busqueda": "uniforme",
        "solo_con_stock": True,
    }]
