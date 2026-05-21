from app.routes import pagos


def test_pagos_route_keeps_legacy_list_response(monkeypatch):
    monkeypatch.setattr(pagos, "historial_pagos_controller", lambda estudiante_id: [{"pago_id": 1}])

    response = pagos.historial_pagos(estudiante_id=3)

    assert response == [{"pago_id": 1}]


def test_pagos_route_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake_historial_pagos_paginado_controller(estudiante_id, limit, offset):
        calls.append({
            "estudiante_id": estudiante_id,
            "limit": limit,
            "offset": offset,
        })
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"pago_id": 9}]}

    monkeypatch.setattr(
        pagos,
        "historial_pagos_paginado_controller",
        fake_historial_pagos_paginado_controller,
    )

    response = pagos.historial_pagos(estudiante_id=3, limit=25, offset=50)

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"pago_id": 9}]}
    assert calls == [{
        "estudiante_id": 3,
        "limit": 25,
        "offset": 50,
    }]
