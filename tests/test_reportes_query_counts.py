import inspect

import pytest
from fastapi.routing import APIRoute

from app.controllers import (
    cartera_mora_controller,
    estado_cuenta_controller,
    reportes_controller,
)
from app.dependencies import get_current_active_admin
from app.routes import cartera, cuentas, reportes


TIPOS_PAGO_COLUMNS = [
    "id",
    "nombre",
    "valor",
    "tipo_cobro",
    "activo",
    "mes_inicial",
    "frecuencia_meses",
    "dia_limite_mes",
    "dias_gracia",
    "mora_tipo",
    "mora_valor",
]


class QueryCountingCursor:
    def __init__(self, student_count):
        self.student_count = student_count
        self.executed = []
        self.rows = []
        self.closed = False

    @property
    def students(self):
        return [
            (student_id, f"Nombre {student_id}", f"Apellido {student_id}")
            for student_id in range(1, self.student_count + 1)
        ]

    def execute(self, query, params=None):
        normalized = " ".join(str(query).lower().split())
        self.executed.append((normalized, params))
        self.rows = self._dispatch(normalized)

    def _dispatch(self, query):
        if "from information_schema.columns" in query:
            return [(column,) for column in TIPOS_PAGO_COLUMNS]
        if "from information_schema.tables" in query:
            return [(1,)]
        if "from tipos_de_pagos" in query and "order by id" in query:
            return [(4, "Pensión", 100, "unico", True, None, 1, None, 0, None, 0)]
        if "select curso_id, tipo_pago_id, valor" in query:
            return [(3, 4, 100)]
        if "from tipos_pagos_cursos" in query:
            return [(4, 100)]
        if "from tipos_pagos_estudiantes" in query:
            return []
        if "c.id as curso_id" in query and "from estudiantes e" in query:
            return [
                (student_id, nombre, apellido, "Activo", 3, "Curso 3")
                for student_id, nombre, apellido in self.students
            ]
        if (
            "select e.id, e.nombre, e.apellido" in query
            and "where e.curso_id" in query
        ):
            return self.students
        if "select id, nombre, apellido" in query and "where curso_id" in query:
            return self.students
        if "select c.id" in query and "where e.id" in query:
            return [(3,)]
        if "string_agg(distinct descripcion" in query:
            return [(0, None)]
        if "select concepto_id, coalesce(sum(monto), 0)" in query:
            return []
        if "select tipo_pago, coalesce(sum(monto), 0)" in query:
            return []
        if "from pagos_aplicaciones" in query:
            return []
        if "from pagos" in query and "group by" in query:
            return []
        if "concepto_id is null" in query:
            return [(0,)]
        if "from ventas" in query:
            return []
        raise AssertionError(f"Consulta no caracterizada: {query}")

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self):
        self.closed = True


class QueryCountingConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.closed = False
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def _connection_for(student_count):
    cursor = QueryCountingCursor(student_count)
    return QueryCountingConnection(cursor), cursor


def _api_routes(*routers):
    return {
        route.path: route
        for router in routers
        for route in router.routes
        if isinstance(route, APIRoute)
    }


def test_financial_report_http_boundary_is_admin_only_sync_get():
    routes = _api_routes(reportes.router, cuentas.router, cartera.router)
    expected_paths = {
        "/reportes/general",
        "/reportes/estado-cuenta/{curso_id}",
        "/reportes/ingresos-mes/{mes}",
        "/reportes/ingresos-rango",
        "/reportes/egresos-rango",
        "/estado-cuenta/curso/{curso_id}",
        "/estado-cuenta/estudiante/{estudiante_id}",
        "/cartera/mora",
        "/cartera/mora/resumen",
    }

    assert set(routes) == expected_paths
    for route in routes.values():
        assert route.methods == {"GET"}
        assert route.status_code is None
        assert route.response_model is None
        assert route.dependant.body_params == []
        assert not inspect.iscoroutinefunction(route.endpoint)
        assert any(
            dependency.call is get_current_active_admin
            for dependency in route.dependant.dependencies
        )


@pytest.mark.parametrize(
    ("student_count", "expected_queries"),
    [(0, 6), (1, 15), (3, 25)],
)
def test_financial_report_account_characterizes_five_queries_per_student(
    monkeypatch,
    student_count,
    expected_queries,
):
    connection, cursor = _connection_for(student_count)
    monkeypatch.setattr(reportes_controller, "get_connection", lambda: connection)

    result = reportes_controller.reporte_estado_cuenta_curso_controller(3)

    assert len(result) == student_count
    assert len(cursor.executed) == expected_queries
    assert cursor.closed is True
    assert connection.closed is True
    assert connection.committed is False


@pytest.mark.parametrize(
    ("student_count", "expected_queries"),
    [(0, 1), (1, 13), (3, 37)],
)
def test_account_course_consumer_characterizes_twelve_queries_per_student(
    monkeypatch,
    student_count,
    expected_queries,
):
    connection, cursor = _connection_for(student_count)
    monkeypatch.setattr(
        estado_cuenta_controller,
        "get_connection",
        lambda: connection,
    )

    result = estado_cuenta_controller.estado_cuenta_curso_controller(3)

    assert len(result) == student_count
    assert len(cursor.executed) == expected_queries
    assert cursor.closed is True
    assert connection.closed is True
    assert connection.committed is False


@pytest.mark.parametrize(
    ("student_count", "expected_queries"),
    [(0, 5), (1, 12), (3, 12)],
)
def test_overdue_portfolio_keeps_grouped_query_count_constant(
    monkeypatch,
    student_count,
    expected_queries,
):
    connection, cursor = _connection_for(student_count)
    monkeypatch.setattr(
        cartera_mora_controller,
        "get_connection",
        lambda: connection,
    )

    result = cartera_mora_controller.reporte_cartera_vencida()

    assert len(result) == student_count
    assert len(cursor.executed) == expected_queries
    assert cursor.closed is True
    assert connection.closed is True
    assert connection.committed is False
