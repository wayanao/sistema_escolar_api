"""Caracterizacion de las subcapas 7.0 y 7.1 de ``planilla``.

Complementa las diez pruebas de ``test_planilla_controlador.py`` y las dos del
servicio en ``test_servicios_validacion.py``. Esas pruebas fijan la transaccion
y el armado del JSON; este archivo fija la frontera, el contrato HTTP real, la
estructura de la frontera de persistencia y los conteos de consultas y
conexiones a traves de las rutas.

Nada de lo observado se corrige aqui. Varias aserciones preservan rarezas o
defectos para impedir que una extraccion posterior cambie el comportamiento sin
una decision explicita.
"""

import ast
import asyncio
import json
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.controllers import boletin_controller
from app.controllers import planilla_controller, planilla_excel_controller
from app.core import permissions
from app.dependencies import get_current_user
from app.routes import notas as ruta_notas
from app.routes import planilla as ruta_planilla
from app.schemas.planilla import NotaPlanillaCreate
from app.services import planilla_service


RAIZ = Path(__file__).resolve().parents[1]
ADMIN = {"id": 7, "rol": "admin", "tenant": "tenant_demo"}
PROFESOR = {"id": 7, "rol": "profesor", "tenant": "tenant_demo"}
ESTUDIANTE = {"id": 11, "rol": "estudiante", "tenant": "tenant_demo"}
# Año lectivo, paso 3.7: la guardia de escritura lee el año de la clase, la
# primera consulta de cada guardado. Aqui se cuenta como las demas.
SQL_GUARDIA = "SELECT al.anio, al.estado"

DATOS = NotaPlanillaCreate(
    estudiante_id=11,
    asignacion_id=12,
    periodo=2,
    nota=4.5,
    descripcion="Parcial 1",
)

PALABRAS_SQL = ("SELECT", "INSERT", "UPDATE", "DELETE", "WITH ")


def _literales_sql(ruta_relativa):
    """Devuelve literales SQL sin contar docstrings."""
    arbol = ast.parse((RAIZ / ruta_relativa).read_text(encoding="utf-8"))
    docstrings = set()
    for nodo in ast.walk(arbol):
        if isinstance(
            nodo,
            (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            texto = ast.get_docstring(nodo, clean=False)
            if texto:
                docstrings.add(texto)

    return [
        nodo.value
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant)
        and isinstance(nodo.value, str)
        and nodo.value not in docstrings
        and any(palabra in nodo.value.upper() for palabra in PALABRAS_SQL)
    ]


def _literales_sql_de_funcion(ruta_relativa, nombre):
    arbol = ast.parse((RAIZ / ruta_relativa).read_text(encoding="utf-8"))
    funcion = next(
        nodo
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.FunctionDef) and nodo.name == nombre
    )
    return [
        nodo.value
        for nodo in ast.walk(funcion)
        if isinstance(nodo, ast.Constant)
        and isinstance(nodo.value, str)
        and any(palabra in nodo.value.upper() for palabra in PALABRAS_SQL)
    ]


def _rutas(router):
    return {
        (metodo, ruta.path)
        for ruta in router.routes
        for metodo in ruta.methods
    }


class CursorInstrumentado:
    def __init__(self, registro):
        self.registro = registro

    def execute(self, query, params=None):
        self.registro.consultas.append((query, params))

    def fetchone(self):
        # La guardia del año lectivo ve 2026 activo sin gastar las filas.
        ultima = self.registro.consultas[-1][0] if self.registro.consultas else ""
        if SQL_GUARDIA in ultima:
            return (2026, "activo")
        if not self.registro.filas:
            return None
        return self.registro.filas.pop(0)

    def fetchall(self):
        return list(self.registro.filas_excel)

    def close(self):
        pass


@pytest.fixture
def instrumentado(monkeypatch):
    """Instrumenta los tres caminos sin abrir PostgreSQL."""

    def instalar(*, filas=(), filas_excel=(), permiso_ok=True):
        registro = SimpleNamespace(
            filas=list(filas),
            filas_excel=list(filas_excel),
            consultas=[],
            cursores=[],
            conexiones_permiso=0,
            consultas_permiso=[],
        )

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            registro.cursores.append(commit)
            yield CursorInstrumentado(registro)

        for modulo in (
            planilla_controller,
            planilla_excel_controller,
            planilla_service,
        ):
            monkeypatch.setattr(modulo, "get_cursor", fake_get_cursor)

        class CursorPermiso:
            def execute(self, query, params=None):
                registro.consultas_permiso.append((query, params))

            def fetchone(self):
                return (1,) if permiso_ok else None

            def close(self):
                pass

        class ConexionPermiso:
            def cursor(self):
                return CursorPermiso()

            def close(self):
                pass

        def fake_get_connection():
            registro.conexiones_permiso += 1
            return ConexionPermiso()

        monkeypatch.setattr(permissions, "get_connection", fake_get_connection)
        return registro

    return instalar


# ---------------------------------------------------------------------------
# Frontera y guardias estructurales de la extraccion
# ---------------------------------------------------------------------------


def test_la_frontera_ejecutable_propia_son_seis_archivos():
    archivos = {
        archivo.relative_to(RAIZ).as_posix()
        for archivo in (RAIZ / "app").rglob("*planilla*.py")
    }

    assert archivos == {
        "app/controllers/planilla_controller.py",
        "app/controllers/planilla_excel_controller.py",
        "app/repositories/planilla_repository.py",
        "app/routes/planilla.py",
        "app/schemas/planilla.py",
        "app/services/planilla_service.py",
    }


def test_el_router_propio_declara_exactamente_tres_entradas():
    assert _rutas(ruta_planilla.router) == {
        ("POST", "/planilla/nota"),
        ("GET", "/planilla-excel/{asignacion_id}/{periodo}"),
        ("DELETE", "/planilla/tipo"),
    }


def test_la_lectura_planilla_por_asignacion_sigue_perteneciendo_a_notas():
    assert ("GET", "/planilla/{asignacion_id}") in _rutas(ruta_notas.router)
    assert ruta_notas.planilla_asignacion_controller.__module__ == (
        "app.controllers.notas_controller"
    )
    assert _rutas(ruta_planilla.router).isdisjoint(_rutas(ruta_notas.router))


def test_el_helper_de_boletin_es_un_sexto_sql_fuera_de_la_frontera_propia():
    nombre = "obtener_notas_planilla_controller"
    assert hasattr(boletin_controller, nombre)
    assert len(
        _literales_sql_de_funcion(
            "app/controllers/boletin_controller.py",
            nombre,
        )
    ) == 1

    propios = (
        "app/routes/planilla.py",
        "app/controllers/planilla_controller.py",
        "app/controllers/planilla_excel_controller.py",
        "app/repositories/planilla_repository.py",
        "app/services/planilla_service.py",
    )
    assert all(
        nombre not in (RAIZ / archivo).read_text(encoding="utf-8")
        for archivo in propios
    )


def test_las_cinco_sentencias_viven_solo_en_el_repositorio():
    assert _literales_sql("app/routes/planilla.py") == []
    assert _literales_sql("app/controllers/planilla_controller.py") == []
    assert _literales_sql("app/controllers/planilla_excel_controller.py") == []
    assert _literales_sql("app/services/planilla_service.py") == []
    assert len(_literales_sql("app/repositories/planilla_repository.py")) == 5


def test_el_repositorio_de_planilla_es_el_duodecimo():
    repositorios = {
        archivo.stem
        for archivo in (RAIZ / "app" / "repositories").glob("*_repository.py")
    }

    assert repositorios == {
        "admisiones_repository",
        "anios_lectivos_repository",
        "asignaciones_repository",
        "asistencia_repository",
        "boletin_repository",
        "branding_repository",
        "dashboard_repository",
        "estudiantes_repository",
        "listas_seguimiento_repository",
        "notas_repository",
        "observaciones_repository",
        "observador_repository",
        "pagos_repository",
        "plan_de_clases_repository",
        "planeador_anual_repository",
        "planilla_repository",
        "profesores_repository",
        "reportes_repository",
        "super_admin_repository",
        "ventas_repository",
    }


def test_las_cinco_funciones_publicas_reciben_el_cursor():
    arbol = ast.parse(
        (RAIZ / "app/repositories/planilla_repository.py").read_text(
            encoding="utf-8"
        )
    )
    funciones = {
        nodo.name: nodo
        for nodo in arbol.body
        if isinstance(nodo, ast.FunctionDef) and not nodo.name.startswith("_")
    }

    assert set(funciones) == {
        "borrar_nota_existente",
        "buscar_estudiante_en_asignacion",
        "eliminar_tipo",
        "insertar_nota",
        "leer_filas_de_planilla",
    }
    assert all(funcion.args.args[0].arg == "cursor" for funcion in funciones.values())


def test_el_repositorio_no_es_dueno_de_recursos():
    arbol = ast.parse(
        (RAIZ / "app/repositories/planilla_repository.py").read_text(
            encoding="utf-8"
        )
    )
    assert not any(isinstance(nodo, (ast.Import, ast.ImportFrom)) for nodo in arbol.body)

    llamadas = {
        nodo.func.attr
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
    }
    assert llamadas.isdisjoint({"commit", "rollback", "close"})


def test_la_unica_tabla_escrita_es_notas_detalle():
    escrituras = [
        literal
        for literal in _literales_sql("app/repositories/planilla_repository.py")
        if literal.lstrip().upper().startswith(("DELETE", "INSERT", "UPDATE"))
    ]

    assert len(escrituras) == 3
    assert all("notas_detalle" in sentencia for sentencia in escrituras)


def test_notas_detalle_no_respalda_el_reemplazo_con_una_restriccion_unica():
    ddl = (
        RAIZ / "migrations/base/20260813_esquema_base_tenant.sql"
    ).read_text(encoding="utf-8")
    tabla = ddl.split("CREATE TABLE IF NOT EXISTS notas_detalle (", 1)[1]
    tabla = tabla.split("CREATE TABLE IF NOT EXISTS observaciones (", 1)[0]

    assert "UNIQUE" not in tabla
    assert "periodo integer DEFAULT 1" in tabla
    assert "periodo integer NOT NULL" not in tabla
    assert "descripcion character varying(100)" in tabla
    assert "notas_detalle_asignacion_id_fkey" in ddl
    assert "notas_detalle_estudiante_id_fkey" in ddl


def test_las_tres_entradas_delegan_el_mismo_permiso_y_su_controlador(
    monkeypatch,
):
    permisos = []
    monkeypatch.setattr(
        ruta_planilla,
        "require_asignacion_access",
        lambda asignacion_id, usuario: permisos.append((asignacion_id, usuario)),
    )
    monkeypatch.setattr(
        ruta_planilla,
        "registrar_nota_planilla_controller",
        lambda data, usuario: ("post", data.asignacion_id),
    )
    monkeypatch.setattr(
        ruta_planilla,
        "planilla_excel_controller",
        lambda asignacion_id, periodo: ("get", asignacion_id, periodo),
    )
    monkeypatch.setattr(
        ruta_planilla,
        "eliminar_tipo_controller",
        lambda asignacion_id, descripcion, periodo, usuario: (
            "delete",
            asignacion_id,
            descripcion,
            periodo,
        ),
    )

    assert ruta_planilla.registrar_nota(DATOS, ADMIN) == ("post", 12)
    assert ruta_planilla.planilla_excel(12, 2, ADMIN) == ("get", 12, 2)
    assert ruta_planilla.eliminar_tipo(12, "Parcial 1", 3, ADMIN) == (
        "delete",
        12,
        "Parcial 1",
        3,
    )
    assert permisos == [(12, ADMIN), (12, ADMIN), (12, ADMIN)]


def test_ninguna_entrada_declara_response_model():
    assert len(ruta_planilla.router.routes) == 3
    assert all(ruta.response_model is None for ruta in ruta_planilla.router.routes)


# ---------------------------------------------------------------------------
# Esquema de entrada
# ---------------------------------------------------------------------------


def test_el_esquema_conserva_defaults_y_nota_opcional():
    modelo = NotaPlanillaCreate(
        estudiante_id=11,
        asignacion_id=12,
        descripcion="Ensayo",
    )

    assert modelo.model_dump() == {
        "estudiante_id": 11,
        "asignacion_id": 12,
        "nota": None,
        "descripcion": "Ensayo",
        "periodo": 1,
        "tipo_evaluacion": "numerica",
        "valoracion": None,
    }


@pytest.mark.parametrize("nota", [0.99, 5.01])
def test_el_esquema_rechaza_notas_fuera_de_uno_a_cinco(nota):
    with pytest.raises(ValidationError):
        NotaPlanillaCreate(
            estudiante_id=11,
            asignacion_id=12,
            nota=nota,
            descripcion="Parcial",
        )


def test_el_esquema_permite_periodo_nulo_textos_vacios_y_tipo_desconocido():
    modelo = NotaPlanillaCreate(
        estudiante_id=11,
        asignacion_id=12,
        nota=None,
        descripcion="",
        periodo=None,
        tipo_evaluacion="otro",
        valoracion="",
    )

    assert modelo.periodo is None
    assert modelo.descripcion == ""
    assert modelo.tipo_evaluacion == "otro"
    assert modelo.valoracion == ""


# ---------------------------------------------------------------------------
# Linea base de consultas y conexiones a traves de las rutas
# ---------------------------------------------------------------------------


def test_post_como_admin_cuesta_cinco_consultas_y_una_conexion(
    instrumentado,
):
    """La funcionalidad de nivel academico agrega una consulta de solo lectura
    dentro de la MISMA conexion/transaccion ya abierta -no abre una conexion
    nueva- para saber si el curso es preescolar o primaria. El conteo sube de
    cuatro a cinco; las conexiones no cambian.

    Desde el 2026-09-24 la validacion del estudiante tambien viaja en esa
    conexion: eran dos, ahora es una. Las cinco consultas son las mismas.

    Año lectivo, paso 3.7: la guardia de escritura suma una sexta, la primera,
    en la misma conexion."""
    registro = instrumentado(filas=[(11,), (77,), (None,), (901,)])

    respuesta = ruta_planilla.registrar_nota(DATOS, ADMIN)

    assert registro.cursores == [True]
    assert registro.conexiones_permiso == 0
    assert len(registro.consultas) == 6
    assert SQL_GUARDIA in registro.consultas[0][0]
    assert len(registro.cursores) + registro.conexiones_permiso == 1
    assert respuesta == {
        "mensaje": "Nota registrada correctamente",
        "nota_id": 901,
    }


def test_post_como_profesor_cuesta_seis_consultas_y_dos_conexiones(
    instrumentado,
):
    """La segunda conexion es la del permiso de la asignacion, que sigue
    comprobandose en la ruta como en las otras dos entradas del router."""
    registro = instrumentado(filas=[(11,), (77,), (None,), (901,)])

    ruta_planilla.registrar_nota(DATOS, PROFESOR)

    assert registro.cursores == [True]
    assert registro.conexiones_permiso == 1
    # Cinco del guardado mas la guardia del año lectivo (paso 3.7).
    assert len(registro.consultas) == 6
    assert len(registro.consultas_permiso) == 1
    assert len(registro.cursores) + registro.conexiones_permiso == 2


def test_post_rechazado_abre_una_conexion_y_responde_error_con_200_logico(
    instrumentado,
):
    registro = instrumentado(filas=[None])

    respuesta = ruta_planilla.registrar_nota(DATOS, ADMIN)

    assert registro.cursores == [True]
    # La guardia del año lectivo (paso 3.7) va primero, y luego la validacion.
    assert len(registro.consultas) == 2
    assert respuesta == {"error": "El estudiante no pertenece a esta asignación"}


# Año lectivo, paso 3.7: la guardia suma una consulta y ninguna conexion
# (antes 2 y 3).
@pytest.mark.parametrize(
    "usuario,consultas,conexiones",
    [(ADMIN, 3, 1), (PROFESOR, 4, 2)],
)
def test_delete_tiene_coste_constante_y_confirma_una_transaccion(
    instrumentado,
    usuario,
    consultas,
    conexiones,
):
    registro = instrumentado(filas=[(77,)])

    respuesta = ruta_planilla.eliminar_tipo(12, "Parcial 1", 2, usuario)

    assert registro.cursores == [True]
    assert len(registro.consultas) + len(registro.consultas_permiso) == consultas
    assert len(registro.cursores) + registro.conexiones_permiso == conexiones
    assert respuesta == {"mensaje": "Tipo eliminado correctamente"}


@pytest.mark.parametrize(
    "usuario,numero_estudiantes,consultas,conexiones",
    [
        (ADMIN, 1, 2, 1),
        (ADMIN, 3, 2, 1),
        (PROFESOR, 1, 3, 2),
        (PROFESOR, 3, 3, 2),
    ],
)
def test_excel_no_tiene_n_mas_un_en_consultas_ni_conexiones(
    instrumentado,
    usuario,
    numero_estudiantes,
    consultas,
    conexiones,
):
    filas_excel = [
        (
            indice,
            f"Nombre {indice}",
            f"Apellido {indice}",
            "Matematicas",
            "Parcial 1",
            4.0,
            "numerica",
            None,
            indice,
        )
        for indice in range(1, numero_estudiantes + 1)
    ]
    registro = instrumentado(filas=[(77,)], filas_excel=filas_excel)

    respuesta = ruta_planilla.planilla_excel(12, 2, usuario)

    assert registro.cursores == [False]
    assert len(registro.consultas) + len(registro.consultas_permiso) == consultas
    assert len(registro.cursores) + registro.conexiones_permiso == conexiones
    assert len(respuesta["data"]) == numero_estudiantes


# ---------------------------------------------------------------------------
# Contrato HTTP real por ASGI
# ---------------------------------------------------------------------------


def _peticion_asgi(aplicacion, metodo, ruta, cuerpo=None, query_string=""):
    crudo = json.dumps(cuerpo).encode() if cuerpo is not None else b""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1",
        "method": metodo,
        "scheme": "http",
        "path": ruta,
        "raw_path": ruta.encode(),
        "query_string": query_string.encode(),
        "root_path": "",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"content-length", str(len(crudo)).encode()),
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    salida = {"status": None, "body": b""}

    async def receive():
        return {"type": "http.request", "body": crudo, "more_body": False}

    async def send(mensaje):
        if mensaje["type"] == "http.response.start":
            salida["status"] = mensaje["status"]
        elif mensaje["type"] == "http.response.body":
            salida["body"] += mensaje.get("body", b"")

    asyncio.run(aplicacion(scope, receive, send))
    return salida["status"], json.loads(salida["body"].decode())


@pytest.fixture
def app_http(monkeypatch):
    from app.main import app

    monkeypatch.setattr(
        ruta_planilla,
        "registrar_nota_planilla_controller",
        lambda data, usuario: {
            "mensaje": "Nota registrada correctamente",
            "nota_id": 901,
        },
    )
    monkeypatch.setattr(
        ruta_planilla,
        "planilla_excel_controller",
        lambda asignacion_id, periodo: {
            "columnas": ["Parcial 1"],
            "data": [{"estudiante_id": 11, "promedio": 4.5}],
        },
    )
    monkeypatch.setattr(
        ruta_planilla,
        "eliminar_tipo_controller",
        lambda asignacion_id, descripcion, periodo, usuario: {
            "mensaje": "Tipo eliminado correctamente"
        },
    )

    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        yield app
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.parametrize(
    "metodo,ruta,query,cuerpo,estado,respuesta",
    [
        (
            "POST",
            "/planilla/nota",
            "",
            {
                "estudiante_id": 11,
                "asignacion_id": 12,
                "nota": 4.5,
                "descripcion": "Parcial 1",
                "periodo": 2,
            },
            200,
            {"mensaje": "Nota registrada correctamente", "nota_id": 901},
        ),
        (
            "GET",
            "/planilla-excel/12/2",
            "",
            None,
            200,
            {
                "columnas": ["Parcial 1"],
                "data": [{"estudiante_id": 11, "promedio": 4.5}],
            },
        ),
        (
            "DELETE",
            "/planilla/tipo",
            "asignacion_id=12&descripcion=Parcial%201&periodo=3",
            None,
            200,
            {"mensaje": "Tipo eliminado correctamente"},
        ),
    ],
)
def test_http_conserva_status_y_payload_de_los_tres_caminos(
    app_http,
    metodo,
    ruta,
    query,
    cuerpo,
    estado,
    respuesta,
):
    estado_real, cuerpo_real = _peticion_asgi(
        app_http,
        metodo,
        ruta,
        cuerpo,
        query,
    )

    assert estado_real == estado
    assert cuerpo_real == respuesta


def test_http_validacion_interna_fallida_sigue_respondiendo_200(
    app_http,
    monkeypatch,
):
    monkeypatch.setattr(
        ruta_planilla,
        "registrar_nota_planilla_controller",
        lambda data, usuario: {"error": "El estudiante no pertenece a esta asignación"},
    )

    estado, cuerpo = _peticion_asgi(
        app_http,
        "POST",
        "/planilla/nota",
        {
            "estudiante_id": 11,
            "asignacion_id": 12,
            "nota": 4.5,
            "descripcion": "Parcial 1",
        },
    )

    assert estado == 200
    assert cuerpo == {"error": "El estudiante no pertenece a esta asignación"}


def test_http_nota_fuera_de_rango_responde_422(app_http):
    estado, cuerpo = _peticion_asgi(
        app_http,
        "POST",
        "/planilla/nota",
        {
            "estudiante_id": 11,
            "asignacion_id": 12,
            "nota": 5.1,
            "descripcion": "Parcial 1",
        },
    )

    assert estado == 422
    assert cuerpo["detail"][0]["loc"] == ["body", "nota"]


def test_http_delete_sin_descripcion_responde_422(app_http):
    estado, cuerpo = _peticion_asgi(
        app_http,
        "DELETE",
        "/planilla/tipo",
        query_string="asignacion_id=12&periodo=1",
    )

    assert estado == 422
    assert cuerpo["detail"][0]["loc"] == ["query", "descripcion"]


def test_http_propaga_el_403_del_permiso(app_http):
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: ESTUDIANTE
    try:
        estado, cuerpo = _peticion_asgi(
            app_http,
            "GET",
            "/planilla-excel/12/2",
        )
    finally:
        app.dependency_overrides[get_current_user] = lambda: ADMIN

    assert estado == 403
    assert cuerpo == {"detail": "No autorizado"}
