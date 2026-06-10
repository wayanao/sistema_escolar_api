from app.routes import inventario


def test_inventario_route_keeps_legacy_list_response(monkeypatch):
    calls = []

    def fake_listado(estado="activo"):
        calls.append(estado)
        return [{"id": 1}]

    monkeypatch.setattr(inventario, "obtener_inventario_controller", fake_listado)

    response = inventario.obtener_inventario()

    assert response == [{"id": 1}]
    assert calls == ["activo"]


def test_inventario_route_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake_obtener_inventario_paginado_controller(limit, offset, busqueda, solo_con_stock, estado):
        calls.append({
            "limit": limit,
            "offset": offset,
            "busqueda": busqueda,
            "solo_con_stock": solo_con_stock,
            "estado": estado,
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
        estado="inactivo",
    )

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 9}]}
    assert calls == [{
        "limit": 25,
        "offset": 50,
        "busqueda": "uniforme",
        "solo_con_stock": True,
        "estado": "inactivo",
    }]


def test_inventario_route_rejects_invalid_estado_filter():
    try:
        inventario.obtener_inventario(estado="agotado")
    except Exception as exc:
        assert exc.status_code == 422
    else:
        raise AssertionError("Expected invalid estado filter to be rejected")


def test_actualizar_estado_inventario_route_returns_controller_result(monkeypatch):
    calls = []

    def fake_update(item_id, estado):
        calls.append((item_id, estado))
        return {"id": item_id, "estado": estado}

    monkeypatch.setattr(inventario, "actualizar_estado_inventario_controller", fake_update)

    result = inventario.actualizar_estado_producto(
        8,
        inventario.InventarioEstadoUpdate(estado="inactivo"),
    )

    assert calls == [(8, "inactivo")]
    assert result == {"id": 8, "estado": "inactivo"}


def test_inventario_delete_is_blocked():
    try:
        inventario.eliminar_producto(8)
    except Exception as exc:
        assert exc.status_code == 405
        assert "no se eliminan" in exc.detail
    else:
        raise AssertionError("Expected inventory deletion to be blocked")
