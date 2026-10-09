"""Fase 6.4a: reabrir un año cerrado y volver a cerrarlo.

Solo cambia el estado del año (`cerrado` <-> `reabierto`), solo admin, con el
año escrito como confirmación y un solo año reabierto a la vez. No toca
estudiantes, cursos, la foto de materias ni las fechas. Todo usa dobles.
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


def _confirmacion(anio=2026):
    return esquemas.ConfirmacionAnioLectivo(confirmar_anio=anio)


def test_la_confirmacion_es_obligatoria_y_razonable():
    with pytest.raises(ValidationError):
        esquemas.ConfirmacionAnioLectivo()
    with pytest.raises(ValidationError):
        esquemas.ConfirmacionAnioLectivo(confirmar_anio=1999)


def test_activar_sigue_pidiendo_la_misma_confirmacion():
    assert issubclass(esquemas.ActivarAnioLectivo, esquemas.ConfirmacionAnioLectivo)
    assert esquemas.ActivarAnioLectivo(confirmar_anio=2027).confirmar_anio == 2027


# ---------------------------------------------------------------------------
# Controlador
# ---------------------------------------------------------------------------


@pytest.fixture
def entorno(monkeypatch):
    estado = SimpleNamespace(
        activo=(2, 2027, "activo"),
        anio=(1, 2026, "cerrado"),
        otro_reabierto=None,
        cambiadas=1,
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
            return respuesta()

        return doble

    monkeypatch.setattr(controlador, "get_cursor", get_cursor_falso)
    dobles = {
        "leer_anio_activo_para_actualizar": registrar("bloquea_activo", lambda: estado.activo),
        "leer_anio_lectivo_para_actualizar": registrar("bloquea_anio", lambda: estado.anio),
        "leer_anio_reabierto": registrar("busca_reabierto", lambda: estado.otro_reabierto),
        "cambiar_estado_anio": registrar("cambia", lambda: estado.cambiadas),
    }
    for nombre, doble in dobles.items():
        monkeypatch.setattr(
            controlador.anios_lectivos_repository, nombre, doble, raising=False
        )
    return estado


def _cambios(eventos):
    return [evento for evento in eventos if evento[0] == "cambia"]


def test_reabre_un_anio_cerrado(entorno):
    respuesta = controlador.reabrir_anio_controller(1, _confirmacion())

    assert entorno.eventos == [
        ("abre", True),
        ("bloquea_activo",),
        ("bloquea_anio", 1),
        ("busca_reabierto",),
        ("cambia", 1, "cerrado", "reabierto"),
    ]
    assert respuesta == {"anio_lectivo": {"id": 1, "anio": 2026, "estado": "reabierto"}}
    assert entorno.commits == 1


def test_vuelve_a_cerrar_un_anio_reabierto(entorno):
    entorno.anio = (1, 2026, "reabierto")

    respuesta = controlador.cerrar_anio_reabierto_controller(1, _confirmacion())

    assert entorno.eventos == [
        ("abre", True),
        ("bloquea_activo",),
        ("bloquea_anio", 1),
        ("cambia", 1, "reabierto", "cerrado"),
    ]
    assert respuesta == {"anio_lectivo": {"id": 1, "anio": 2026, "estado": "cerrado"}}
    assert entorno.commits == 1


@pytest.mark.parametrize("estado_actual", ["activo", "preparacion", "reabierto"])
def test_solo_se_reabre_un_anio_cerrado(entorno, estado_actual):
    entorno.anio = (1, 2026, estado_actual)

    with pytest.raises(
        controlador.AnioLectivoDestinoInvalidoError,
        match="Solo se puede reabrir un año cerrado.",
    ):
        controlador.reabrir_anio_controller(1, _confirmacion())

    assert _cambios(entorno.eventos) == []
    assert entorno.rollbacks == 1


@pytest.mark.parametrize("estado_actual", ["activo", "preparacion", "cerrado"])
def test_solo_se_vuelve_a_cerrar_un_anio_reabierto(entorno, estado_actual):
    entorno.anio = (1, 2026, estado_actual)

    with pytest.raises(
        controlador.AnioLectivoDestinoInvalidoError,
        match="Solo se puede volver a cerrar un año reabierto.",
    ):
        controlador.cerrar_anio_reabierto_controller(1, _confirmacion())

    assert _cambios(entorno.eventos) == []


@pytest.mark.parametrize(
    ("funcion", "estado_actual", "mensaje"),
    [
        ("reabrir_anio_controller", "cerrado", "Para reabrir, escribe el año 2026."),
        ("cerrar_anio_reabierto_controller", "reabierto", "Para cerrar, escribe el año 2026."),
    ],
)
def test_el_anio_escrito_debe_coincidir(entorno, funcion, estado_actual, mensaje):
    entorno.anio = (1, 2026, estado_actual)

    with pytest.raises(controlador.ConfirmacionAnioInvalidaError, match=mensaje):
        getattr(controlador, funcion)(1, _confirmacion(2027))

    assert _cambios(entorno.eventos) == []
    assert entorno.rollbacks == 1


def test_solo_un_anio_reabierto_a_la_vez(entorno):
    entorno.otro_reabierto = (5, 2025, "reabierto")

    with pytest.raises(
        controlador.AnioLectivoReabiertoExistenteError,
        match="Ya está reabierto el año 2025. Ciérralo antes de reabrir otro.",
    ):
        controlador.reabrir_anio_controller(1, _confirmacion())

    assert _cambios(entorno.eventos) == []
    assert entorno.rollbacks == 1


@pytest.mark.parametrize("funcion", ["reabrir_anio_controller", "cerrar_anio_reabierto_controller"])
def test_un_anio_inexistente_no_cambia_nada(entorno, funcion):
    entorno.anio = None

    with pytest.raises(AnioLectivoInexistenteError):
        getattr(controlador, funcion)(1, _confirmacion())

    assert _cambios(entorno.eventos) == []


def test_si_el_estado_no_cambio_se_deshace(entorno):
    entorno.cambiadas = 0

    with pytest.raises(controlador.AnioLectivoDestinoInvalidoError, match="Nada cambió"):
        controlador.reabrir_anio_controller(1, _confirmacion())

    assert entorno.commits == 0
    assert entorno.rollbacks == 1


# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------


def test_cambiar_estado_solo_toca_el_estado_del_anio():
    cursor = CursorFalso(rowcounts=[1])

    cambiadas = repositorio.cambiar_estado_anio(cursor, 1, "cerrado", "reabierto")

    assert cambiadas == 1
    [(sql, params)] = cursor.consultas
    assert sql == "UPDATE anios_lectivos SET estado = %s WHERE id = %s AND estado = %s"
    assert params == ("reabierto", 1, "cerrado")


def test_leer_el_anio_reabierto():
    cursor = CursorFalso(una=[(5, 2025, "reabierto")])

    assert repositorio.leer_anio_reabierto(cursor) == (5, 2025, "reabierto")
    [(sql, params)] = cursor.consultas
    assert sql == "SELECT id, anio, estado FROM anios_lectivos WHERE estado = 'reabierto'"
    assert params is None


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------


RUTAS = {
    "/anios-lectivos/{anio_lectivo_id}/reabrir": ("reabrir_anio_lectivo", "reabrir_anio_controller"),
    "/anios-lectivos/{anio_lectivo_id}/cerrar": (
        "cerrar_anio_lectivo",
        "cerrar_anio_reabierto_controller",
    ),
}


@pytest.mark.parametrize("path", sorted(RUTAS))
def test_las_rutas_son_post_y_solo_admin(path):
    from app.dependencies import get_current_active_admin

    ruta = next(ruta for ruta in rutas.router.routes if ruta.path == path)

    assert ruta.methods == {"POST"}
    assert get_current_active_admin in [
        dependencia.call for dependencia in ruta.dependant.dependencies
    ]


@pytest.mark.parametrize("path", sorted(RUTAS))
@pytest.mark.parametrize(
    ("error", "codigo"),
    [
        (AnioLectivoInexistenteError("El año lectivo seleccionado no existe."), 404),
        (controlador.AnioLectivoActivoInexistenteError("Sin activo."), 409),
        (controlador.AnioLectivoDestinoInvalidoError("Estado incorrecto."), 409),
        (controlador.ConfirmacionAnioInvalidaError("Escribe 2026."), 409),
        (controlador.AnioLectivoReabiertoExistenteError("Ya hay uno."), 409),
    ],
)
def test_las_rutas_traducen_errores(monkeypatch, path, error, codigo):
    funcion_ruta, funcion_controlador = RUTAS[path]

    def rechazar(*_args):
        raise error

    monkeypatch.setattr(rutas, funcion_controlador, rechazar)

    with pytest.raises(HTTPException) as capturado:
        getattr(rutas, funcion_ruta)(1, _confirmacion())

    assert capturado.value.status_code == codigo
    assert capturado.value.detail == str(error)
