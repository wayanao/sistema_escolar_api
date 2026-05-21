from app.routes import cursos, materias, profesores, usuario


def test_profesores_keeps_legacy_list_response(monkeypatch):
    monkeypatch.setattr(profesores, "obtener_profesores_controller", lambda: [{"id": 1}])

    assert profesores.obtener_profesores() == [{"id": 1}]


def test_profesores_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake(limit, offset, busqueda):
        calls.append({"limit": limit, "offset": offset, "busqueda": busqueda})
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"id": 9}]}

    monkeypatch.setattr(profesores, "obtener_profesores_paginado_controller", fake)

    response = profesores.obtener_profesores(limit=25, offset=50, busqueda="ana")

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 9}]}
    assert calls == [{"limit": 25, "offset": 50, "busqueda": "ana"}]


def test_cursos_keeps_legacy_list_response(monkeypatch):
    monkeypatch.setattr(cursos, "obtener_cursos_controller", lambda: [{"id": 1}])

    assert cursos.obtener_cursos() == [{"id": 1}]


def test_cursos_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake(limit, offset, busqueda):
        calls.append({"limit": limit, "offset": offset, "busqueda": busqueda})
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"id": 9}]}

    monkeypatch.setattr(cursos, "obtener_cursos_paginado_controller", fake)

    response = cursos.obtener_cursos(limit=25, offset=50, busqueda="primero")

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 9}]}
    assert calls == [{"limit": 25, "offset": 50, "busqueda": "primero"}]


def test_materias_keeps_legacy_list_response(monkeypatch):
    monkeypatch.setattr(materias, "obtener_materias_controller", lambda: [{"id": 1}])

    assert materias.obtener_materias() == [{"id": 1}]


def test_materias_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake(limit, offset, busqueda):
        calls.append({"limit": limit, "offset": offset, "busqueda": busqueda})
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"id": 9}]}

    monkeypatch.setattr(materias, "obtener_materias_paginado_controller", fake)

    response = materias.obtener_materias(limit=25, offset=50, busqueda="math")

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 9}]}
    assert calls == [{"limit": 25, "offset": 50, "busqueda": "math"}]


def test_usuarios_keeps_legacy_list_response(monkeypatch):
    monkeypatch.setattr(usuario, "obtener_usuarios_controller", lambda: [{"id": 1}])

    assert usuario.obtener_usuarios() == [{"id": 1}]


def test_usuarios_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake(limit, offset, busqueda, rol):
        calls.append({"limit": limit, "offset": offset, "busqueda": busqueda, "rol": rol})
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"id": 9}]}

    monkeypatch.setattr(usuario, "obtener_usuarios_paginado_controller", fake)

    response = usuario.obtener_usuarios(limit=25, offset=50, busqueda="admin", rol="admin")

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 9}]}
    assert calls == [{"limit": 25, "offset": 50, "busqueda": "admin", "rol": "admin"}]
