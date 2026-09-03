"""Caracterizacion de la ruta GET de observaciones, migrada en la subcapa 1.4k.

Era una de las dos unicas aperturas de conexion que vivian en la capa HTTP.

Se fija que los guards de permiso se ejecutan ANTES de leer el dominio, y que la
ruta devuelve None cuando no hay observacion guardada, en vez de un 404 o un
diccionario vacio.

Desde el 2026-09-03 los guards comparten el cursor de la ruta en vez de abrir
cada uno el suyo, asi que si tocan la base antes de aprobar: lo que se fija es
que ninguna consulta del DOMINIO se ejecute sin permiso, no que la base quede
intacta.
"""

from contextlib import contextmanager

import pytest
from fastapi import HTTPException

from app.routes import observaciones


class CursorFalso:
    def __init__(self, fila=None):
        self.fila = fila
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.fila


@pytest.fixture
def entorno(monkeypatch):
    def instalar(fila=None, asignacion_resuelta=77):
        cursor = CursorFalso(fila=fila)
        commits = []
        guards = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        monkeypatch.setattr(observaciones, "get_cursor", fake_get_cursor)
        monkeypatch.setattr(
            observaciones,
            "resolver_asignacion_academica_id_cursor",
            lambda _c, _a: asignacion_resuelta,
        )
        monkeypatch.setattr(
            observaciones,
            "require_asignacion_access",
            lambda *a, **k: guards.append("asignacion"),
        )
        monkeypatch.setattr(
            observaciones,
            "require_estudiante_in_asignacion",
            lambda *a, **k: guards.append("estudiante"),
        )
        return cursor, commits, guards

    return instalar


def test_obtener_observacion_devuelve_las_tres_dimensiones(entorno):
    cursor, commits, guards = entorno(fila=("Atento", "Analitico", "Fluido"))

    respuesta = observaciones.obtener_observacion(
        estudiante_id=11,
        asignacion_id=12,
        periodo=2,
        current_user={"id": 3, "rol": "profesor"},
    )

    query, params = cursor.calls[0]
    assert "FROM observaciones" in query
    assert params == (11, 77, 2)
    assert commits == [False]
    assert respuesta == {
        "conductual": "Atento",
        "cognitivo": "Analitico",
        "lenguaje": "Fluido",
    }


def test_obtener_observacion_devuelve_none_si_no_hay_registro(entorno):
    entorno(fila=None)

    respuesta = observaciones.obtener_observacion(
        estudiante_id=11,
        asignacion_id=12,
        periodo=2,
        current_user={"id": 3, "rol": "profesor"},
    )

    assert respuesta is None


def test_obtener_observacion_valida_permisos_antes_de_consultar(entorno):
    cursor, _, guards = entorno(fila=None)

    observaciones.obtener_observacion(
        estudiante_id=11,
        asignacion_id=12,
        periodo=2,
        current_user={"id": 3, "rol": "profesor"},
    )

    assert guards == ["asignacion", "estudiante"]


def test_obtener_observacion_no_consulta_si_el_guard_rechaza(entorno, monkeypatch):
    """Un guard que deniega corta antes de leer nada del dominio.

    Cambio del 2026-09-03: el guard ahora corre DENTRO del `with get_cursor()`,
    asi que el cursor si se abre antes de que deniegue. No cuesta una conexion
    de mas -antes el propio guard abria la suya para consultar la asignacion,
    asi que el pool ve una en los dos casos-, y a cambio la peticion aprobada,
    que es el caso normal, pasa de 3 conexiones a 1.

    Lo que se mantiene intacto y es lo que esta prueba cuida: **ninguna consulta
    del dominio llega a ejecutarse**.

    El doble lanza `HTTPException`, como los guards de verdad. Antes lanzaba
    `PermissionError`, que ningun guard lanza: hoy eso saldria como 500 -queda
    fijado en `test_un_403_de_un_guard_no_se_convierte_en_500`, que comprueba
    que una `HTTPException` sigue saliendo con su propio status-.
    """
    cursor, commits, _ = entorno(fila=None)

    def denegar(*_args, **_kwargs):
        raise HTTPException(status_code=403, detail="sin acceso a la asignacion")

    monkeypatch.setattr(observaciones, "require_asignacion_access", denegar)

    with pytest.raises(HTTPException) as exc:
        observaciones.obtener_observacion(
            estudiante_id=11,
            asignacion_id=12,
            periodo=2,
            current_user={"id": 3, "rol": "profesor"},
        )

    assert exc.value.status_code == 403
    assert cursor.calls == []
    assert commits == [False]
