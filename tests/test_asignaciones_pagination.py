from contextlib import contextmanager

from app.routes import asignaciones


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((query, params))

    def fetchall(self):
        return self.rows

    def close(self):
        pass


def test_mis_clases_incluye_jornada_del_curso(monkeypatch):
    cursor = FakeCursor([
        (11, 12, "Matemáticas", "Sexto A", 4, "Tarde", "Lunes", "13:00", "14:00"),
    ])

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        yield cursor

    monkeypatch.setattr(asignaciones, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(asignaciones, "require_profesor_scope", lambda *args, **kwargs: None)

    response = asignaciones.obtener_clases_profesor(
        profesor_id=3,
        current_user={"id": 3, "rol": "profesor"},
    )

    assert response == [{
        "id": 11,
        "horario_id": 12,
        "materia": "Matemáticas",
        "curso": "Sexto A",
        "curso_id": 4,
        "jornada": "Tarde",
        "dia": "Lunes",
        "hora_inicio": "13:00",
        "hora_fin": "14:00",
    }]
    assert "c.jornada" in cursor.queries[0][0]


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
