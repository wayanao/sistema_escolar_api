"""Año lectivo, fase 5.1: la matrícula manda sobre el curso vigente.

El formulario existente conserva su cuerpo y su respuesta, pero ya no puede
escribir ``estudiantes.curso_id`` directamente. Primero guarda la matrícula
del año activo y después ``sincronizar_curso_vigente`` actualiza esa copia.
"""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.controllers import estudiante_controller
from app.repositories import anios_lectivos_repository
from app.routes import estudiantes as rutas_estudiantes


class CursorEspia:
    def __init__(self, filas=None):
        self.ejecutadas = []
        self._filas = list(filas or [])

    def execute(self, query, params=None):
        self.ejecutadas.append((query, params))

    def fetchone(self):
        return self._filas.pop(0) if self._filas else None


def _normalizado(query):
    return " ".join(query.split())


def _estudiante(curso_id=4):
    campos = {
        "nombre": "Ana",
        "apellido": "Ríos",
        "documento_identidad": "123",
        "fecha_nacimiento": None,
        "curso_id": curso_id,
        "estado": "activo",
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


def test_matricular_en_el_activo_valida_el_curso_y_hace_upsert():
    cursor = CursorEspia(filas=[(4,)])

    resultado = anios_lectivos_repository.matricular_en_curso_del_anio_activo(
        cursor, estudiante_id=55, curso_id=4
    )

    assert resultado is True
    query, params = cursor.ejecutadas[0]
    sql = _normalizado(query)
    assert params == (55, 4)
    assert sql.startswith(
        "INSERT INTO matriculas (estudiante_id, curso_id, anio_lectivo_id)"
    )
    assert "JOIN anios_lectivos al ON al.id = c.anio_lectivo_id" in sql
    assert "al.estado = 'activo'" in sql
    assert (
        "ON CONFLICT (estudiante_id, anio_lectivo_id) "
        "DO UPDATE SET curso_id = EXCLUDED.curso_id"
    ) in sql
    assert "RETURNING matriculas.curso_id" in sql


def test_matricular_rechaza_un_curso_que_no_es_del_activo():
    cursor = CursorEspia()

    resultado = anios_lectivos_repository.matricular_en_curso_del_anio_activo(
        cursor, estudiante_id=55, curso_id=99
    )

    assert resultado is False


def test_sincronizar_curso_vigente_copia_la_matricula_activa_o_null():
    cursor = CursorEspia()

    anios_lectivos_repository.sincronizar_curso_vigente(cursor, 55)

    assert len(cursor.ejecutadas) == 1
    query, params = cursor.ejecutadas[0]
    sql = _normalizado(query)
    assert params == (55,)
    assert sql.startswith("WITH curso_vigente AS")
    assert "LEFT JOIN matriculas m" in sql
    assert "al.estado = 'activo'" in sql
    assert "UPDATE estudiantes e SET curso_id = cv.curso_id" in sql
    assert "e.curso_id IS DISTINCT FROM cv.curso_id" in sql


@pytest.fixture
def flujo_espiado(monkeypatch):
    eventos = []
    cursor = object()
    resultado_actualizar = {"fila": (55,)}
    matricula_guardada = {"valor": True}

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        eventos.append(("abre", commit))
        yield cursor
        eventos.append(("cierra",))

    def insertar(cursor_recibido, valores):
        eventos.append(("inserta", cursor_recibido is cursor, valores))
        return 55

    def actualizar(cursor_recibido, valores):
        eventos.append(("actualiza", cursor_recibido is cursor, valores))
        return resultado_actualizar["fila"]

    def matricular(cursor_recibido, estudiante_id, curso_id):
        eventos.append(
            ("matricula", cursor_recibido is cursor, estudiante_id, curso_id)
        )
        return matricula_guardada["valor"]

    def sincronizar(cursor_recibido, estudiante_id):
        eventos.append(("sincroniza", cursor_recibido is cursor, estudiante_id))

    def sincronizar_legacy(cursor_recibido, estudiante_id):
        eventos.append(("sincroniza_legacy", cursor_recibido is cursor, estudiante_id))

    monkeypatch.setattr(estudiante_controller, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(
        estudiante_controller.estudiantes_repository, "insertar_estudiante", insertar
    )
    monkeypatch.setattr(
        estudiante_controller.estudiantes_repository, "actualizar_estudiante", actualizar
    )
    monkeypatch.setattr(
        estudiante_controller.anios_lectivos_repository,
        "matricular_en_curso_del_anio_activo",
        matricular,
        raising=False,
    )
    monkeypatch.setattr(
        estudiante_controller.anios_lectivos_repository,
        "sincronizar_curso_vigente",
        sincronizar,
        raising=False,
    )
    monkeypatch.setattr(
        estudiante_controller.anios_lectivos_repository,
        "sincronizar_matricula_del_anio_activo",
        sincronizar_legacy,
        raising=False,
    )
    return SimpleNamespace(
        eventos=eventos,
        resultado_actualizar=resultado_actualizar,
        matricula_guardada=matricula_guardada,
    )


def test_crear_guarda_matricula_y_despues_sincroniza_el_curso(flujo_espiado):
    respuesta = estudiante_controller.crear_estudiante_controller(_estudiante())

    assert respuesta == {"mensaje": "Estudiante creado correctamente", "id": 55}
    assert [evento[0] for evento in flujo_espiado.eventos] == [
        "abre", "inserta", "matricula", "sincroniza", "cierra"
    ]
    assert flujo_espiado.eventos[2] == ("matricula", True, 55, 4)
    # El curso solo viaja a la matrícula; no forma parte del INSERT del alumno.
    assert 4 not in flujo_espiado.eventos[1][2]


def test_editar_guarda_matricula_y_despues_sincroniza_el_curso(flujo_espiado):
    respuesta = estudiante_controller.actualizar_estudiante_controller(
        55, _estudiante(curso_id=7)
    )

    assert respuesta == {"mensaje": "Estudiante actualizado correctamente", "id": 55}
    assert [evento[0] for evento in flujo_espiado.eventos] == [
        "abre", "actualiza", "matricula", "sincroniza", "cierra"
    ]
    assert flujo_espiado.eventos[2] == ("matricula", True, 55, 7)
    # El ultimo valor es el id del estudiante; el curso no va al UPDATE global.
    valores = flujo_espiado.eventos[1][2]
    assert valores[-1] == 55
    assert 7 not in valores[:-1]


@pytest.mark.parametrize("accion", ["crear", "editar"])
def test_un_curso_fuera_del_activo_revierte_el_flujo(accion, flujo_espiado):
    error = getattr(estudiante_controller, "CursoNoPerteneceAlAnioActivoError", None)
    assert error is not None
    flujo_espiado.matricula_guardada["valor"] = False

    with pytest.raises(error, match="año lectivo activo"):
        if accion == "crear":
            estudiante_controller.crear_estudiante_controller(_estudiante(curso_id=99))
        else:
            estudiante_controller.actualizar_estudiante_controller(
                55, _estudiante(curso_id=99)
            )

    nombres = [evento[0] for evento in flujo_espiado.eventos]
    assert "sincroniza" not in nombres
    assert "sincroniza_legacy" not in nombres


def test_las_rutas_traducen_el_curso_fuera_del_activo_a_409(monkeypatch):
    error = getattr(estudiante_controller, "CursoNoPerteneceAlAnioActivoError", None)
    assert error is not None

    def rechazar(*_args, **_kwargs):
        raise error("El curso seleccionado debe pertenecer al año lectivo activo.")

    monkeypatch.setattr(rutas_estudiantes, "crear_estudiante_controller", rechazar)
    monkeypatch.setattr(rutas_estudiantes, "actualizar_estudiante_controller", rechazar)

    with pytest.raises(HTTPException) as crear:
        rutas_estudiantes.crear_estudiante(_estudiante())
    with pytest.raises(HTTPException) as editar:
        rutas_estudiantes.actualizar_estudiante(55, _estudiante())

    assert crear.value.status_code == 409
    assert editar.value.status_code == 409
    assert crear.value.detail == editar.value.detail

