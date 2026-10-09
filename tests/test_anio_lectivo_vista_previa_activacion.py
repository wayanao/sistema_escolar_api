"""Fase 6.2a: vista previa de la activación del año en preparación.

Solo lectura. Todo usa dobles: no se crea 2027 en una base real ni se
ejecutan migraciones.
"""
from contextlib import contextmanager

import pytest
from fastapi import HTTPException

from app.controllers import anios_lectivos_controller as controlador_anios
from app.repositories import anios_lectivos_repository as repositorio_anios
from app.routes import anios_lectivos as rutas_anios
from app.services.anio_lectivo import AnioLectivoInexistenteError


class CursorFalso:
    def __init__(self, una=(), todas=()):
        self.una = list(una)
        self.todas = list(todas)
        self.consultas = []

    def execute(self, sql, params=None):
        self.consultas.append((" ".join(str(sql).split()), params))

    def fetchone(self):
        return self.una.pop(0) if self.una else None

    def fetchall(self):
        return self.todas.pop(0) if self.todas else []


def _preparar_controlador(monkeypatch, pendientes):
    eventos = []
    cursor = object()

    @contextmanager
    def cursor_falso(commit=False):
        eventos.append(("commit", commit))
        yield cursor

    monkeypatch.setattr(controlador_anios, "get_cursor", cursor_falso)
    monkeypatch.setattr(
        controlador_anios,
        "_contexto_activacion",
        lambda cursor_recibido, anio_id: (
            (2, 2026, "activo"),
            (anio_id, 2027, "preparacion"),
        ),
    )
    monkeypatch.setattr(
        controlador_anios.anios_lectivos_repository,
        "contar_decisiones_activacion",
        lambda cursor_recibido, origen_id, destino_id: eventos.append(
            ("conteos", origen_id, destino_id)
        )
        or {"continuan": 170, "nuevos": 4, "retirados": 2, "egresados": 18},
        raising=False,
    )
    monkeypatch.setattr(
        controlador_anios.anios_lectivos_repository,
        "listar_sin_decidir_activacion",
        lambda cursor_recibido, origen_id, destino_id: eventos.append(
            ("pendientes", origen_id, destino_id)
        )
        or pendientes,
        raising=False,
    )
    return eventos


def test_la_vista_previa_reune_conteos_y_lista_de_pendientes(monkeypatch):
    eventos = _preparar_controlador(
        monkeypatch,
        [
            {
                "id": 7,
                "nombre": "Ana",
                "apellido": "Pérez",
                "documento_identidad": "1001",
                "curso_id": 20,
                "curso_nombre": "Quinto A",
                "curso_jornada": "Mañana",
            }
        ],
    )

    respuesta = controlador_anios.vista_previa_activacion_controller(3)

    assert respuesta == {
        "anio_origen": {"id": 2, "anio": 2026},
        "anio_destino": {"id": 3, "anio": 2027},
        "resumen": {
            "continuan": 170,
            "nuevos": 4,
            "retirados": 2,
            "egresados": 18,
            "sin_decidir": 1,
        },
        "puede_activar": False,
        "sin_decidir": [
            {
                "id": 7,
                "nombre": "Ana",
                "apellido": "Pérez",
                "documento_identidad": "1001",
                "curso_id": 20,
                "curso_nombre": "Quinto A",
                "curso_jornada": "Mañana",
            }
        ],
    }
    assert eventos == [
        ("commit", False),
        ("conteos", 2, 3),
        ("pendientes", 2, 3),
    ]


def test_sin_pendientes_el_backend_permite_activar(monkeypatch):
    _preparar_controlador(monkeypatch, [])

    respuesta = controlador_anios.vista_previa_activacion_controller(3)

    assert respuesta["puede_activar"] is True
    assert respuesta["resumen"]["sin_decidir"] == 0
    assert respuesta["sin_decidir"] == []


def _preparar_contexto(monkeypatch, activo, destino):
    monkeypatch.setattr(
        controlador_anios.anios_lectivos_repository,
        "leer_anio_activo",
        lambda _cursor: activo,
    )
    monkeypatch.setattr(
        controlador_anios.anios_lectivos_repository,
        "leer_anio_lectivo",
        lambda _cursor, _anio_id: destino,
    )


def test_el_contexto_lee_sin_bloquear_y_acepta_el_siguiente_en_preparacion(
    monkeypatch,
):
    _preparar_contexto(monkeypatch, (2, 2026, "activo"), (3, 2027, "preparacion"))

    def no_bloquear(*_args):
        raise AssertionError("la vista previa no debe bloquear filas")

    monkeypatch.setattr(
        controlador_anios.anios_lectivos_repository,
        "leer_anio_activo_para_actualizar",
        no_bloquear,
    )
    monkeypatch.setattr(
        controlador_anios.anios_lectivos_repository,
        "leer_anio_lectivo_para_actualizar",
        no_bloquear,
    )

    activo, destino = controlador_anios._contexto_activacion(object(), 3)

    assert activo == (2, 2026, "activo")
    assert destino == (3, 2027, "preparacion")


@pytest.mark.parametrize(
    ("activo", "destino", "error", "mensaje"),
    [
        (
            None,
            (3, 2027, "preparacion"),
            controlador_anios.AnioLectivoActivoInexistenteError,
            "No hay un año lectivo activo",
        ),
        (
            (2, 2026, "activo"),
            None,
            AnioLectivoInexistenteError,
            "no existe",
        ),
        (
            (2, 2026, "activo"),
            (2, 2026, "activo"),
            controlador_anios.AnioLectivoDestinoInvalidoError,
            "Solo se puede activar un año en preparación",
        ),
        (
            (2, 2026, "activo"),
            (4, 2028, "preparacion"),
            controlador_anios.AnioLectivoDestinoInvalidoError,
            "debe ser el 2027",
        ),
    ],
)
def test_el_contexto_rechaza_lo_que_no_se_puede_activar(
    monkeypatch, activo, destino, error, mensaje
):
    _preparar_contexto(monkeypatch, activo, destino)

    with pytest.raises(error, match=mensaje):
        controlador_anios._contexto_activacion(object(), 3)


def test_los_conteos_separan_quien_sigue_quien_llega_y_quien_sale():
    cursor = CursorFalso(una=[(170, 4, 2, 18)])

    conteos = repositorio_anios.contar_decisiones_activacion(cursor, 2, 3)

    assert conteos == {
        "continuan": 170,
        "nuevos": 4,
        "retirados": 2,
        "egresados": 18,
    }
    sql, params = cursor.consultas[0]
    assert params == (2, 3)
    assert sql.startswith("WITH origen AS")
    assert "estado_salida = 'retirado'" in sql
    assert "estado_salida = 'egresado'" in sql
    # Una matrícula en el destino cuenta como que el estudiante continúa.
    assert sql.count("NOT EXISTS (SELECT 1 FROM destino d") == 2
    for palabra in ("INSERT", "UPDATE", "DELETE"):
        assert palabra not in sql


def test_los_conteos_tambien_leen_un_cursor_de_diccionarios():
    fila = {"continuan": 1, "nuevos": 0, "retirados": 0, "egresados": 0}
    cursor = CursorFalso(una=[fila])

    assert repositorio_anios.contar_decisiones_activacion(cursor, 2, 3) == fila


def test_pendientes_son_activos_del_anio_sin_matricula_siguiente_ni_marca():
    fila = (7, "Ana", "Pérez", "1001", 20, "Quinto A", "Mañana")
    cursor = CursorFalso(todas=[[fila]])

    pendientes = repositorio_anios.listar_sin_decidir_activacion(cursor, 2, 3)

    assert pendientes == [
        {
            "id": 7,
            "nombre": "Ana",
            "apellido": "Pérez",
            "documento_identidad": "1001",
            "curso_id": 20,
            "curso_nombre": "Quinto A",
            "curso_jornada": "Mañana",
        }
    ]
    sql, params = cursor.consultas[0]
    assert params == (2, 3)
    assert "origen.anio_lectivo_id = %s" in sql
    assert "origen.estado_salida IS NULL" in sql
    assert "COALESCE(LOWER(e.estado), 'activo') = 'activo'" in sql
    assert "NOT EXISTS" in sql
    assert "destino.anio_lectivo_id = %s" in sql
    assert "LEFT JOIN cursos c ON c.id = origen.curso_id" in sql
    assert "ORDER BY c.nombre, c.jornada, e.apellido, e.nombre, e.id" in sql
    for palabra in ("INSERT", "UPDATE", "DELETE"):
        assert palabra not in sql


def _ruta_vista_previa():
    return next(
        ruta
        for ruta in rutas_anios.router.routes
        if ruta.path == "/anios-lectivos/{anio_lectivo_id}/activacion/vista-previa"
    )


def test_la_ruta_de_vista_previa_es_get_y_solo_admin():
    from app.dependencies import get_current_active_admin

    ruta = _ruta_vista_previa()

    assert ruta.methods == {"GET"}
    assert get_current_active_admin in [
        dependencia.call for dependencia in ruta.dependant.dependencies
    ]


@pytest.mark.parametrize(
    ("error", "codigo"),
    [
        (AnioLectivoInexistenteError("El año lectivo seleccionado no existe."), 404),
        (
            controlador_anios.AnioLectivoActivoInexistenteError(
                "No hay un año lectivo activo para cerrar."
            ),
            409,
        ),
        (
            controlador_anios.AnioLectivoDestinoInvalidoError(
                "Solo se puede activar un año en preparación."
            ),
            409,
        ),
    ],
)
def test_la_ruta_de_vista_previa_traduce_errores(monkeypatch, error, codigo):
    def rechazar(_anio_id):
        raise error

    monkeypatch.setattr(rutas_anios, "vista_previa_activacion_controller", rechazar)

    with pytest.raises(HTTPException) as capturado:
        rutas_anios.vista_previa_activacion(3)

    assert capturado.value.status_code == codigo
    assert capturado.value.detail == str(error)
