"""Fase 1 del año lectivo: toda fila nueva nace con su año.

Ver docs/funcionalidades/ANIO_LECTIVO.md, fase 1, punto 2. Cursos, conceptos
de pago, pagos y anotaciones del observador escriben el año activo dentro del
mismo INSERT (sin una consulta mas ni un parametro mas), y crear o editar un
estudiante deja su matricula del año activo igual a su curso, en la misma
transaccion. Los dos INSERT de pagos los fijan sus propias pruebas
(`test_pagos_adelantados.py`, `test_pagos_escrituras_caracterizacion.py`) y la
siembra del alta de colegios, `test_super_admin_caracterizacion.py`.
"""
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app.controllers import curso_controller, estudiante_controller, tipos_pagos_controller
from app.repositories import anios_lectivos_repository, observador_repository
from app.repositories.anios_lectivos_repository import ANIO_ACTIVO_ID_SQL


SUBCONSULTA = "(SELECT id FROM anios_lectivos WHERE estado = 'activo')"


class CursorEspia:
    def __init__(self, una=None):
        self.ejecutadas = []
        self._una = list(una or [])

    def execute(self, query, params=None):
        self.ejecutadas.append((query, params))

    def fetchone(self):
        return self._una.pop(0) if self._una else None

    def close(self):
        pass


class ConexionEspia:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0

    def cursor(self, *args, **kwargs):
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass

    def close(self):
        pass


def _normalizado(query):
    return " ".join(query.split())


# ---------------------------------------------------------------------------
# El repositorio
# ---------------------------------------------------------------------------


def test_el_año_activo_es_una_subconsulta_por_estado():
    assert ANIO_ACTIVO_ID_SQL == SUBCONSULTA


def test_sincronizar_crea_o_corrige_la_matricula_del_año_activo():
    cursor = CursorEspia()

    anios_lectivos_repository.sincronizar_matricula_del_anio_activo(cursor, 55)

    assert len(cursor.ejecutadas) == 1
    query, params = cursor.ejecutadas[0]
    sql = _normalizado(query)
    assert params == (55,)
    assert sql.startswith("INSERT INTO matriculas (estudiante_id, curso_id, anio_lectivo_id)")
    # El año sale del curso, como en la migracion A: coincide siempre con la
    # clave foranea compuesta (curso_id, anio_lectivo_id).
    assert "SELECT e.id, e.curso_id, c.anio_lectivo_id FROM estudiantes e" in sql
    assert "JOIN cursos c ON c.id = e.curso_id" in sql
    assert "AND al.estado = 'activo'" in sql
    assert "ON CONFLICT (estudiante_id, anio_lectivo_id) DO UPDATE SET curso_id = EXCLUDED.curso_id" in sql
    assert "DELETE" not in sql.upper()


def test_el_alta_siembra_el_año_como_activo():
    cursor = CursorEspia()

    anios_lectivos_repository.crear_anio_activo_inicial(cursor, 2027)

    query, params = cursor.ejecutadas[0]
    assert "INSERT INTO anios_lectivos (anio, estado, activado_en)" in _normalizado(query)
    assert "VALUES (%s, 'activo', CURRENT_TIMESTAMP)" in _normalizado(query)
    assert params == (2027,)


def test_el_repositorio_no_administra_recursos():
    from pathlib import Path

    fuente = Path(anios_lectivos_repository.__file__).read_text(encoding="utf-8")
    for prohibido in ("get_connection", "get_cursor", "commit()", "rollback()", "close()"):
        assert prohibido not in fuente


# ---------------------------------------------------------------------------
# Cada fila nueva nace en el año activo, sin parametro nuevo
# ---------------------------------------------------------------------------


def test_un_curso_nuevo_nace_en_el_año_activo(monkeypatch):
    cursor = CursorEspia(una=[None, (21,)])
    monkeypatch.setattr(curso_controller, "get_connection", lambda: ConexionEspia(cursor))

    curso_id = curso_controller.crear_curso_controller(
        SimpleNamespace(
            nombre="Primero A", jornada="Mañana", estado="activo",
            nivel="primaria", director_grupo_id=None,
        )
    )

    assert curso_id == 21
    query, params = next(q for q in cursor.ejecutadas if "INSERT INTO cursos" in q[0])
    assert (
        "INSERT INTO cursos (nombre, jornada, estado, nivel, director_grupo_id, anio_lectivo_id)"
        in _normalizado(query)
    )
    assert SUBCONSULTA in query
    assert params == ("PRIMERO A", "Mañana", "activo", "primaria", None)


def test_un_concepto_nuevo_nace_en_el_año_activo(monkeypatch):
    cursor = CursorEspia(una=[None, (8,)])
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: ConexionEspia(cursor))

    respuesta = tipos_pagos_controller.crear_tipo_pago("PENSION", 200000)

    assert respuesta == {"id": 8, "nombre": "PENSION", "valor": 200000}
    query, params = next(q for q in cursor.ejecutadas if "INSERT INTO tipos_de_pagos" in q[0])
    assert "INSERT INTO tipos_de_pagos (nombre, valor, anio_lectivo_id)" in query
    assert SUBCONSULTA in query
    assert params == ("PENSION", 200000)


def test_una_anotacion_nueva_nace_en_el_año_activo():
    cursor = CursorEspia(una=[(301,)])

    anotacion_id = observador_repository.crear_anotacion(
        cursor, 55, 9, 2, "Conducta", "Cognitivo", "Lenguaje",
    )

    assert anotacion_id == 301
    query, params = cursor.ejecutadas[0]
    sql = _normalizado(query)
    assert (
        "estudiante_id, profesor_id, periodo, conductual, cognitivo, lenguaje, anio_lectivo_id"
        in sql
    )
    assert SUBCONSULTA in sql
    assert params == (55, 9, 2, "Conducta", "Cognitivo", "Lenguaje")


# ---------------------------------------------------------------------------
# Estudiantes: la matricula del año activo sigue al curso
# ---------------------------------------------------------------------------


@pytest.fixture
def estudiante_espiado(monkeypatch):
    """Dobla el cursor y los dos repositorios; anota el orden de las llamadas.

    `resultado_actualizar` es lo que devuelve el UPDATE: una fila si el
    estudiante existe, `None` si no.
    """
    espia = SimpleNamespace(eventos=[], resultado_actualizar=(55,))
    cursor = object()

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        espia.eventos.append(("abre", commit))
        yield cursor
        espia.eventos.append(("cierra",))

    def insertar(cursor_recibido, valores):
        espia.eventos.append(("inserta", cursor_recibido is cursor))
        return 55

    def actualizar(cursor_recibido, valores):
        espia.eventos.append(("actualiza", cursor_recibido is cursor))
        return espia.resultado_actualizar

    def sincronizar(cursor_recibido, estudiante_id):
        espia.eventos.append(("sincroniza", cursor_recibido is cursor, estudiante_id))

    monkeypatch.setattr(estudiante_controller, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(estudiante_controller.estudiantes_repository, "insertar_estudiante", insertar)
    monkeypatch.setattr(estudiante_controller.estudiantes_repository, "actualizar_estudiante", actualizar)
    monkeypatch.setattr(
        estudiante_controller.anios_lectivos_repository,
        "sincronizar_matricula_del_anio_activo",
        sincronizar,
    )
    return espia


def _estudiante():
    campos = {
        "nombre": "Ana", "apellido": "Rios", "documento_identidad": "123",
        "fecha_nacimiento": None, "curso_id": 4, "estado": "activo",
    }
    return SimpleNamespace(**campos, **{
        nombre: None
        for nombre in (
            "descuento_matricula", "descuento_mensualidad", "datos_medicos",
            "telefono", "email", "direccion", "nombre_padre", "telefono_padre",
            "nombre_madre", "telefono_madre", "contacto_emergencia",
            "tipo_documento", "lugar_expedicion", "eps", "estrato", "jornada",
            "colegio_anterior", "anio_cursado_anterior", "pre_escolar_anterior",
            "ebp_anterior", "motivo_retiro_anterior", "paz_salvo_anterior",
            "ocupacion_padre", "tipo_documento_padre", "documento_padre",
            "ocupacion_madre", "tipo_documento_madre", "documento_madre",
            "condicion_diagnostico",
        )
    })


def test_crear_estudiante_sincroniza_su_matricula_en_la_misma_transaccion(estudiante_espiado):
    respuesta = estudiante_controller.crear_estudiante_controller(_estudiante())

    assert respuesta == {"mensaje": "Estudiante creado correctamente", "id": 55}
    assert estudiante_espiado.eventos == [
        ("abre", True),
        ("inserta", True),
        ("sincroniza", True, 55),
        ("cierra",),
    ]


def test_editar_estudiante_sincroniza_su_matricula_en_la_misma_transaccion(estudiante_espiado):
    respuesta = estudiante_controller.actualizar_estudiante_controller(55, _estudiante())

    assert respuesta == {"mensaje": "Estudiante actualizado correctamente", "id": 55}
    assert estudiante_espiado.eventos == [
        ("abre", True),
        ("actualiza", True),
        ("sincroniza", True, 55),
        ("cierra",),
    ]


def test_editar_un_estudiante_inexistente_no_sincroniza_nada(estudiante_espiado):
    estudiante_espiado.resultado_actualizar = None

    respuesta = estudiante_controller.actualizar_estudiante_controller(99, _estudiante())

    assert respuesta == {"mensaje": "Estudiante no encontrado"}
    assert estudiante_espiado.eventos == [
        ("abre", True),
        ("actualiza", True),
        ("cierra",),
    ]
