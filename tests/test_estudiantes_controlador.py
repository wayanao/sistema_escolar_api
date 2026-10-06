"""Caracterizacion de crear y actualizar estudiante, migradas en la subcapa 1.4m.

Eran los dos ultimos sitios desprotegidos del programa.

Desde la fase 5.1 del año lectivo, las dos escriben 34 datos globales. El curso
se guarda en `matriculas` y luego se copia desde el año activo. Se fija el orden
completo: un desplazamiento silencioso guardaria el telefono del padre en el
campo de la madre sin lanzar ningun error.

Tambien se fija la regla de estado al actualizar: la consulta usa
COALESCE(%s, estado, 'activo'), de modo que enviar None CONSERVA el estado
actual en vez de sobrescribirlo.
"""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app.controllers import estudiante_controller

CAMPOS = [
    "nombre", "apellido", "documento_identidad", "fecha_nacimiento", "curso_id",
    "descuento_matricula", "descuento_mensualidad", "datos_medicos", "telefono",
    "email", "direccion", "nombre_padre", "telefono_padre", "nombre_madre",
    "telefono_madre", "contacto_emergencia", "tipo_documento", "lugar_expedicion",
    "eps", "estrato", "jornada", "colegio_anterior", "anio_cursado_anterior",
    "pre_escolar_anterior", "ebp_anterior", "motivo_retiro_anterior",
    "paz_salvo_anterior", "ocupacion_padre", "tipo_documento_padre",
    "documento_padre", "ocupacion_madre", "tipo_documento_madre",
    "documento_madre", "condicion_diagnostico",
]
CAMPOS_GLOBALES = [campo for campo in CAMPOS if campo != "curso_id"]


def _estudiante(**overrides):
    """Cada campo lleva su propio nombre como valor, para detectar desplazamientos."""
    datos = {campo: campo for campo in CAMPOS}
    datos.update(overrides)
    return SimpleNamespace(**datos)


class CursorFalso:
    def __init__(self, fila=None):
        self.fila = fila
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.fila


@pytest.fixture
def cursor_de(monkeypatch):
    def instalar(fila=None):
        cursor = CursorFalso(fila=fila)
        commits = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        monkeypatch.setattr(estudiante_controller, "get_cursor", fake_get_cursor)
        return cursor, commits

    return instalar


def test_crear_estudiante_inserta_los_34_datos_globales_en_orden(cursor_de):
    cursor, commits = cursor_de(fila=(55,))

    respuesta = estudiante_controller.crear_estudiante_controller(
        _estudiante(estado="activo")
    )

    query, params = cursor.calls[0]
    assert "INSERT INTO estudiantes" in query
    assert "RETURNING id" in query
    assert "curso_id" not in query
    assert len(params) == 34
    assert list(params[:33]) == CAMPOS_GLOBALES
    assert params[33] == "activo"
    assert commits == [True]
    assert respuesta == {"mensaje": "Estudiante creado correctamente", "id": 55}


def test_crear_estudiante_normaliza_el_estado(cursor_de):
    cursor, _ = cursor_de(fila=(55,))

    estudiante_controller.crear_estudiante_controller(_estudiante(estado="  ACTIVO  "))

    _, params = cursor.calls[0]
    assert params[33] == "activo"


def test_actualizar_estudiante_envia_los_34_datos_globales_y_el_id(cursor_de):
    cursor, commits = cursor_de(fila=(55,))

    respuesta = estudiante_controller.actualizar_estudiante_controller(
        55, _estudiante(estado="inactivo")
    )

    query, params = cursor.calls[0]
    assert "UPDATE estudiantes" in query
    assert "RETURNING id" in query
    assert "curso_id" not in query
    assert len(params) == 35
    assert list(params[:33]) == CAMPOS_GLOBALES
    assert params[33] == "inactivo"
    assert params[34] == 55
    assert commits == [True]
    assert respuesta == {"mensaje": "Estudiante actualizado correctamente", "id": 55}


def test_actualizar_sin_estado_conserva_el_actual(cursor_de):
    cursor, _ = cursor_de(fila=(55,))

    estudiante_controller.actualizar_estudiante_controller(55, _estudiante(estado=None))

    query, params = cursor.calls[0]
    # El None viaja hasta el COALESCE, que se queda con el estado ya guardado.
    assert "estado = COALESCE(%s, estado, 'activo')" in query
    assert params[33] is None


def test_actualizar_estudiante_inexistente_avisa_sin_id(cursor_de):
    cursor, commits = cursor_de(fila=None)

    respuesta = estudiante_controller.actualizar_estudiante_controller(
        999, _estudiante(estado="activo")
    )

    assert respuesta == {"mensaje": "Estudiante no encontrado"}
    # La version anterior confirmaba igual en este camino; se conserva.
    assert commits == [True]
