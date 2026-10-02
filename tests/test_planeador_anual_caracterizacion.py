import ast
import asyncio
import json
import re
from contextlib import contextmanager
from datetime import date
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException

from app.controllers import planeador_anual_controller
from app.core import permissions
from app.routes import planeador_anual
from app.schemas.planeador_anual import (
    PlaneadorAnual,
    PlaneadorAnualCreate,
    PlaneadorAnualUpdate,
)


ROOT = Path(__file__).resolve().parents[1]
ROUTE_PATH = ROOT / "app" / "routes" / "planeador_anual.py"
CONTROLLER_PATH = ROOT / "app" / "controllers" / "planeador_anual_controller.py"
REPOSITORY_PATH = ROOT / "app" / "repositories" / "planeador_anual_repository.py"
SCHEMA_PATH = ROOT / "app" / "schemas" / "planeador_anual.py"
BASE_DDL_PATH = ROOT / "migrations" / "base" / "20260813_esquema_base_tenant.sql"
ADMIN = {"id": 9, "rol": "admin"}
# Año lectivo, paso 3.7: la guardia de escritura lee el año de la clase, la
# primera consulta del guardado. Aqui se cuenta como las demas.
SQL_GUARDIA = "SELECT al.anio, al.estado"


def _source(path):
    return path.read_text(encoding="utf-8")


def _sql_literals(path):
    tree = ast.parse(_source(path))
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and re.search(r"\b(?:SELECT|INSERT|UPDATE|DELETE)\b", node.value, re.IGNORECASE)
    ]


def test_frontera_propia_incluye_un_repositorio_y_no_un_servicio():
    assert ROUTE_PATH.is_file()
    assert CONTROLLER_PATH.is_file()
    assert REPOSITORY_PATH.is_file()
    assert SCHEMA_PATH.is_file()
    assert not (ROOT / "app" / "services" / "planeador_anual_service.py").exists()
    assert "app.include_router(planeador_anual.router)" in _source(ROOT / "app" / "main.py")


def test_router_expone_exactamente_get_y_put_sin_response_model():
    rutas = {
        (method, route.path): route
        for route in planeador_anual.router.routes
        for method in route.methods
    }

    assert set(rutas) == {
        ("GET", "/planeador-anual/{asignacion_id}/{periodo}"),
        ("PUT", "/planeador-anual/{asignacion_id}/{periodo}"),
    }
    assert all(route.response_model is None for route in rutas.values())


def test_ruta_solo_importa_los_dos_controladores_con_consumidor_http():
    tree = ast.parse(_source(ROUTE_PATH))
    importados = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "app.controllers.planeador_anual_controller"
        for alias in node.names
    }

    assert importados == {
        "obtener_planeadores_anual_controller",
        "bulk_actualizar_planeadores_controller",
    }
    assert "crear_planeador_anual_controller" not in _source(ROUTE_PATH)
    assert "actualizar_planeador_anual_controller" not in _source(ROUTE_PATH)


def test_cinco_sql_viven_unicamente_en_el_repositorio():
    sql_repositorio = _sql_literals(REPOSITORY_PATH)

    assert len(sql_repositorio) == 5
    assert _sql_literals(CONTROLLER_PATH) == []
    assert _sql_literals(ROUTE_PATH) == []
    assert _sql_literals(SCHEMA_PATH) == []
    operaciones = [sql.lstrip().split(None, 1)[0].upper() for sql in sql_repositorio]
    assert operaciones.count("INSERT") == 2
    assert operaciones.count("SELECT") == 1
    assert operaciones.count("UPDATE") == 1
    assert operaciones.count("DELETE") == 1


def test_repositorio_tiene_cinco_funciones_cursor_first_sin_administrar_recursos():
    tree = ast.parse(_source(REPOSITORY_PATH))
    funciones = [node for node in tree.body if isinstance(node, ast.FunctionDef)]

    assert [funcion.name for funcion in funciones] == [
        "insertar_planeador_anual",
        "seleccionar_planeadores_anuales",
        "actualizar_planeador_anual",
        "eliminar_slot_planeador",
        "guardar_slot_planeador",
    ]
    assert all(funcion.args.args[0].arg == "cursor" for funcion in funciones)
    source = _source(REPOSITORY_PATH)
    assert "get_connection" not in source
    assert "get_cursor" not in source
    assert ".commit(" not in source
    assert ".rollback(" not in source
    assert ".close(" not in source


def test_ddl_fija_periodos_slots_unicidad_y_fk_con_cascade():
    ddl = _source(BASE_DDL_PATH)
    tabla = ddl.split("CREATE TABLE IF NOT EXISTS planeador_anual (", 1)[1].split(");", 1)[0]

    assert "periodo integer NOT NULL" in tabla
    assert "slot integer NOT NULL" in tabla
    assert "CHECK (((periodo >= 1) AND (periodo <= 4)))" in tabla
    assert "CHECK (((slot >= 1) AND (slot <= 8)))" in tabla
    assert "UNIQUE (asignacion_id, periodo, slot)" in tabla
    assert (
        "planeador_anual_asignacion_id_fkey FOREIGN KEY (asignacion_id) "
        "REFERENCES asignaciones(id) ON DELETE CASCADE"
    ) in ddl


def test_esquemas_create_y_respuesta_omiten_periodo_y_slot():
    create = PlaneadorAnualCreate(
        asignacion_id=10,
        periodo=2,
        slot=1,
        contenido="Fracciones",
        fecha="2026-08-15",
    )
    respuesta = PlaneadorAnual(
        id=5,
        asignacion_id=10,
        periodo=2,
        slot=1,
        contenido="Fracciones",
        fecha="2026-08-15",
    )

    assert "periodo" not in create.model_dump()
    assert "slot" not in create.model_dump()
    assert "periodo" not in respuesta.model_dump()
    assert "slot" not in respuesta.model_dump()


def test_borde_notificaciones_planeadores_pertenece_a_plan_de_clases():
    ruta_vecina = _source(ROOT / "app" / "routes" / "plan_de_clases.py")
    servicio_vecino = _source(ROOT / "app" / "services" / "plan_de_clases_service.py")

    assert '@router.get("/notificaciones/planeadores")' in ruta_vecina
    assert "planeador_anual_controller" not in ruta_vecina
    assert "planeador_anual_controller" not in servicio_vecino
    assert "/notificaciones/planeadores" not in _source(ROUTE_PATH)


async def _asgi_request(app, method, path, payload=None):
    body = b"" if payload is None else json.dumps(payload).encode("utf-8")
    headers = [(b"host", b"testserver")]
    if payload is not None:
        headers.extend(
            [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ]
        )
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "root_path": "",
        "headers": headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    request_sent = False
    messages = []

    async def receive():
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)
    start = next(message for message in messages if message["type"] == "http.response.start")
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return start["status"], json.loads(response_body or b"null")


def _http_app(current_user, dependency_calls):
    app = FastAPI()
    app.include_router(planeador_anual.router)

    def fake_current_user():
        dependency_calls.append(current_user)
        return current_user

    app.dependency_overrides[planeador_anual.get_current_user] = fake_current_user
    return app


def test_get_http_conserva_status_payload_orden_fecha_guard_y_un_auth(monkeypatch):
    dependency_calls = []
    guard_calls = []
    current_user = {"id": 9, "rol": "admin"}
    app = _http_app(current_user, dependency_calls)
    monkeypatch.setattr(
        planeador_anual,
        "require_asignacion_access",
        lambda asignacion_id, user: guard_calls.append((asignacion_id, user)),
    )
    monkeypatch.setattr(
        planeador_anual,
        "obtener_planeadores_anual_controller",
        lambda asignacion_id, periodo: [
            {
                "id": 5,
                "asignacion_id": asignacion_id,
                "periodo": periodo,
                "slot": 2,
                "unidad_tematica": "Fracciones",
                "estandar_competencia": "Comprende",
                "contenido": "Equivalencias",
                "actividades_recursos": "Guía",
                "fecha": date(2026, 8, 15),
            }
        ],
    )

    status, payload = asyncio.run(_asgi_request(app, "GET", "/planeador-anual/10/2"))

    assert status == 200
    assert payload == {
        "planeadores": [
            {
                "id": 5,
                "asignacion_id": 10,
                "periodo": 2,
                "slot": 2,
                "unidad_tematica": "Fracciones",
                "estandar_competencia": "Comprende",
                "contenido": "Equivalencias",
                "actividades_recursos": "Guía",
                "fecha": "2026-08-15",
            }
        ]
    }
    assert list(payload) == ["planeadores"]
    assert guard_calls == [(10, current_user)]
    assert dependency_calls == [current_user]


def test_put_http_conserva_status_payload_normalizacion_y_guard(monkeypatch):
    dependency_calls = []
    guard_calls = []
    controller_calls = []
    current_user = {"id": 9, "rol": "profesor"}
    app = _http_app(current_user, dependency_calls)
    monkeypatch.setattr(
        planeador_anual,
        "require_asignacion_access",
        lambda asignacion_id, user: guard_calls.append((asignacion_id, user)),
    )
    monkeypatch.setattr(
        planeador_anual,
        "bulk_actualizar_planeadores_controller",
        lambda asignacion_id, periodo, filas, usuario: controller_calls.append(
            (asignacion_id, periodo, filas, usuario)
        ),
    )

    status, payload = asyncio.run(
        _asgi_request(
            app,
            "PUT",
            "/planeador-anual/10/2",
            [
                {
                    "contenido": "  Fracciones equivalentes  ",
                    "fecha": "2026-08-15",
                },
                {"fecha": ""},
            ],
        )
    )

    assert status == 200
    assert payload == {"message": "Planeador actualizado correctamente"}
    assert guard_calls == [(10, current_user)]
    assert dependency_calls == [current_user]
    asignacion_id, periodo, filas, usuario = controller_calls[0]
    assert (asignacion_id, periodo) == (10, 2)
    assert usuario == current_user
    assert [(fila.contenido, fila.fecha) for fila in filas] == [
        ("Fracciones equivalentes", date(2026, 8, 15)),
        ("", None),
    ]


def test_put_http_invalido_responde_422_antes_del_controlador(monkeypatch):
    dependency_calls = []
    controller_calls = []
    app = _http_app({"id": 9, "rol": "admin"}, dependency_calls)
    monkeypatch.setattr(
        planeador_anual,
        "bulk_actualizar_planeadores_controller",
        lambda *args, **kwargs: controller_calls.append(args),
    )

    status, payload = asyncio.run(
        _asgi_request(
            app,
            "PUT",
            "/planeador-anual/10/2",
            [{"contenido": "Sin fecha"}],
        )
    )

    assert status == 422
    assert payload["detail"][0]["loc"] == ["body", 0]
    assert "fecha" in payload["detail"][0]["msg"]
    assert payload["detail"][0]["ctx"] == {"error": {}}
    assert controller_calls == []


@pytest.mark.parametrize(
    ("method", "payload"),
    [("GET", None), ("PUT", [])],
)
def test_path_no_entero_responde_422_antes_del_controlador(monkeypatch, method, payload):
    dependency_calls = []
    controller_calls = []
    app = _http_app({"id": 9, "rol": "admin"}, dependency_calls)
    monkeypatch.setattr(
        planeador_anual,
        "obtener_planeadores_anual_controller",
        lambda *args: controller_calls.append(args),
    )
    monkeypatch.setattr(
        planeador_anual,
        "bulk_actualizar_planeadores_controller",
        lambda *args, **kwargs: controller_calls.append(args),
    )

    status, response = asyncio.run(
        _asgi_request(app, method, "/planeador-anual/no-entero/2", payload)
    )

    assert status == 422
    assert response["detail"][0]["loc"] == ["path", "asignacion_id"]
    assert controller_calls == []


def test_get_http_no_limita_periodo_antes_del_controlador(monkeypatch):
    dependency_calls = []
    controller_calls = []
    app = _http_app({"id": 9, "rol": "admin"}, dependency_calls)
    monkeypatch.setattr(planeador_anual, "require_asignacion_access", lambda *_args: None)

    def obtener(asignacion_id, periodo):
        controller_calls.append((asignacion_id, periodo))
        return []

    monkeypatch.setattr(planeador_anual, "obtener_planeadores_anual_controller", obtener)

    status, payload = asyncio.run(_asgi_request(app, "GET", "/planeador-anual/10/5"))

    assert status == 200
    assert payload == {"planeadores": []}
    assert controller_calls == [(10, 5)]


def test_put_http_no_limita_el_lote_a_los_ocho_slots_del_ddl(monkeypatch):
    dependency_calls = []
    controller_calls = []
    app = _http_app({"id": 9, "rol": "admin"}, dependency_calls)
    monkeypatch.setattr(planeador_anual, "require_asignacion_access", lambda *_args: None)
    monkeypatch.setattr(
        planeador_anual,
        "bulk_actualizar_planeadores_controller",
        lambda _asignacion_id, _periodo, filas, usuario: controller_calls.append(filas),
    )
    filas = [
        {"contenido": f"Contenido {slot}", "fecha": "2026-08-15"}
        for slot in range(1, 10)
    ]

    status, payload = asyncio.run(
        _asgi_request(app, "PUT", "/planeador-anual/10/2", filas)
    )

    assert status == 200
    assert payload == {"message": "Planeador actualizado correctamente"}
    assert len(controller_calls[0]) == 9


def test_guard_403_corre_fuera_del_try_y_conserva_detail(monkeypatch):
    dependency_calls = []
    controller_calls = []
    app = _http_app({"id": 4, "rol": "profesor"}, dependency_calls)

    def denegar(_asignacion_id, _current_user):
        raise HTTPException(status_code=403, detail="No autorizado")

    monkeypatch.setattr(planeador_anual, "require_asignacion_access", denegar)
    monkeypatch.setattr(
        planeador_anual,
        "obtener_planeadores_anual_controller",
        lambda *args: controller_calls.append(args),
    )

    status, payload = asyncio.run(_asgi_request(app, "GET", "/planeador-anual/10/2"))

    assert status == 403
    assert payload == {"detail": "No autorizado"}
    assert controller_calls == []


@pytest.mark.parametrize("method", ["GET", "PUT"])
def test_fallo_del_controlador_responde_500_y_expone_el_texto(monkeypatch, method):
    dependency_calls = []
    app = _http_app({"id": 9, "rol": "admin"}, dependency_calls)
    monkeypatch.setattr(planeador_anual, "require_asignacion_access", lambda *_args: None)

    def fallar(*_args, **_kwargs):
        raise RuntimeError("detalle interno planeador")

    if method == "GET":
        monkeypatch.setattr(planeador_anual, "obtener_planeadores_anual_controller", fallar)
        payload_enviado = None
    else:
        monkeypatch.setattr(planeador_anual, "bulk_actualizar_planeadores_controller", fallar)
        payload_enviado = []

    status, payload = asyncio.run(
        _asgi_request(app, method, "/planeador-anual/10/2", payload_enviado)
    )

    assert status == 500
    assert payload == {"detail": "detalle interno planeador"}


class RecordingCursor:
    def __init__(self, fetchone_values=(), fetchall_value=(), fail_on_call=None):
        self.fetchone_values = list(fetchone_values)
        self.fetchall_value = list(fetchall_value)
        self.fail_on_call = fail_on_call
        self.calls = []
        self.closed = False

    def execute(self, query, params=None):
        self.calls.append((query, params))
        if self.fail_on_call is not None and len(self.calls) == self.fail_on_call:
            raise RuntimeError("fallo simulado")

    def fetchone(self):
        if self.calls and SQL_GUARDIA in self.calls[-1][0]:
            return (2026, "activo")
        return self.fetchone_values.pop(0)

    def fetchall(self):
        return self.fetchall_value

    def close(self):
        self.closed = True


class RecordingConnection:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def _install_permission_connection(monkeypatch, allowed=True):
    cursor = RecordingCursor(fetchone_values=[(1,) if allowed else None])
    conn = RecordingConnection(cursor)
    calls = []

    def factory():
        calls.append(conn)
        return conn

    monkeypatch.setattr(permissions, "get_connection", factory)
    return cursor, conn, calls


def _install_get_cursor(monkeypatch, rows):
    cursor = RecordingCursor(fetchone_values=[(77,)], fetchall_value=rows)
    contexts = []
    closed = []

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        contexts.append((commit, cursor_factory))
        try:
            yield cursor
        finally:
            closed.append(True)

    monkeypatch.setattr(planeador_anual_controller, "get_cursor", fake_get_cursor)
    return cursor, contexts, closed


@pytest.mark.parametrize(
    ("current_user", "expected_queries", "expected_connections"),
    [
        ({"id": 9, "rol": "admin"}, 2, 1),
        ({"id": 9, "rol": "profesor"}, 3, 2),
    ],
)
def test_get_tiene_conteo_constante_y_conserva_recursos(
    monkeypatch,
    current_user,
    expected_queries,
    expected_connections,
):
    permission_cursor, permission_conn, permission_connections = (
        _install_permission_connection(monkeypatch)
    )
    rows = [
        (1, 77, 2, 1, "Unidad 1", "Estándar 1", "Contenido 1", "Guía 1", None),
        (2, 77, 2, 2, "Unidad 2", "Estándar 2", "Contenido 2", "Guía 2", None),
        (3, 77, 2, 3, "Unidad 3", "Estándar 3", "Contenido 3", "Guía 3", None),
    ]
    controller_cursor, contexts, closed = _install_get_cursor(monkeypatch, rows)

    resultado = planeador_anual.obtener_planeador_anual(10, 2, current_user)

    assert len(resultado["planeadores"]) == 3
    assert len(permission_cursor.calls) + len(controller_cursor.calls) == expected_queries
    assert len(permission_connections) + len(contexts) == expected_connections
    assert contexts == [(False, None)]
    assert closed == [True]
    if current_user["rol"] == "profesor":
        assert permission_conn.closed is True
        assert permission_cursor.closed is True
    else:
        assert permission_connections == []


def test_profesor_sin_ownership_recibe_403_y_no_llega_al_controlador(monkeypatch):
    permission_cursor, permission_conn, permission_connections = (
        _install_permission_connection(monkeypatch, allowed=False)
    )
    controller_calls = []
    monkeypatch.setattr(
        planeador_anual,
        "obtener_planeadores_anual_controller",
        lambda *args: controller_calls.append(args),
    )

    with pytest.raises(HTTPException) as exc_info:
        planeador_anual.obtener_planeador_anual(10, 2, {"id": 9, "rol": "profesor"})

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "No autorizado"
    assert len(permission_cursor.calls) == 1
    assert len(permission_connections) == 1
    assert permission_cursor.closed is True
    assert permission_conn.closed is True
    assert controller_calls == []


def test_rol_ajeno_recibe_403_sin_abrir_conexion(monkeypatch):
    monkeypatch.setattr(
        permissions,
        "get_connection",
        lambda: pytest.fail("un rol ajeno no debe consultar ownership"),
    )

    with pytest.raises(HTTPException) as exc_info:
        planeador_anual.obtener_planeador_anual(10, 2, {"id": 3, "rol": "estudiante"})

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "No autorizado"


def _filled_rows(count):
    return [
        PlaneadorAnualUpdate(contenido=f"Contenido {slot}", fecha="2026-08-15")
        for slot in range(1, count + 1)
    ]


# Año lectivo, paso 3.7: la guardia suma una consulta y ninguna conexion
# (antes 2/4/3/5).
@pytest.mark.parametrize(
    ("role", "row_count", "expected_queries", "expected_connections"),
    [
        ("admin", 1, 3, 1),
        ("admin", 3, 5, 1),
        ("profesor", 1, 4, 2),
        ("profesor", 3, 6, 2),
    ],
)
def test_put_es_un_mas_n_consultas_con_conexiones_constantes(
    monkeypatch,
    role,
    row_count,
    expected_queries,
    expected_connections,
):
    permission_cursor, permission_conn, permission_connections = (
        _install_permission_connection(monkeypatch)
    )
    controller_cursor = RecordingCursor(fetchone_values=[(77,)])
    controller_conn = RecordingConnection(controller_cursor)
    controller_connections = []

    def controller_factory():
        controller_connections.append(controller_conn)
        return controller_conn

    monkeypatch.setattr(planeador_anual_controller, "get_connection", controller_factory)
    current_user = {"id": 9, "rol": role}

    resultado = planeador_anual.actualizar_planeador_anual(
        10,
        2,
        _filled_rows(row_count),
        current_user,
    )

    assert resultado == {"message": "Planeador actualizado correctamente"}
    assert len(permission_cursor.calls) + len(controller_cursor.calls) == expected_queries
    assert len(permission_connections) + len(controller_connections) == expected_connections
    assert controller_conn.commits == 1
    assert controller_conn.rollbacks == 0
    assert controller_cursor.closed is True
    assert controller_conn.closed is True
    if role == "profesor":
        assert permission_conn.closed is True
    else:
        assert permission_connections == []


def test_put_mas_corto_no_borra_slots_que_no_llegan_en_el_payload(monkeypatch):
    cursor = RecordingCursor(fetchone_values=[(77,)])
    conn = RecordingConnection(cursor)
    monkeypatch.setattr(planeador_anual_controller, "get_connection", lambda: conn)

    planeador_anual_controller.bulk_actualizar_planeadores_controller(
        10,
        2,
        _filled_rows(1),
        usuario=ADMIN,
    )

    # calls[0] es la guardia del año lectivo (paso 3.7), calls[1] el resolutor.
    consultas_dominio = cursor.calls[2:]
    assert len(consultas_dominio) == 1
    assert "INSERT INTO planeador_anual" in consultas_dominio[0][0]
    assert "ON CONFLICT (asignacion_id, periodo, slot)" in consultas_dominio[0][0]
    assert all("DELETE FROM planeador_anual" not in query for query, _params in consultas_dominio)


def test_put_vacio_confirma_sin_borrar_ningun_slot(monkeypatch):
    cursor = RecordingCursor(fetchone_values=[(77,)])
    conn = RecordingConnection(cursor)
    monkeypatch.setattr(planeador_anual_controller, "get_connection", lambda: conn)

    planeador_anual_controller.bulk_actualizar_planeadores_controller(10, 2, [], usuario=ADMIN)

    # La guardia del año lectivo (paso 3.7) y el resolutor; nada de escritura.
    assert len(cursor.calls) == 2
    assert SQL_GUARDIA in cursor.calls[0][0]
    assert "FROM asignaciones" in cursor.calls[1][0]
    assert conn.commits == 1
    assert conn.rollbacks == 0
    assert cursor.closed is True
    assert conn.closed is True


def test_bulk_fallido_revierte_y_cierra_la_conexion(monkeypatch):
    # Falla el segundo INSERT: 1 guardia del año (paso 3.7), 2 resolutor, 3 y 4
    # los INSERT.
    cursor = RecordingCursor(fetchone_values=[(77,)], fail_on_call=4)
    conn = RecordingConnection(cursor)
    monkeypatch.setattr(planeador_anual_controller, "get_connection", lambda: conn)

    with pytest.raises(RuntimeError, match="fallo simulado"):
        planeador_anual_controller.bulk_actualizar_planeadores_controller(
            10,
            2,
            _filled_rows(2),
            usuario=ADMIN,
        )

    assert conn.commits == 0
    assert conn.rollbacks == 1
    assert cursor.closed is True
    assert conn.closed is True


def test_permiso_y_resolutor_no_filtran_asignaciones_inactivas():
    permiso = _source(ROOT / "app" / "core" / "permissions.py")
    resolutor = _source(ROOT / "app" / "services" / "asignacion_academica.py")
    bloque_permiso = permiso.split("def require_asignacion_access", 1)[1].split(
        "def require_estudiante_in_asignacion", 1
    )[0]
    bloque_resolutor = resolutor.split(
        "def resolver_asignacion_academica_id_cursor", 1
    )[1].split("def resolver_asignacion_academica_id", 1)[0]

    assert "FROM asignaciones" in bloque_permiso
    assert "activo" not in bloque_permiso
    assert "FROM asignaciones" in bloque_resolutor
    assert "activo" not in bloque_resolutor
