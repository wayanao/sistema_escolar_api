from scripts import apply_tenant_indexes


class FakeCursor:
    def __init__(self, rows=None, one=None):
        self.rows = rows or []
        self.one = one
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((str(query), params))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.one


def test_index_list_contains_recommended_indexes():
    indexes = {(table, index_name, tuple(columns)) for table, index_name, columns in apply_tenant_indexes.INDEXES}

    assert ("estudiantes", "idx_estudiantes_curso_id", ("curso_id",)) in indexes
    assert ("asignaciones", "idx_asignaciones_profesor_id", ("profesor_id",)) in indexes
    assert ("asignaciones", "idx_asignaciones_curso_id", ("curso_id",)) in indexes
    assert (
        "notas_detalle",
        "idx_notas_detalle_estudiante_asignacion_periodo",
        ("estudiante_id", "asignacion_id", "periodo"),
    ) in indexes
    assert ("boletin_cabecera", "idx_boletin_cabecera_lookup", ("estudiante_id", "asignacion_id", "periodo")) in indexes
    assert ("asistencia", "idx_asistencia_asignacion_periodo", ("asignacion_id", "periodo")) in indexes
    assert ("asistencia", "idx_asistencia_estudiante_fecha", ("estudiante_id", "fecha")) in indexes
    assert ("pagos", "idx_pagos_estudiante_id", ("estudiante_id",)) in indexes
    assert ("pagos", "idx_pagos_fecha", ("fecha",)) in indexes
    assert ("pagos", "idx_pagos_fecha_pago", ("fecha_pago",)) in indexes
    assert ("ventas", "idx_ventas_estudiante_estado", ("estudiante_id", "estado")) in indexes
    assert ("plan_de_clases", "idx_plan_de_clases_asignacion_fecha", ("asignacion_id", "fecha")) in indexes


def test_columns_exist_returns_true_when_all_columns_are_present():
    cursor = FakeCursor(rows=[("estudiante_id",), ("asignacion_id",), ("periodo",)])

    assert apply_tenant_indexes.columns_exist(
        cursor,
        "tenant_demo",
        "notas_detalle",
        ["estudiante_id", "asignacion_id", "periodo"],
    )


def test_columns_exist_returns_false_when_any_column_is_missing():
    cursor = FakeCursor(rows=[("estudiante_id",), ("asignacion_id",)])

    assert not apply_tenant_indexes.columns_exist(
        cursor,
        "tenant_demo",
        "notas_detalle",
        ["estudiante_id", "asignacion_id", "periodo"],
    )


def test_create_index_uses_schema_qualified_table_and_safe_identifiers():
    cursor = FakeCursor()

    apply_tenant_indexes.create_index(
        cursor,
        "tenant_demo",
        "notas_detalle",
        "idx_notas_detalle_estudiante_asignacion_periodo",
        ["estudiante_id", "asignacion_id", "periodo"],
    )

    query = cursor.calls[0][0]
    assert "CREATE INDEX IF NOT EXISTS" in query
