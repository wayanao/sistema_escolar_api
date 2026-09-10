"""`GET /observador/mis-estudiantes`: la lista de alumnos de un profesor.

Ver `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`. Existe para que la pantalla
del observador **no dependa de una asignacion elegida**: el observador es del
nino y no de la materia, y la clase solo servia para saber a quien listar.

Fija lo que puede romperse sin que nadie lo note:

- que la ruta estatica gana a `/observador/{estudiante_id}`, que es un accidente
  de una sola linea de distancia;
- que la lista usa **la misma regla** que el guard que deja abrir una bitacora,
  para que no pueda listar a quien no se puede abrir;
- que el admin no tiene lista, porque su `id` sale de otra tabla;
- que sigue siendo **una sola** consulta y una sola conexion.
"""
from contextlib import contextmanager

import pytest
from fastapi import HTTPException

from app.core import permissions
from app.repositories import observador_repository
from app.routes import observador


# (id, nombre, apellido, curso_id, curso)
FILAS = [
    (11, "Ana", "Rojas", 3, "PRIMERO-A"),
    (12, "Luis", "Pardo", 3, "PRIMERO-A"),
    (21, "Sofia", "Ruiz", 5, "SEGUNDO-B"),
]

PROFESOR = {"id": 7, "rol": "profesor"}
ADMIN = {"id": 1, "rol": "admin"}
ACUDIENTE = {"id": 3, "rol": "acudiente"}


class CursorFalso:
    def __init__(self, filas=()):
        self.filas = list(filas)
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchall(self):
        return self.filas

    def fetchone(self):
        return self.filas[0] if self.filas else None


class ContadorDeConexiones:
    def __init__(self, cursor):
        self.cursor = cursor
        self.abiertas = 0

    @contextmanager
    def __call__(self, commit=False, cursor_factory=None):
        self.abiertas += 1
        yield self.cursor


def cursor_de(monkeypatch, filas=FILAS):
    cursor = CursorFalso(filas=filas)
    contador = ContadorDeConexiones(cursor)
    monkeypatch.setattr(observador, "get_cursor", contador)
    return cursor, contador


# ---------------------------------------------------------------------------
# El orden de las rutas
# ---------------------------------------------------------------------------


def _rutas_de_observador():
    return [getattr(r, "path", "") for r in observador.router.routes]


def test_la_ruta_estatica_va_antes_que_la_parametrizada():
    """Un accidente de una linea: si se declarara despues, seria un 422.

    Starlette prueba las rutas en el orden en que se declaran.
    `/observador/mis-estudiantes` encaja tambien en el patron
    `/observador/{estudiante_id}`, asi que si la parametrizada fuera primero
    FastAPI intentaria convertir "mis-estudiantes" en `int` y respondería un 422
    incomprensible. No lo protege ningun framework: lo protege el orden.
    """
    rutas = _rutas_de_observador()

    assert rutas.index("/observador/mis-estudiantes") < rutas.index(
        "/observador/{estudiante_id}"
    )


def test_la_ruta_responde_de_verdad_por_http(monkeypatch):
    """La prueba anterior mira la estructura; esta pide la URL real.

    Se hace con ASGI a pelo porque `httpx` no esta instalado en este proyecto,
    igual que en `tests/test_notas_caracterizacion.py`.
    """
    from app.dependencies import get_current_user
    from app.main import app

    cursor_de(monkeypatch)

    app.dependency_overrides[get_current_user] = lambda: PROFESOR
    try:
        estado, cuerpo = _get_asgi(app, "/observador/mis-estudiantes")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert estado == 200, cuerpo
    assert [alumno["estudiante_id"] for alumno in cuerpo] == [11, 12, 21]
    assert isinstance(cuerpo, list)


def _get_asgi(aplicacion, ruta):
    import asyncio
    import json

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": ruta,
        "raw_path": ruta.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"testserver")],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    salida = {"status": None, "body": b""}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(mensaje):
        if mensaje["type"] == "http.response.start":
            salida["status"] = mensaje["status"]
        elif mensaje["type"] == "http.response.body":
            salida["body"] += mensaje.get("body", b"")

    asyncio.run(aplicacion(scope, receive, send))
    return salida["status"], json.loads(salida["body"].decode())


# ---------------------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------------------


def test_un_profesor_recibe_sus_alumnos_con_su_curso(monkeypatch):
    cursor, _ = cursor_de(monkeypatch)

    resultado = observador.listar_mis_estudiantes(PROFESOR)

    assert resultado[0] == {
        "estudiante_id": 11,
        "nombre": "Ana",
        "apellido": "Rojas",
        "curso_id": 3,
        "curso": "PRIMERO-A",
    }
    # El profesor sale del token, nunca de la URL: nadie puede pedir la lista
    # de otro cambiando un numero.
    assert cursor.calls[0][1] == (7,)


def test_el_admin_no_tiene_lista(monkeypatch):
    """Excepcion deliberada, y por un motivo medido.

    El `id` de un admin sale de `usuarios`, no de `profesor`. Devolverle una
    lista no daria error: daria los alumnos del profesor que por casualidad
    tenga ese mismo numero. En `tenant_colegio_1` la administradora tiene
    `usuarios.id = 1` y el profesor 1 es otra persona.
    """
    cursor, contador = cursor_de(monkeypatch)

    with pytest.raises(HTTPException) as exc:
        observador.listar_mis_estudiantes(ADMIN)

    assert exc.value.status_code == 403
    # Ni siquiera se abre la conexion.
    assert contador.abiertas == 0


def test_ningun_otro_rol_tiene_lista(monkeypatch):
    cursor_de(monkeypatch)

    with pytest.raises(HTTPException) as exc:
        observador.listar_mis_estudiantes(ACUDIENTE)

    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Coste: es la pantalla que existe para matar el N+1
# ---------------------------------------------------------------------------


def test_cuesta_una_sola_consulta_y_una_sola_conexion(monkeypatch):
    """La alternativa era pedir las clases y luego los alumnos de cada una.

    Con 6 cursos serian 7 idas y vueltas, a ~180 ms cada una contra Neon: seria
    reconstruir el N+1 justo en la pantalla que existe para matarlo.
    """
    cursor, contador = cursor_de(monkeypatch)

    observador.listar_mis_estudiantes(PROFESOR)

    assert len(cursor.calls) == 1
    assert contador.abiertas == 1


def test_un_fallo_de_base_no_filtra_el_mensaje_de_postgresql(monkeypatch):
    class CursorQueRevienta(CursorFalso):
        def execute(self, query, params=None):
            raise RuntimeError('relation "estudiantes" does not exist')

    contador = ContadorDeConexiones(CursorQueRevienta())
    monkeypatch.setattr(observador, "get_cursor", contador)

    with pytest.raises(HTTPException) as exc:
        observador.listar_mis_estudiantes(PROFESOR)

    assert exc.value.status_code == 500
    # El texto sale tal cual en un aviso de la pantalla de una profesora.
    assert "does not exist" not in exc.value.detail


# ---------------------------------------------------------------------------
# La consulta
# ---------------------------------------------------------------------------


def test_la_consulta_usa_la_misma_regla_que_el_guard_de_lectura():
    """Si las dos se separan, la lista miente.

    Mas ancha: listaria alumnos que al abrirlos dan 403. Mas estrecha:
    esconderia alumnos que si se pueden ver. Las dos son el mismo `JOIN` entre
    `estudiantes` y `asignaciones` por `curso_id`.
    """
    lista = " ".join(observador_repository._SELECT_MIS_ESTUDIANTES.split())
    guard = " ".join(permissions._SQL_PROFESOR_COMPARTE_CURSO.split())

    assert "JOIN asignaciones a ON a.curso_id = e.curso_id" in lista
    assert "JOIN asignaciones a ON a.curso_id = e.curso_id" in guard
    assert "a.profesor_id = %s" in lista
    assert "a.profesor_id = %s" in guard


def test_la_consulta_deduplica():
    """Sin `DISTINCT`, cada alumno saldria una vez por materia.

    No es un caso de borde: medido, el 73% de los pares profesor-curso dan mas
    de una materia, y una profesora da 9 en PRIMERO-A. Su curso apareceria nueve
    veces entero.
    """
    assert "SELECT DISTINCT" in observador_repository._SELECT_MIS_ESTUDIANTES


def test_la_consulta_solo_trae_alumnos_activos():
    """Igual que `GET /planilla/{asignacion_id}`, la lista que reemplaza.

    Filtra la lista, no el permiso: la bitacora de un alumno retirado se sigue
    pudiendo leer si se llega a ella por su id.
    """
    sql = " ".join(observador_repository._SELECT_MIS_ESTUDIANTES.split())

    assert "COALESCE(LOWER(e.estado), 'activo') = 'activo'" in sql


def test_la_consulta_ordena_por_curso_y_apellido():
    """La pantalla los agrupa por curso: un profesor puede tener 81 -medido-, y
    una lista plana de 81 nombres no se lee."""
    sql = " ".join(observador_repository._SELECT_MIS_ESTUDIANTES.split())

    assert "ORDER BY c.nombre, e.apellido, e.nombre" in sql


def test_no_hay_ninguna_ruta_de_borrado_en_el_observador():
    """Sigue sin existir, tambien despues de anadir una ruta nueva."""
    metodos = {
        metodo
        for r in observador.router.routes
        for metodo in getattr(r, "methods", set())
    }

    assert "DELETE" not in metodos
