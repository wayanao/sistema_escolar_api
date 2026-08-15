import datetime
import re
from pathlib import Path

from app.controllers import reportes_controller
from app.repositories import reportes_repository
from app.services import cobros, reportes_financieros


TIPOS_PAGO = [
    {"id": 10, "nombre": "Matrícula"},
    {"id": 20, "nombre": "Pensión"},
]
ASIGNACIONES_CURSO = {10: 100.0, 20: 200.0}
ESTUDIANTES = [
    (8, "Beto", "Álvarez"),
    (7, "Ana", "Zuluaga"),
]
PAGOS_DESCRIPCION = {
    7: [("Matrícula", 80), ("Pensión", 60)],
    8: [("Matrícula", 40), ("Pensión", 50)],
}
PAGOS_NOMBRE = {
    7: [("MATRÍCULA", 30)],
    8: [("MATRÍCULA", 0)],
}
VALORES_PERSONALIZADOS = {
    7: {20: 250.0},
    8: {10: 0.0},
}
PAGOS_APLICADOS = {7: {"pensión": 20.0}}
OTROS_PAGOS = {7: 15.0, 8: 0.0}


def _normalizar_sql(query):
    return " ".join(str(query).lower().split())


class EstadoCuentaCursor:
    def __init__(self, fail_pattern=None):
        self.fail_pattern = fail_pattern
        self.executed = []
        self.rows = []
        self.closed = False

    def execute(self, query, params=None):
        normalized = _normalizar_sql(query)
        self.executed.append((normalized, params))
        if self.fail_pattern and self.fail_pattern in normalized:
            raise RuntimeError("fallo-controlado")
        self.rows = self._dispatch(normalized, params)

    def _dispatch(self, query, params):
        if "from pagos" in query and re.search(r"\bconcepto_id\b", query):
            raise AssertionError(
                "El schema canónico de pagos no contiene concepto_id"
            )

        if (
            "select e.id, e.nombre, e.apellido" in query
            and "where e.curso_id = %s" in query
        ):
            return ESTUDIANTES

        if "select estudiante_id, descripcion" in query:
            return [
                (7, "Matrícula", 80),
                (8, "Pensión", 50),
                (7, "Pensión", 60),
                (8, "Matrícula", 40),
            ]
        if "select descripcion, coalesce(sum(monto), 0)" in query:
            return PAGOS_DESCRIPCION[params[0]]

        if "select estudiante_id, tipo_pago" in query:
            return [
                (8, "MATRÍCULA", 0),
                (7, "MATRÍCULA", 30),
                (7, " MATRÍCULA ", 90),
            ]
        if "select tipo_pago, coalesce(sum(monto), 0)" in query:
            return PAGOS_NOMBRE[params[0]]

        if "venta_id is not null" in query:
            if "select estudiante_id," in query:
                return [(7, 15)]
            return [(OTROS_PAGOS[params[0]],)]

        raise AssertionError(f"Consulta no caracterizada: {query}")

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self):
        self.closed = True


class EstadoCuentaConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def _instalar_dependencias(monkeypatch, cursor):
    connection = EstadoCuentaConnection(cursor)
    contexts = []

    monkeypatch.setattr(
        reportes_controller,
        "get_connection",
        lambda: connection,
    )
    monkeypatch.setattr(
        reportes_controller,
        "obtener_tipos_pago",
        lambda _cursor: TIPOS_PAGO,
    )
    monkeypatch.setattr(
        reportes_controller,
        "obtener_asignaciones_cobro_por_curso",
        lambda _cursor, _curso_id: ASIGNACIONES_CURSO,
    )
    monkeypatch.setattr(
        reportes_controller,
        "obtener_pagos_por_concepto_estudiantes",
        lambda _cursor, _ids: (
            {7: {"matrícula": 999.0}},
            {7: {"matrícula": 888.0}},
            PAGOS_APLICADOS,
        ),
    )
    monkeypatch.setattr(
        reportes_controller,
        "tabla_pagos_aplicaciones_existe",
        lambda _cursor: True,
    )
    monkeypatch.setattr(
        reportes_controller,
        "obtener_valores_personalizados_estudiante",
        lambda _cursor, estudiante_id: VALORES_PERSONALIZADOS[estudiante_id],
        raising=False,
    )
    def obtener_valores_agrupados(_cursor, estudiante_ids):
        assert estudiante_ids == (8, 7)
        return VALORES_PERSONALIZADOS

    monkeypatch.setattr(
        reportes_controller,
        "obtener_valores_personalizados_por_estudiantes",
        obtener_valores_agrupados,
        raising=False,
    )

    def calcular_resumen(**contexto):
        contexts.append(contexto)
        assert contexto["tipos_pago"] is TIPOS_PAGO
        assert contexto["asignaciones_curso"] is ASIGNACIONES_CURSO
        assert contexto["pagos_descripcion"] == {}

        if contexto["valores_estudiante"] == {10: 0.0}:
            assert contexto["pagos_nombre"] == {
                "matrícula": 0.0,
                "pensión": 50.0,
            }
            assert contexto["pagos_aplicados"] == {}
            return {
                "deudas": [
                    {
                        "concepto": "Matrícula",
                        "valor_total": 0.0,
                        "pagado": 0.0,
                        "deuda": 0.0,
                        "mora": 0.0,
                        "cuotas_vencidas": 0,
                    },
                    {
                        "concepto": "Pensión",
                        "valor_total": 200.0,
                        "pagado": 50.0,
                        "deuda": 150.0,
                        "mora": 0.0,
                        "cuotas_vencidas": 0,
                    },
                ]
            }

        assert contexto["valores_estudiante"] == {20: 250.0}
        assert contexto["pagos_nombre"] == {
            " matrícula ": 90.0,
            "matrícula": 30.0,
            "pensión": 60.0,
        }
        assert contexto["pagos_aplicados"] == {"pensión": 20.0}
        return {
            "deudas": [
                {
                    "concepto": "Matrícula",
                    "valor_total": 100.0,
                    "pagado": 30.0,
                    "deuda": 70.0,
                    "mora": 0.0,
                    "cuotas_vencidas": 0,
                },
                {
                    "concepto": "Pensión",
                    "valor_total": 250.0,
                    "pagado": 80.0,
                    "deuda": 170.0,
                    "mora": 0.0,
                    "cuotas_vencidas": 0,
                },
            ]
        }

    monkeypatch.setattr(
        reportes_financieros,
        "calcular_deudas_desde_contexto",
        calcular_resumen,
    )
    return connection, contexts


def test_estado_cuenta_preserva_reglas_orden_totales_y_aislamiento(monkeypatch):
    cursor = EstadoCuentaCursor()
    connection, contexts = _instalar_dependencias(monkeypatch, cursor)

    result = reportes_controller.reporte_estado_cuenta_curso_controller(3)

    assert result == [
        {
            "id": 8,
            "nombre": "Beto",
            "apellido": "Álvarez",
            "pagado": 50.0,
            "total": 200.0,
            "deuda": 150.0,
            "deudas_detalle": [
                {
                    "concepto": "Matrícula",
                    "valor_total": 0.0,
                    "pagado": 0.0,
                    "deuda": 0.0,
                    "mora": 0.0,
                    "cuotas_vencidas": 0,
                },
                {
                    "concepto": "Pensión",
                    "valor_total": 200.0,
                    "pagado": 50.0,
                    "deuda": 150.0,
                    "mora": 0.0,
                    "cuotas_vencidas": 0,
                },
            ],
        },
        {
            "id": 7,
            "nombre": "Ana",
            "apellido": "Zuluaga",
            "pagado": 125.0,
            "total": 365.0,
            "deuda": 240.0,
            "deudas_detalle": [
                {
                    "concepto": "Matrícula",
                    "valor_total": 100.0,
                    "pagado": 30.0,
                    "deuda": 70.0,
                    "mora": 0.0,
                    "cuotas_vencidas": 0,
                },
                {
                    "concepto": "Pensión",
                    "valor_total": 250.0,
                    "pagado": 80.0,
                    "deuda": 170.0,
                    "mora": 0.0,
                    "cuotas_vencidas": 0,
                },
                {
                    "concepto": "Otros Pagos",
                    "valor_total": 0,
                    "pagado": 15.0,
                    "deuda": -15.0,
                },
            ],
        },
    ]
    assert len(contexts) == 2

    students_query, students_params = next(
        (query, params) for query, params in cursor.executed
        if "select e.id, e.nombre, e.apellido" in query
    )
    assert "join cursos c on e.curso_id = c.id" in students_query
    assert "where e.curso_id = %s" in students_query
    assert "order by e.apellido, e.nombre" in students_query
    assert students_params == (3,)

    payment_executions = [
        (query, params) for query, params in cursor.executed
        if "from pagos" in query
    ]
    payment_queries = [query for query, _params in payment_executions]
    assert len(payment_executions) == 3
    assert payment_queries
    assert all(params == ((8, 7),) for _query, params in payment_executions)
    assert all(
        "coalesce(estado, 'pagado') <> 'anulado'" in query
        for query in payment_queries
    )
    description_query = next(
        query for query in payment_queries
        if "group by estudiante_id, descripcion" in query
    )
    assert "descripcion is not null" in description_query
    assert "venta_id is null" in description_query
    assert "not exists" in description_query
    name_query = next(
        query for query in payment_queries
        if "group by estudiante_id, tipo_pago" in query
    )
    assert "lower(tipo_pago)" not in name_query
    assert "venta_id is null" in name_query
    assert "not exists" in name_query
    others_queries = [
        query for query in payment_queries
        if "venta_id is not null" in query
    ]
    assert len(others_queries) == 1
    others_query = others_queries[0]
    expected_other_classification = (
        "and ( venta_id is not null or not exists ( select 1 "
        "from tipos_de_pagos tp where ( pagos.tipo_pago is not null "
        "and pagos.tipo_pago <> '' "
        "and lower(pagos.tipo_pago) = lower(tp.nombre) ) or ( "
        "pagos.descripcion is not null and pagos.descripcion <> '' "
        "and lower(pagos.descripcion) = lower(tp.nombre) ) ) )"
    )
    assert expected_other_classification in others_query
    assert all("not exists" in query for query in others_queries)
    assert all("from pagos_aplicaciones pa" in query for query in others_queries)
    assert all(
        "not exists ( select 1 from tipos_de_pagos tp" in query
        for query in others_queries
    )
    assert all(
        "pagos.descripcion is not null" in query
        and "pagos.descripcion <> ''" in query
        and "lower(pagos.descripcion) = lower(tp.nombre)" in query
        for query in others_queries
    )
    assert all(
        "pagos.tipo_pago is not null" in query
        and "pagos.tipo_pago <> ''" in query
        and "lower(pagos.tipo_pago) = lower(tp.nombre)" in query
        for query in others_queries
    )
    assert all("pa.pago_id = pagos.id" in query for query in others_queries)
    assert "tp.activo" not in others_query
    assert all("pa.activo" not in query for query in payment_queries)
    assert all("pa.periodo" not in query for query in payment_queries)
    assert all("trim(" not in query for query in payment_queries)
    assert all("concepto_id" not in query for query in payment_queries)

    assert cursor.closed is True
    assert connection.closed is True
    assert connection.committed is False
    assert connection.rolled_back is False


def test_estado_cuenta_error_conserva_fallback_y_cierres(monkeypatch):
    cursor = EstadoCuentaCursor(
        fail_pattern="descripcion, coalesce(sum(monto), 0)",
    )
    connection, _contexts = _instalar_dependencias(monkeypatch, cursor)

    result = reportes_controller.reporte_estado_cuenta_curso_controller(3)

    assert result == []
    assert cursor.closed is True
    assert connection.closed is True
    assert connection.committed is False
    assert connection.rolled_back is False


def test_estado_cuenta_error_de_regla_conserva_fallback_y_cierres(monkeypatch):
    cursor = EstadoCuentaCursor()
    connection, _contexts = _instalar_dependencias(monkeypatch, cursor)

    def fallar_calculo(**_contexto):
        raise RuntimeError("fallo-controlado-de-regla")

    monkeypatch.setattr(
        reportes_financieros,
        "calcular_deudas_desde_contexto",
        fallar_calculo,
    )

    result = reportes_controller.reporte_estado_cuenta_curso_controller(3)

    assert result == []
    assert cursor.closed is True
    assert connection.closed is True
    assert connection.committed is False
    assert connection.rolled_back is False


def test_estado_cuenta_propaga_ausencia_de_tabla_de_aplicaciones(monkeypatch):
    cursor = EstadoCuentaCursor()
    connection, _contexts = _instalar_dependencias(monkeypatch, cursor)
    monkeypatch.setattr(
        reportes_controller,
        "tabla_pagos_aplicaciones_existe",
        lambda _cursor: False,
    )

    result = reportes_controller.reporte_estado_cuenta_curso_controller(3)

    assert result
    payment_queries = [
        query for query, _params in cursor.executed
        if "from pagos" in query
    ]
    assert len(payment_queries) == 3
    assert all(
        "from pagos_aplicaciones pa" not in query
        for query in payment_queries
    )
    others_query = next(
        query for query in payment_queries
        if "venta_id is not null" in query
    )
    assert "from tipos_de_pagos tp" in others_query
    assert connection.closed is True


class CobrosCharacterizationCursor:
    def __init__(self):
        self.executed = []
        self.rows = []

    def execute(self, query, params=None):
        normalized = _normalizar_sql(query)
        self.executed.append((normalized, params))

        if "from information_schema.tables" in normalized:
            self.rows = [(1,)]
        elif "from tipos_pagos_estudiantes" in normalized:
            self.rows = [(7, 20, 250), (8, 10, 0)]
        elif "lower(coalesce(tipo_pago, ''))" in normalized:
            self.rows = [(7, "transferencia", 25)]
        elif "lower(coalesce(descripcion, ''))" in normalized:
            self.rows = []
        elif "from pagos_aplicaciones pa" in normalized:
            if "pa.periodo <= %s" in normalized:
                self.rows = [(7, "pensión", 100)]
            else:
                self.rows = [(7, "pensión", 200)]
        else:
            raise AssertionError(f"Consulta no caracterizada: {normalized}")

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None


def test_valores_personalizados_agrupados_preservan_cada_estudiante():
    cursor = CobrosCharacterizationCursor()

    result = cobros.obtener_valores_personalizados_por_estudiantes(
        cursor,
        (7, 8),
    )

    assert result == {7: {20: 250.0}, 8: {10: 0.0}}
    values_query, values_params = cursor.executed[-1]
    assert "where estudiante_id in %s and activo = true" in values_query
    assert values_params == ((7, 8),)


def test_aplicaciones_agrupadas_incluyen_solo_periodos_maduros():
    cursor = CobrosCharacterizationCursor()

    pagos_nombre, pagos_descripcion, pagos_aplicados = (
        cobros.obtener_pagos_por_concepto_estudiantes(
            cursor,
            (7, 8),
            hoy=datetime.date(2026, 5, 27),
        )
    )

    assert pagos_nombre == {7: {"transferencia": 25.0}}
    assert pagos_descripcion == {}
    assert pagos_aplicados == {7: {"pensión": 100.0}}

    regular_payment_queries = [
        query for query, _params in cursor.executed
        if "lower(coalesce(tipo_pago, ''))" in query
        or "lower(coalesce(descripcion, ''))" in query
    ]
    assert len(regular_payment_queries) == 2
    assert all("not exists" in query for query in regular_payment_queries)

    applications_query, applications_params = cursor.executed[-1]
    assert "pa.activo = true" in applications_query
    assert "pa.periodo <= %s" in applications_query
    assert "coalesce(p.estado, 'pagado') <> 'anulado'" in applications_query
    assert applications_params == ((7, 8), datetime.date(2026, 5, 1))


def test_otros_pagos_no_referencia_aplicaciones_si_la_tabla_no_existe():
    cursor = EstadoCuentaCursor()

    result = reportes_repository.consultar_otros_pagos_por_estudiantes(
        cursor,
        (7, 8),
        False,
    )

    assert result == [(7, 15)]
    query, params = cursor.executed[-1]
    assert "from pagos_aplicaciones pa" not in query
    assert "from tipos_de_pagos tp" in query
    assert "group by estudiante_id" in query
    assert params == ((7, 8),)


def test_estado_cuenta_no_requiere_concepto_id_en_schema_canonico():
    schema_path = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "base"
        / "20260813_esquema_base_tenant.sql"
    )
    schema = schema_path.read_text(encoding="utf-8")
    pagos_ddl = schema.split(
        "CREATE TABLE IF NOT EXISTS pagos (",
        maxsplit=1,
    )[1].split(");", maxsplit=1)[0]
    assert "concepto_id" not in pagos_ddl

    cursor = EstadoCuentaCursor()
    pagos_descripcion, pagos_legacy = (
        reportes_repository.consultar_pagos_estado_cuenta_por_estudiantes(
            cursor,
            (7, 8),
            True,
        )
    )
    otros = reportes_repository.consultar_otros_pagos_por_estudiantes(
        cursor,
        (7, 8),
        True,
    )

    assert pagos_descripcion
    assert pagos_legacy
    assert otros == [(7, 15)]
    assert all("concepto_id" not in query for query, _params in cursor.executed)
