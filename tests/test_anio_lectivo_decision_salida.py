"""Fase 6.2b: guardar o quitar la decisión de salida del año que termina.

La marca vive en la matrícula del año activo (`estado_salida`) y se excluye
con una matrícula en el año siguiente. Todo usa dobles: no se escribe en una
base real.
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
    def __init__(self, todas=(), filas_afectadas=0):
        self.todas = list(todas)
        self.consultas = []
        self.rowcount = filas_afectadas

    def execute(self, sql, params=None):
        self.consultas.append((" ".join(str(sql).split()), params))

    def fetchall(self):
        return self.todas.pop(0) if self.todas else []


def _decision(**cambios):
    datos = {"estudiante_ids": [1, 2], "estado_salida": "egresado"}
    datos.update(cambios)
    return esquemas.DecisionSalidaEstudiantes(**datos)


# ---------------------------------------------------------------------------
# Cuerpo de la petición
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("estado", ["retirado", "egresado", None])
def test_el_cuerpo_acepta_retirado_egresado_o_quitar_la_marca(estado):
    decision = _decision(estado_salida=estado)

    assert decision.estado_salida == estado


def test_el_cuerpo_exige_decir_la_marca_aunque_sea_para_quitarla():
    with pytest.raises(ValidationError):
        esquemas.DecisionSalidaEstudiantes(estudiante_ids=[1])


@pytest.mark.parametrize("estado", ["inactivo", "activo", "RETIRADO", ""])
def test_el_cuerpo_rechaza_otras_marcas(estado):
    with pytest.raises(ValidationError):
        _decision(estado_salida=estado)


@pytest.mark.parametrize("ids", [[], [1, 1], [0], [-4]])
def test_el_cuerpo_rechaza_ids_vacios_repetidos_o_no_positivos(ids):
    with pytest.raises(ValidationError):
        _decision(estudiante_ids=ids)


# ---------------------------------------------------------------------------
# Controlador
# ---------------------------------------------------------------------------


@pytest.fixture
def entorno_salida(monkeypatch):
    estado = SimpleNamespace(
        activo=(2, 2026, "activo"),
        destino=(3, 2027, "preparacion"),
        matriculas=[
            {"estudiante_id": 1, "estado_salida": None, "matriculado_en_destino": False},
            {"estudiante_id": 2, "estado_salida": "retirado", "matriculado_en_destino": False},
            {"estudiante_id": 3, "estado_salida": None, "matriculado_en_destino": True},
        ],
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

    def leer_activo_bloqueando(cursor_recibido):
        estado.eventos.append(("bloquea_activo", cursor_recibido is cursor))
        return estado.activo

    def leer_destino_bloqueando(cursor_recibido, anio_id):
        estado.eventos.append(("bloquea_destino", cursor_recibido is cursor, anio_id))
        return estado.destino

    def listar_matriculas(cursor_recibido, estudiante_ids, origen_id, destino_id):
        estado.eventos.append(
            ("lee", cursor_recibido is cursor, list(estudiante_ids), origen_id, destino_id)
        )
        return [
            fila for fila in estado.matriculas if fila["estudiante_id"] in estudiante_ids
        ]

    def guardar(cursor_recibido, estudiante_ids, origen_id, estado_salida):
        estado.eventos.append(
            ("guarda", cursor_recibido is cursor, list(estudiante_ids), origen_id, estado_salida)
        )
        return len(estudiante_ids)

    monkeypatch.setattr(controlador, "get_cursor", get_cursor_falso)
    dobles = {
        "leer_anio_activo_para_actualizar": leer_activo_bloqueando,
        "leer_anio_lectivo_para_actualizar": leer_destino_bloqueando,
        "listar_matriculas_para_salida": listar_matriculas,
        "guardar_estado_salida": guardar,
    }
    for nombre, doble in dobles.items():
        monkeypatch.setattr(
            controlador.anios_lectivos_repository, nombre, doble, raising=False
        )
    return estado


def test_marca_la_salida_en_la_matricula_del_anio_activo(entorno_salida):
    respuesta = controlador.guardar_decision_salida_controller(
        3, _decision(estudiante_ids=[1, 2], estado_salida="egresado")
    )

    assert respuesta == {
        "anio_origen": {"id": 2, "anio": 2026},
        "anio_destino": {"id": 3, "anio": 2027},
        "estado_salida": "egresado",
        "estudiante_ids": [1, 2],
        "cantidad": 2,
    }
    assert entorno_salida.eventos == [
        ("abre", True),
        ("bloquea_activo", True),
        ("bloquea_destino", True, 3),
        ("lee", True, [1, 2], 2, 3),
        ("guarda", True, [1, 2], 2, "egresado"),
    ]
    assert entorno_salida.commits == 1


def test_quitar_la_marca_se_permite_aunque_ya_tenga_matricula_siguiente(
    entorno_salida,
):
    respuesta = controlador.guardar_decision_salida_controller(
        3, _decision(estudiante_ids=[3], estado_salida=None)
    )

    assert respuesta["estado_salida"] is None
    assert ("guarda", True, [3], 2, None) in entorno_salida.eventos
    assert entorno_salida.commits == 1


def test_no_marca_a_quien_ya_tiene_matricula_en_el_anio_siguiente(entorno_salida):
    with pytest.raises(
        controlador.CandidatosMatriculaInvalidosError,
        match="ya tienen matrícula en 2027",
    ):
        controlador.guardar_decision_salida_controller(
            3, _decision(estudiante_ids=[1, 3], estado_salida="retirado")
        )

    assert not any(evento[0] == "guarda" for evento in entorno_salida.eventos)
    assert entorno_salida.rollbacks == 1


@pytest.mark.parametrize("estado", ["retirado", None])
def test_no_marca_a_quien_no_tiene_matricula_en_el_anio_activo(
    entorno_salida, estado
):
    with pytest.raises(
        controlador.CandidatosMatriculaInvalidosError,
        match="no tienen matrícula en el año lectivo 2026",
    ):
        controlador.guardar_decision_salida_controller(
            3, _decision(estudiante_ids=[1, 99], estado_salida=estado)
        )

    assert not any(evento[0] == "guarda" for evento in entorno_salida.eventos)
    assert entorno_salida.rollbacks == 1


def test_no_marca_si_el_destino_no_es_el_siguiente_en_preparacion(entorno_salida):
    entorno_salida.destino = (3, 2027, "activo")

    with pytest.raises(controlador.AnioLectivoDestinoInvalidoError):
        controlador.guardar_decision_salida_controller(3, _decision())

    assert not any(evento[0] in {"lee", "guarda"} for evento in entorno_salida.eventos)
    assert entorno_salida.rollbacks == 1


# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------


def test_lee_la_matricula_activa_y_si_existe_la_siguiente():
    cursor = CursorFalso(todas=[[(1, "retirado", False)]])

    filas = repositorio.listar_matriculas_para_salida(cursor, [1, 2], 2, 3)

    assert filas == [
        {"estudiante_id": 1, "estado_salida": "retirado", "matriculado_en_destino": False}
    ]
    sql, params = cursor.consultas[0]
    assert params == (3, 2, [1, 2])
    assert "FROM matriculas origen" in sql
    assert "LEFT JOIN matriculas destino" in sql
    assert "destino.anio_lectivo_id = %s" in sql
    assert "origen.anio_lectivo_id = %s" in sql
    assert "origen.estudiante_id = ANY(%s)" in sql


def test_guardar_solo_cambia_la_marca_de_la_matricula_activa():
    cursor = CursorFalso(filas_afectadas=2)

    afectadas = repositorio.guardar_estado_salida(cursor, [1, 2], 2, "egresado")

    assert afectadas == 2
    sql, params = cursor.consultas[0]
    assert sql == (
        "UPDATE matriculas SET estado_salida = %s "
        "WHERE anio_lectivo_id = %s AND estudiante_id = ANY(%s)"
    )
    assert params == ("egresado", 2, [1, 2])


# ---------------------------------------------------------------------------
# Ruta
# ---------------------------------------------------------------------------


def _ruta_salida():
    return next(
        ruta
        for ruta in rutas.router.routes
        if ruta.path == "/anios-lectivos/{anio_lectivo_id}/matriculas/salida"
    )


def test_la_ruta_de_salida_es_put_y_solo_admin():
    from app.dependencies import get_current_active_admin

    ruta = _ruta_salida()

    assert ruta.methods == {"PUT"}
    assert get_current_active_admin in [
        dependencia.call for dependencia in ruta.dependant.dependencies
    ]


def test_la_ruta_de_salida_pasa_el_cuerpo_al_controlador(monkeypatch):
    recibidos = []
    monkeypatch.setattr(
        rutas,
        "guardar_decision_salida_controller",
        lambda anio_id, datos: recibidos.append((anio_id, datos)) or {"ok": True},
    )
    decision = _decision()

    assert rutas.guardar_decision_salida(3, decision) == {"ok": True}
    assert recibidos == [(3, decision)]


@pytest.mark.parametrize(
    ("error", "codigo"),
    [
        (AnioLectivoInexistenteError("El año lectivo seleccionado no existe."), 404),
        (
            controlador.AnioLectivoDestinoInvalidoError(
                "Solo se puede matricular en un año en preparación."
            ),
            409,
        ),
        (
            controlador.CandidatosMatriculaInvalidosError(
                "Los estudiantes 3 ya tienen matrícula en 2027."
            ),
            409,
        ),
    ],
)
def test_la_ruta_de_salida_traduce_errores(monkeypatch, error, codigo):
    def rechazar(*_args):
        raise error

    monkeypatch.setattr(rutas, "guardar_decision_salida_controller", rechazar)

    with pytest.raises(HTTPException) as capturado:
        rutas.guardar_decision_salida(3, _decision())

    assert capturado.value.status_code == codigo
    assert capturado.value.detail == str(error)
