from app.routes import cursos, materias, profesores, usuario


def test_profesores_keeps_legacy_list_response(monkeypatch):
    calls = []

    def fake_listado(estado="activo"):
        calls.append(estado)
        return [{"id": 1}]

    monkeypatch.setattr(profesores, "obtener_profesores_controller", fake_listado)

    assert profesores.obtener_profesores() == [{"id": 1}]
    assert calls == ["activo"]


def test_profesores_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake(limit, offset, busqueda, estado):
        calls.append({"limit": limit, "offset": offset, "busqueda": busqueda, "estado": estado})
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"id": 9}]}

    monkeypatch.setattr(profesores, "obtener_profesores_paginado_controller", fake)

    response = profesores.obtener_profesores(limit=25, offset=50, busqueda="ana", estado="inactivo")

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 9}]}
    assert calls == [{"limit": 25, "offset": 50, "busqueda": "ana", "estado": "inactivo"}]


def test_profesores_rejects_invalid_estado_filter():
    try:
        profesores.obtener_profesores(estado="retirado")
    except Exception as exc:
        assert exc.status_code == 422
    else:
        raise AssertionError("Expected invalid estado filter to be rejected")


def test_actualizar_estado_profesor_route_returns_controller_result(monkeypatch):
    calls = []

    def fake_update(profesor_id, estado):
        calls.append((profesor_id, estado))
        return {"id": profesor_id, "estado": estado}

    monkeypatch.setattr(profesores, "actualizar_estado_profesor_controller", fake_update)

    result = profesores.actualizar_estado_profesor(
        4,
        profesores.ProfesorEstadoUpdate(estado="inactivo"),
    )

    assert calls == [(4, "inactivo")]
    assert result == {"id": 4, "estado": "inactivo"}


def test_cursos_keeps_legacy_list_response(monkeypatch):
    calls = []

    def fake_listado(estado="activo"):
        calls.append(estado)
        return [{"id": 1}]

    monkeypatch.setattr(cursos, "obtener_cursos_controller", fake_listado)

    assert cursos.obtener_cursos() == [{"id": 1}]
    assert calls == ["activo"]


def test_cursos_returns_paginated_response_when_limit_is_sent(monkeypatch):
    calls = []

    def fake(limit, offset, busqueda, estado):
        calls.append({"limit": limit, "offset": offset, "busqueda": busqueda, "estado": estado})
        return {"total": 1, "limit": limit, "offset": offset, "items": [{"id": 9}]}

    monkeypatch.setattr(cursos, "obtener_cursos_paginado_controller", fake)

    response = cursos.obtener_cursos(limit=25, offset=50, busqueda="primero", estado="inactivo")

    assert response == {"total": 1, "limit": 25, "offset": 50, "items": [{"id": 9}]}
    assert calls == [{"limit": 25, "offset": 50, "busqueda": "primero", "estado": "inactivo"}]


def test_cursos_rejects_invalid_estado_filter():
    try:
        cursos.obtener_cursos(estado="retirado")
    except Exception as exc:
        assert exc.status_code == 422
    else:
        raise AssertionError("Expected invalid estado filter to be rejected")


def test_actualizar_estado_curso_route_returns_controller_result(monkeypatch):
    calls = []

    def fake_update(curso_id, estado):
        calls.append((curso_id, estado))
        return {"id": curso_id, "estado": estado}

    monkeypatch.setattr(cursos, "actualizar_estado_curso_controller", fake_update)

    result = cursos.actualizar_estado_curso(
        5,
        cursos.CursoEstadoUpdate(estado="inactivo"),
    )

    assert calls == [(5, "inactivo")]
    assert result == {"id": 5, "estado": "inactivo"}


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
