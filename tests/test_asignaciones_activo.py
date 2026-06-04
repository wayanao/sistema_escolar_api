from app.controllers import asignacion_controller
from app.schemas.asignacion import AsignacionCreate


class FakeCursor:
    def __init__(self, fetchone_values=None, fetchall_values=None):
        self.queries = []
        self.fetchone_values = list(fetchone_values or [])
        self.fetchall_values = list(fetchall_values or [])

    def execute(self, query, params=None):
        self.queries.append((query, params))

    def fetchone(self):
        if self.fetchone_values:
            return self.fetchone_values.pop(0)
        return None

    def fetchall(self):
        if self.fetchall_values:
            return self.fetchall_values.pop(0)
        return []

    def close(self):
        pass


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.commits = 0

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def close(self):
        pass


def test_eliminar_asignacion_por_id_desactiva_sin_borrar(monkeypatch):
    cursor = FakeCursor(fetchone_values=[(7,)])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(asignacion_controller, "get_connection", lambda: conn)

    response = asignacion_controller.eliminar_asignacion_por_id_controller(7)

    sql_ejecutado = "\n".join(query for query, _ in cursor.queries).upper()
    assert response == {"mensaje": "Asignación desactivada. El historial académico se conserva."}
    assert "UPDATE ASIGNACIONES SET ACTIVO = FALSE" in sql_ejecutado
    assert "DELETE FROM ASIGNACIONES" not in sql_ejecutado
    assert "DELETE FROM NOTAS" not in sql_ejecutado
    assert conn.commits == 1


def test_obtener_disponibilidad_profesor_calcula_rangos_libres(monkeypatch):
    cursor = FakeCursor(fetchall_values=[
        [
            ("08:00", "09:00"),
            ("14:00", "15:30"),
        ]
    ])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(asignacion_controller, "get_connection", lambda: conn)

    response = asignacion_controller.obtener_disponibilidad_profesor_controller(3, "Lunes")

    manana = response["jornadas"][0]
    tarde = response["jornadas"][1]
    assert response["profesor_id"] == 3
    assert response["dia"] == "Lunes"
    assert manana["rangos"] == [
        {"inicio": "06:30", "fin": "08:00"},
        {"inicio": "09:00", "fin": "12:30"},
    ]
    assert tarde["rangos"] == [
        {"inicio": "13:00", "fin": "14:00"},
        {"inicio": "15:30", "fin": "18:00"},
    ]


def test_validar_rango_institucional_bloquea_cruce_entre_jornadas():
    assert asignacion_controller.validar_rango_institucional("12:00", "14:00") == (
        "El horario debe estar dentro de una jornada válida: 06:30-12:30 o 13:00-18:00."
    )


def test_asignar_profesor_bloquea_profesor_inactivo(monkeypatch):
    cursor = FakeCursor(fetchone_values=[None])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(asignacion_controller, "get_connection", lambda: conn)

    response = asignacion_controller.asignar_profesor_controller(
        AsignacionCreate(
            profesor_id=3,
            curso_id=2,
            materia_id=5,
            dia="Lunes",
            hora_inicio="08:00",
            hora_fin="09:00",
        )
    )

    assert response == {"error": "No se puede asignar un profesor inactivo."}
    assert conn.commits == 0


def test_asignar_profesor_bloquea_curso_inactivo(monkeypatch):
    cursor = FakeCursor(fetchone_values=[(1,), None])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(asignacion_controller, "get_connection", lambda: conn)

    response = asignacion_controller.asignar_profesor_controller(
        AsignacionCreate(
            profesor_id=3,
            curso_id=2,
            materia_id=5,
            dia="Lunes",
            hora_inicio="08:00",
            hora_fin="09:00",
        )
    )

    assert response == {"error": "No se puede asignar un curso inactivo."}
    assert conn.commits == 0


def test_asignar_profesor_bloquea_materia_inactiva(monkeypatch):
    cursor = FakeCursor(fetchone_values=[(1,), (1,), None])
    conn = FakeConnection(cursor)
    monkeypatch.setattr(asignacion_controller, "get_connection", lambda: conn)

    response = asignacion_controller.asignar_profesor_controller(
        AsignacionCreate(
            profesor_id=3,
            curso_id=2,
            materia_id=5,
            dia="Lunes",
            hora_inicio="08:00",
            hora_fin="09:00",
        )
    )

    assert response == {"error": "No se puede asignar una materia inactiva."}
    assert conn.commits == 0
