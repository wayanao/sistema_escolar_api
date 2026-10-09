"""Fase 6.3a: activar el año en preparación en una sola transacción.

Cierra el activo, activa el siguiente, aplica las marcas de salida, guarda las
materias ocultas del año que se cierra y sincroniza el curso vigente de todos.
Todo usa dobles: no se activa ningún año en una base real.
"""
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.controllers import anios_lectivos_controller as controlador
from app.repositories import anios_lectivos_repository as repositorio
from app.routes import anios_lectivos as rutas
from app.schemas import anio_lectivo as esquemas
from app.services.anio_lectivo import AnioLectivoInexistenteError


class CursorFalso:
    """Registra cada consulta; `rowcounts` y `una` se consumen en orden."""

    def __init__(self, una=(), rowcounts=()):
        self.una = list(una)
        self.rowcounts = list(rowcounts)
        self.consultas = []
        self.rowcount = -1

    def execute(self, sql, params=None):
        self.consultas.append((" ".join(str(sql).split()), params))
        self.rowcount = self.rowcounts.pop(0) if self.rowcounts else -1

    def fetchone(self):
        return self.una.pop(0) if self.una else None


PENDIENTE = {
    "id": 7,
    "nombre": "Ana",
    "apellido": "Pérez",
    "documento_identidad": "1001",
    "curso_id": 20,
    "curso_nombre": "Quinto A",
    "curso_jornada": "Mañana",
}


def _confirmacion(anio=2027):
    return esquemas.ActivarAnioLectivo(confirmar_anio=anio)


# ---------------------------------------------------------------------------
# Cuerpo de la petición
# ---------------------------------------------------------------------------


def test_el_cuerpo_exige_escribir_el_anio():
    with pytest.raises(ValidationError):
        esquemas.ActivarAnioLectivo()


@pytest.mark.parametrize("anio", [1999, 2101, "dos mil"])
def test_el_cuerpo_rechaza_un_anio_imposible(anio):
    with pytest.raises(ValidationError):
        esquemas.ActivarAnioLectivo(confirmar_anio=anio)


# ---------------------------------------------------------------------------
# Controlador
# ---------------------------------------------------------------------------


@pytest.fixture
def entorno_activacion(monkeypatch):
    estado = SimpleNamespace(
        activo=(2, 2026, "activo"),
        destino=(3, 2027, "preparacion"),
        pendientes=[],
        cambios_de_anio=(1, 1),
        desajustes=0,
        eventos=[],
        commits=0,
        rollbacks=0,
    )
    cursor = object()

    @contextmanager
    def get_cursor_falso(commit=False):
        estado.eventos.append(("abre", commit))
        try:
            yield cursor
        except Exception:
            estado.rollbacks += 1
            raise
        else:
            if commit:
                estado.commits += 1

    def registrar(nombre, respuesta):
        def doble(cursor_recibido, *args):
            assert cursor_recibido is cursor
            estado.eventos.append((nombre, *args))
            return respuesta() if callable(respuesta) else respuesta

        return doble

    def no_leer_sin_bloquear(*_args):
        raise AssertionError("la activación debe bloquear los dos años")

    monkeypatch.setattr(controlador, "get_cursor", get_cursor_falso)
    dobles = {
        "leer_anio_activo_para_actualizar": registrar("bloquea_activo", lambda: estado.activo),
        "leer_anio_lectivo_para_actualizar": registrar("bloquea_destino", lambda: estado.destino),
        "leer_anio_activo": no_leer_sin_bloquear,
        "leer_anio_lectivo": no_leer_sin_bloquear,
        "listar_sin_decidir_activacion": registrar("pendientes", lambda: estado.pendientes),
        "contar_decisiones_activacion": registrar(
            "conteos",
            {"continuan": 170, "nuevos": 4, "retirados": 2, "egresados": 18},
        ),
        "guardar_materias_ocultas": registrar("materias_ocultas", 3),
        "aplicar_marcas_de_salida": registrar("marcas", 20),
        "activar_anio_siguiente": registrar("cambia_anios", lambda: estado.cambios_de_anio),
        "sincronizar_curso_vigente_de_todos": registrar("sincroniza_todos", 174),
        "contar_desajustes_curso_vigente": registrar("control", lambda: estado.desajustes),
    }
    for nombre, doble in dobles.items():
        monkeypatch.setattr(
            controlador.anios_lectivos_repository, nombre, doble, raising=False
        )
    return estado


def _escrituras(eventos):
    return [
        evento
        for evento in eventos
        if evento[0] in {"materias_ocultas", "marcas", "cambia_anios", "sincroniza_todos"}
    ]


def test_activa_todo_en_una_transaccion_y_en_orden(entorno_activacion):
    respuesta = controlador.activar_anio_controller(3, _confirmacion())

    assert entorno_activacion.eventos == [
        ("abre", True),
        ("bloquea_activo",),
        ("bloquea_destino", 3),
        ("pendientes", 2, 3),
        ("conteos", 2, 3),
        ("materias_ocultas", 2),
        ("marcas", 2, 3),
        ("cambia_anios", 2, 3),
        ("sincroniza_todos",),
        ("control",),
    ]
    assert entorno_activacion.commits == 1
    assert entorno_activacion.rollbacks == 0
    assert respuesta == {
        "anio_cerrado": {"id": 2, "anio": 2026, "estado": "cerrado"},
        "anio_activo": {"id": 3, "anio": 2027, "estado": "activo"},
        "resumen": {
            "continuan": 170,
            "nuevos": 4,
            "retirados": 2,
            "egresados": 18,
            "materias_ocultas": 3,
            "cursos_vigentes_actualizados": 174,
        },
    }


def test_no_activa_si_el_anio_escrito_no_coincide(entorno_activacion):
    with pytest.raises(
        controlador.ConfirmacionAnioInvalidaError,
        match="escribe el año 2027",
    ):
        controlador.activar_anio_controller(3, _confirmacion(2026))

    assert _escrituras(entorno_activacion.eventos) == []
    assert not any(evento[0] == "pendientes" for evento in entorno_activacion.eventos)
    assert entorno_activacion.rollbacks == 1


def test_no_activa_con_pendientes_y_entrega_la_lista(entorno_activacion):
    entorno_activacion.pendientes = [PENDIENTE]

    with pytest.raises(controlador.ActivacionConPendientesError) as capturado:
        controlador.activar_anio_controller(3, _confirmacion())

    assert "faltan 1 estudiantes por decidir" in str(capturado.value)
    assert capturado.value.codigo == "activacion_con_pendientes"
    assert capturado.value.sin_decidir == [PENDIENTE]
    assert _escrituras(entorno_activacion.eventos) == []
    assert entorno_activacion.rollbacks == 1


@pytest.mark.parametrize(
    ("destino", "error"),
    [
        (None, AnioLectivoInexistenteError),
        ((3, 2027, "activo"), controlador.AnioLectivoDestinoInvalidoError),
        ((4, 2028, "preparacion"), controlador.AnioLectivoDestinoInvalidoError),
    ],
)
def test_no_activa_lo_que_no_es_el_siguiente_en_preparacion(
    entorno_activacion, destino, error
):
    entorno_activacion.destino = destino

    with pytest.raises(error):
        controlador.activar_anio_controller(3, _confirmacion())

    assert _escrituras(entorno_activacion.eventos) == []
    assert entorno_activacion.rollbacks == 1


def test_sin_anio_activo_no_activa(entorno_activacion):
    entorno_activacion.activo = None

    with pytest.raises(controlador.AnioLectivoActivoInexistenteError):
        controlador.activar_anio_controller(3, _confirmacion())

    assert _escrituras(entorno_activacion.eventos) == []


@pytest.mark.parametrize("cambios", [(0, 1), (1, 0)])
def test_si_un_anio_no_cambio_de_estado_se_deshace_todo(entorno_activacion, cambios):
    entorno_activacion.cambios_de_anio = cambios

    with pytest.raises(controlador.ActivacionInconsistenteError, match="Nada cambió"):
        controlador.activar_anio_controller(3, _confirmacion())

    assert not any(e[0] == "sincroniza_todos" for e in entorno_activacion.eventos)
    assert entorno_activacion.commits == 0
    assert entorno_activacion.rollbacks == 1


def test_si_la_consulta_de_control_no_da_cero_se_deshace_todo(entorno_activacion):
    entorno_activacion.desajustes = 2

    with pytest.raises(controlador.ActivacionInconsistenteError, match="Nada cambió"):
        controlador.activar_anio_controller(3, _confirmacion())

    assert entorno_activacion.commits == 0
    assert entorno_activacion.rollbacks == 1


# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------


def test_guarda_como_ocultas_las_materias_inactivas_del_anio_que_cierra():
    cursor = CursorFalso(rowcounts=[3])

    guardadas = repositorio.guardar_materias_ocultas(cursor, 2)

    assert guardadas == 3
    sql, params = cursor.consultas[0]
    assert params == (2,)
    assert sql.startswith(
        "INSERT INTO anios_lectivos_materias_ocultas (anio_lectivo_id, materia_id)"
    )
    # El complemento exacto del filtro del boletín.
    assert "WHERE COALESCE(LOWER(m.estado), 'activo') <> 'activo'" in sql
    assert sql.endswith("ON CONFLICT DO NOTHING")


def test_las_marcas_cambian_el_estado_solo_de_quien_no_sigue():
    cursor = CursorFalso(rowcounts=[20])

    cambiados = repositorio.aplicar_marcas_de_salida(cursor, 2, 3)

    assert cambiados == 20
    sql, params = cursor.consultas[0]
    assert params == (2, 3)
    assert sql.startswith("UPDATE estudiantes e SET estado = m.estado_salida")
    assert "m.anio_lectivo_id = %s" in sql
    assert "m.estado_salida IS NOT NULL" in sql
    assert "NOT EXISTS" in sql
    assert "d.anio_lectivo_id = %s" in sql
    assert "e.estado IS DISTINCT FROM m.estado_salida" in sql
    # Quien vuelve con matrícula siguiente conserva su estado (decisión del
    # usuario del 2026-10-08) y el curso vigente no se escribe aquí.
    assert "curso_id" not in sql.split("SET", 1)[1].split("FROM", 1)[0]


def test_cierra_el_activo_antes_de_activar_el_siguiente():
    cursor = CursorFalso(rowcounts=[1, 1])

    cambios = repositorio.activar_anio_siguiente(cursor, 2, 3)

    assert cambios == (1, 1)
    (cierre, params_cierre), (activacion, params_activacion) = cursor.consultas
    assert cierre == (
        "UPDATE anios_lectivos SET estado = 'cerrado', cerrado_en = CURRENT_TIMESTAMP "
        "WHERE id = %s AND estado = 'activo'"
    )
    assert params_cierre == (2,)
    assert activacion == (
        "UPDATE anios_lectivos SET estado = 'activo', activado_en = CURRENT_TIMESTAMP "
        "WHERE id = %s AND estado = 'preparacion'"
    )
    assert params_activacion == (3,)


def test_sincronizar_todos_usa_la_misma_regla_que_uno_solo():
    uno = CursorFalso(rowcounts=[1])
    todos = CursorFalso(rowcounts=[174])

    repositorio.sincronizar_curso_vigente(uno, 55)
    actualizados = repositorio.sincronizar_curso_vigente_de_todos(todos)

    sql_uno, params_uno = uno.consultas[0]
    sql_todos, params_todos = todos.consultas[0]
    assert actualizados == 174
    assert params_uno == (55,)
    assert params_todos is None
    assert "WHERE e.id = %s" in sql_uno
    assert "%s" not in sql_todos
    assert sql_todos == sql_uno.replace(" WHERE e.id = %s", "")
    assert "UPDATE estudiantes e SET curso_id = cv.curso_id" in sql_todos
    assert "e.curso_id IS DISTINCT FROM cv.curso_id" in sql_todos


@pytest.mark.parametrize("fila", [(0,), {"desajustes": 0}])
def test_la_consulta_de_control_cuenta_desajustes(fila):
    cursor = CursorFalso(una=[fila])

    assert repositorio.contar_desajustes_curso_vigente(cursor) == 0

    sql, params = cursor.consultas[0]
    assert params is None
    assert "FROM estudiantes e LEFT JOIN matriculas m" in sql
    assert "(SELECT id FROM anios_lectivos WHERE estado = 'activo')" in sql
    assert sql.endswith("WHERE e.curso_id IS DISTINCT FROM m.curso_id")


# ---------------------------------------------------------------------------
# Ruta
# ---------------------------------------------------------------------------


def _ruta_activar():
    return next(
        ruta
        for ruta in rutas.router.routes
        if ruta.path == "/anios-lectivos/{anio_lectivo_id}/activar"
    )


def test_la_ruta_de_activar_es_post_y_solo_admin():
    from app.dependencies import get_current_active_admin

    ruta = _ruta_activar()

    assert ruta.methods == {"POST"}
    assert get_current_active_admin in [
        dependencia.call for dependencia in ruta.dependant.dependencies
    ]


def test_la_ruta_responde_los_pendientes_con_codigo_y_lista(monkeypatch):
    def rechazar(*_args):
        raise controlador.ActivacionConPendientesError(
            "No se puede activar 2027: faltan 1 estudiantes por decidir.",
            [PENDIENTE],
        )

    monkeypatch.setattr(rutas, "activar_anio_controller", rechazar)

    with pytest.raises(HTTPException) as capturado:
        rutas.activar_anio_lectivo(3, _confirmacion())

    assert capturado.value.status_code == 409
    assert capturado.value.detail == {
        "codigo": "activacion_con_pendientes",
        "mensaje": "No se puede activar 2027: faltan 1 estudiantes por decidir.",
        "sin_decidir": [PENDIENTE],
    }


@pytest.mark.parametrize(
    ("error", "codigo"),
    [
        (AnioLectivoInexistenteError("El año lectivo seleccionado no existe."), 404),
        (controlador.AnioLectivoActivoInexistenteError("Sin activo."), 409),
        (controlador.AnioLectivoDestinoInvalidoError("No es el siguiente."), 409),
        (controlador.ConfirmacionAnioInvalidaError("Escribe 2027."), 409),
        (controlador.ActivacionInconsistenteError("Nada cambió."), 409),
    ],
)
def test_la_ruta_traduce_los_demas_errores(monkeypatch, error, codigo):
    def rechazar(*_args):
        raise error

    monkeypatch.setattr(rutas, "activar_anio_controller", rechazar)

    with pytest.raises(HTTPException) as capturado:
        rutas.activar_anio_lectivo(3, _confirmacion())

    assert capturado.value.status_code == codigo
    assert capturado.value.detail == str(error)
