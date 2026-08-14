import datetime

import pytest

from app.controllers import reportes_controller


def _normalize_sql(query):
    return " ".join(query.split())


GENERAL_STATS_SQL = _normalize_sql(
    """
    SELECT
        (SELECT COUNT(*) FROM estudiantes) as total_estudiantes,
        (SELECT COUNT(*) FROM profesor) as total_profesores,
        (SELECT COUNT(*) FROM cursos) as total_cursos,
        (SELECT COUNT(*) FROM materias) as total_materias,
        (SELECT COALESCE(SUM(monto), 0) FROM pagos WHERE COALESCE(estado, 'Pagado') <> 'Anulado') as total_ingresos,
        (
            SELECT COALESCE(SUM(monto), 0)
            FROM pagos
            WHERE DATE(COALESCE(fecha, fecha_pago::timestamp)) = (NOW() AT TIME ZONE 'America/Bogota')::date
              AND COALESCE(estado, 'Pagado') <> 'Anulado'
        ) as ingresos_hoy,
        (SELECT COALESCE(SUM(monto), 0) FROM egresos) as total_egresos,
        (
            SELECT COALESCE(SUM(monto), 0)
            FROM egresos
            WHERE fecha::date = (NOW() AT TIME ZONE 'America/Bogota')::date
        ) as egresos_hoy
    """
)

GENERAL_STUDENTS_SQL = _normalize_sql(
    """
    SELECT
        c.nombre as curso,
        COUNT(e.id) as cantidad_estudiantes
    FROM cursos c
    LEFT JOIN estudiantes e ON c.id = e.curso_id
    GROUP BY c.id, c.nombre
    ORDER BY c.nombre
    """
)

GENERAL_INCOME_SQL = _normalize_sql(
    """
    SELECT
        TO_CHAR(COALESCE(fecha, fecha_pago::timestamp), 'YYYY-MM') as mes,
        SUM(CASE WHEN COALESCE(estado, 'Pagado') = 'Anulado' THEN 0 ELSE monto END) as total
    FROM pagos
    WHERE COALESCE(fecha, fecha_pago::timestamp) >= CURRENT_DATE - INTERVAL '6 months'
    GROUP BY TO_CHAR(COALESCE(fecha, fecha_pago::timestamp), 'YYYY-MM')
    ORDER BY mes DESC
    """
)

GENERAL_EXPENSE_SQL = _normalize_sql(
    """
    SELECT
        TO_CHAR(fecha::date, 'YYYY-MM') as mes,
        SUM(monto) as total
    FROM egresos
    WHERE fecha::date >= CURRENT_DATE - INTERVAL '6 months'
    GROUP BY TO_CHAR(fecha::date, 'YYYY-MM')
    ORDER BY mes DESC
    """
)

MONTH_COUNT_SQL = _normalize_sql(
    """
    SELECT COUNT(*)
    FROM pagos p
    WHERE TO_CHAR(COALESCE(p.fecha, p.fecha_pago::timestamp), 'YYYY-MM') = %s
    """
)

MONTH_ITEMS_SQL = _normalize_sql(
    """
    SELECT
        p.id,
        e.nombre,
        e.apellido,
        p.monto,
        COALESCE(p.fecha, p.fecha_pago::timestamp) AS fecha,
        p.descripcion,
        p.tipo_pago,
        COALESCE(p.estado, 'Pagado') AS estado,
        p.motivo_anulacion,
        p.fecha_anulacion
    FROM pagos p
    LEFT JOIN estudiantes e ON p.estudiante_id = e.id
    WHERE TO_CHAR(COALESCE(p.fecha, p.fecha_pago::timestamp), 'YYYY-MM') = %s
    ORDER BY COALESCE(p.fecha, p.fecha_pago::timestamp) DESC
    """
)

MONTH_ITEMS_PAGED_SQL = MONTH_ITEMS_SQL + " LIMIT %s OFFSET %s"

RANGE_COUNT_SQL = _normalize_sql(
    """
    SELECT COUNT(*)
    FROM pagos p
    WHERE COALESCE(p.fecha, p.fecha_pago::timestamp) >= %s::date
      AND COALESCE(p.fecha, p.fecha_pago::timestamp) < %s::date + interval '1 day'
    """
)

RANGE_ITEMS_SQL = _normalize_sql(
    """
    SELECT
        p.id,
        e.nombre,
        e.apellido,
        p.monto,
        COALESCE(p.fecha, p.fecha_pago::timestamp) AS fecha,
        p.descripcion,
        p.tipo_pago,
        COALESCE(p.estado, 'Pagado') AS estado,
        p.motivo_anulacion,
        p.fecha_anulacion
    FROM pagos p
    LEFT JOIN estudiantes e ON p.estudiante_id = e.id
    WHERE COALESCE(p.fecha, p.fecha_pago::timestamp) >= %s::date
      AND COALESCE(p.fecha, p.fecha_pago::timestamp) < %s::date + interval '1 day'
    ORDER BY COALESCE(p.fecha, p.fecha_pago::timestamp) DESC
    """
)

RANGE_ITEMS_PAGED_SQL = RANGE_ITEMS_SQL + " LIMIT %s OFFSET %s"

EXPENSE_COUNT_SQL = _normalize_sql(
    """
    SELECT COUNT(*)
    FROM egresos
    WHERE fecha::date >= %s::date
      AND fecha::date < %s::date + interval '1 day'
    """
)

EXPENSE_ITEMS_SQL = _normalize_sql(
    """
    SELECT id, concepto, monto, fecha, categoria, notas, COALESCE(origen, 'manual') AS origen
    FROM egresos
    WHERE fecha::date >= %s::date
      AND fecha::date < %s::date + interval '1 day'
    ORDER BY fecha DESC, id DESC
    """
)

EXPENSE_ITEMS_PAGED_SQL = EXPENSE_ITEMS_SQL + " LIMIT %s OFFSET %s"


INCOME_ROW = (
    20,
    None,
    "Apellido ignorado",
    60000,
    datetime.datetime(2026, 5, 27, 10, 30),
    None,
    None,
    " ANULADO ",
    "Error de caja",
    datetime.datetime(2026, 5, 28, 8, 15),
)

EXPECTED_INCOME = {
    "id": 20,
    "estudiante": "Desconocido",
    "monto": 60000.0,
    "monto_valido": 0,
    "fecha": "27/05/2026 10:30",
    "descripcion": "Sin descripción",
    "tipo_pago": None,
    "estado": " ANULADO ",
    "anulado": True,
    "motivo_anulacion": "Error de caja",
    "fecha_anulacion": "28/05/2026 08:15",
}

PAID_INCOME_ROW = (
    21,
    "Ana",
    "Ruiz",
    75000,
    datetime.datetime(2026, 5, 29, 14, 45),
    "Mensualidad",
    "Transferencia",
    None,
    None,
    None,
)

EXPECTED_PAID_INCOME = {
    "id": 21,
    "estudiante": "Ana Ruiz",
    "monto": 75000.0,
    "monto_valido": 75000.0,
    "fecha": "29/05/2026 14:45",
    "descripcion": "Mensualidad",
    "tipo_pago": "Transferencia",
    "estado": "Pagado",
    "anulado": False,
    "motivo_anulacion": None,
    "fecha_anulacion": None,
}

EXPENSE_ROW = (31, None, None, None, None, None, None)

EXPECTED_EXPENSE = {
    "id": 31,
    "concepto": "Sin concepto",
    "monto": 0.0,
    "fecha": None,
    "categoria": "Otros",
    "notas": "",
    "origen": "manual",
}

FULL_EXPENSE_ROW = (
    32,
    "Servicios",
    125000,
    datetime.datetime(2026, 5, 30, 9, 0),
    "Operación",
    "Factura 123",
    "importado",
)

EXPECTED_FULL_EXPENSE = {
    "id": 32,
    "concepto": "Servicios",
    "monto": 125000.0,
    "fecha": "30/05/2026",
    "categoria": "Operación",
    "notas": "Factura 123",
    "origen": "importado",
}


class ScriptedCursor:
    def __init__(self, fetches=(), fail_on_execute=None):
        self.fetches = list(fetches)
        self.fail_on_execute = fail_on_execute
        self.execute_count = 0
        self.events = []
        self.closed = False

    def execute(self, query, params=None):
        self.execute_count += 1
        self.events.append(("execute", _normalize_sql(query), params))
        if self.execute_count == self.fail_on_execute:
            raise RuntimeError("fallo-controlado")

    def fetchone(self):
        self.events.append(("fetchone",))
        return self.fetches.pop(0)

    def fetchall(self):
        self.events.append(("fetchall",))
        return self.fetches.pop(0)

    def close(self):
        self.events.append(("close",))
        self.closed = True


class ScriptedConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def _install_connection(monkeypatch, fetches=(), fail_on_execute=None):
    cursor = ScriptedCursor(fetches, fail_on_execute)
    connection = ScriptedConnection(cursor)
    monkeypatch.setattr(
        reportes_controller,
        "get_connection",
        lambda: connection,
    )
    return connection, cursor


def _assert_read_lifecycle(connection, cursor):
    assert cursor.closed is True
    assert connection.closed is True
    assert connection.committed is False


def _executions(cursor):
    return [event[1:] for event in cursor.events if event[0] == "execute"]


def test_general_characterizes_sql_fetch_order_payload_and_close(monkeypatch):
    connection, cursor = _install_connection(
        monkeypatch,
        fetches=[
            (3, 2, 1, 4, 120000, 50000, 30000, 10000),
            [("Primero", 3), ("Vacío", 0)],
            [("2026-05", 120000), ("2026-04", 0)],
            [("2026-05", 30000)],
        ],
    )

    result = reportes_controller.reporte_general_controller()

    assert result == {
        "estadisticas_generales": {
            "total_estudiantes": 3,
            "total_profesores": 2,
            "total_cursos": 1,
            "total_materias": 4,
            "total_ingresos": 120000.0,
            "ingresos_hoy": 50000.0,
            "total_egresos": 30000.0,
            "egresos_hoy": 10000.0,
            "balance_general": 90000.0,
            "balance_hoy": 40000.0,
        },
        "estudiantes_por_curso": [
            {"curso": "Primero", "cantidad": 3},
            {"curso": "Vacío", "cantidad": 0},
        ],
        "ingresos_mensuales": [
            {"mes": "2026-05", "total": 120000.0},
            {"mes": "2026-04", "total": 0.0},
        ],
        "egresos_mensuales": [{"mes": "2026-05", "total": 30000.0}],
    }
    assert _executions(cursor) == [
        (GENERAL_STATS_SQL, None),
        (GENERAL_STUDENTS_SQL, None),
        (GENERAL_INCOME_SQL, None),
        (GENERAL_EXPENSE_SQL, None),
    ]
    assert [event[0] for event in cursor.events] == [
        "execute",
        "fetchone",
        "execute",
        "fetchall",
        "execute",
        "fetchall",
        "execute",
        "fetchall",
        "close",
    ]
    _assert_read_lifecycle(connection, cursor)


def test_general_failure_discards_partial_results_and_closes(monkeypatch):
    connection, cursor = _install_connection(
        monkeypatch,
        fetches=[
            (3, 2, 1, 4, 120000, 50000, 30000, 10000),
            [("Primero", 3)],
            [("2026-05", 120000)],
        ],
        fail_on_execute=4,
    )

    result = reportes_controller.reporte_general_controller()

    assert result == {
        "estadisticas_generales": {
            "total_estudiantes": 0,
            "total_profesores": 0,
            "total_cursos": 0,
            "total_materias": 0,
            "total_ingresos": 0,
            "ingresos_hoy": 0,
            "total_egresos": 0,
            "egresos_hoy": 0,
            "balance_general": 0,
            "balance_hoy": 0,
        },
        "estudiantes_por_curso": [],
        "ingresos_mensuales": [],
        "egresos_mensuales": [],
    }
    assert cursor.execute_count == 4
    _assert_read_lifecycle(connection, cursor)


@pytest.mark.parametrize(
    ("controller", "args", "row", "expected", "expected_sql", "expected_params"),
    [
        (
            reportes_controller.reporte_ingresos_mes_controller,
            ("2026-05", None, 99),
            INCOME_ROW,
            EXPECTED_INCOME,
            MONTH_ITEMS_SQL,
            ("2026-05",),
        ),
        (
            reportes_controller.reporte_ingresos_rango_controller,
            ("2026-05-01", "2026-05-31", None, 99),
            INCOME_ROW,
            EXPECTED_INCOME,
            RANGE_ITEMS_SQL,
            ("2026-05-01", "2026-05-31"),
        ),
        (
            reportes_controller.reporte_egresos_rango_controller,
            ("2026-05-01", "2026-05-31", None, 99),
            EXPENSE_ROW,
            EXPECTED_EXPENSE,
            EXPENSE_ITEMS_SQL,
            ("2026-05-01", "2026-05-31"),
        ),
    ],
)
def test_simple_legacy_reports_characterize_sql_params_payload_and_close(
    monkeypatch,
    controller,
    args,
    row,
    expected,
    expected_sql,
    expected_params,
):
    connection, cursor = _install_connection(monkeypatch, fetches=[[row]])

    result = controller(*args)

    assert result == [expected]
    assert _executions(cursor) == [(expected_sql, expected_params)]
    assert [event[0] for event in cursor.events] == [
        "execute",
        "fetchall",
        "close",
    ]
    _assert_read_lifecycle(connection, cursor)


@pytest.mark.parametrize(
    (
        "controller",
        "args",
        "row",
        "expected",
        "count_sql",
        "count_params",
        "items_sql",
        "items_params",
    ),
    [
        (
            reportes_controller.reporte_ingresos_mes_controller,
            ("2026-05", 0, 7),
            INCOME_ROW,
            EXPECTED_INCOME,
            MONTH_COUNT_SQL,
            ("2026-05",),
            MONTH_ITEMS_PAGED_SQL,
            ("2026-05", 0, 7),
        ),
        (
            reportes_controller.reporte_ingresos_rango_controller,
            ("2026-05-01", "2026-05-31", 25, 50),
            INCOME_ROW,
            EXPECTED_INCOME,
            RANGE_COUNT_SQL,
            ("2026-05-01", "2026-05-31"),
            RANGE_ITEMS_PAGED_SQL,
            ("2026-05-01", "2026-05-31", 25, 50),
        ),
        (
            reportes_controller.reporte_egresos_rango_controller,
            ("2026-05-01", "2026-05-31", 25, 50),
            EXPENSE_ROW,
            EXPECTED_EXPENSE,
            EXPENSE_COUNT_SQL,
            ("2026-05-01", "2026-05-31"),
            EXPENSE_ITEMS_PAGED_SQL,
            ("2026-05-01", "2026-05-31", 25, 50),
        ),
    ],
)
def test_simple_paginated_reports_characterize_count_then_page(
    monkeypatch,
    controller,
    args,
    row,
    expected,
    count_sql,
    count_params,
    items_sql,
    items_params,
):
    connection, cursor = _install_connection(
        monkeypatch,
        fetches=[(7,), [row]],
    )

    result = controller(*args)

    assert result == {
        "total": 7,
        "limit": args[-2],
        "offset": args[-1],
        "items": [expected],
    }
    assert _executions(cursor) == [
        (count_sql, count_params),
        (items_sql, items_params),
    ]
    assert [event[0] for event in cursor.events] == [
        "execute",
        "fetchone",
        "execute",
        "fetchall",
        "close",
    ]
    _assert_read_lifecycle(connection, cursor)


@pytest.mark.parametrize(
    ("controller", "args"),
    [
        (reportes_controller.reporte_ingresos_mes_controller, ("2026-05", 25, 0)),
        (
            reportes_controller.reporte_ingresos_rango_controller,
            ("2026-05-01", "2026-05-31", 25, 0),
        ),
        (
            reportes_controller.reporte_egresos_rango_controller,
            ("2026-05-01", "2026-05-31", 25, 0),
        ),
    ],
)
def test_simple_report_failure_keeps_list_fallback_and_closes(
    monkeypatch,
    controller,
    args,
):
    connection, cursor = _install_connection(monkeypatch, fail_on_execute=1)

    result = controller(*args)

    assert result == []
    _assert_read_lifecycle(connection, cursor)


def test_simple_report_formatters_preserve_current_defaults():
    assert reportes_controller._formatear_ingreso(INCOME_ROW) == EXPECTED_INCOME
    assert reportes_controller._formatear_egreso(EXPENSE_ROW) == EXPECTED_EXPENSE


def test_simple_report_formatters_preserve_current_populated_values():
    assert (
        reportes_controller._formatear_ingreso(PAID_INCOME_ROW)
        == EXPECTED_PAID_INCOME
    )
    assert (
        reportes_controller._formatear_egreso(FULL_EXPENSE_ROW)
        == EXPECTED_FULL_EXPENSE
    )
