"""Caracterizacion de la subcapa 7.0 del dominio `observaciones`.

Fija el comportamiento observable ANTES de cualquier extraccion: frontera con
`plan_de_clases`, entradas HTTP, permisos, status codes, semantica
transaccional, la normalizacion de las tres dimensiones y la linea base de
consultas y de conexiones.

No corrige ningun hallazgo. Varias pruebas son deliberadamente guardias de
linea base: si una extraccion posterior cambia el conteo de sentencias, el
reparto entre ruta y controlador o el numero de archivos, deben fallar y
obligar a una decision explicita.

Complementa, sin repetirlas, las **8 pruebas heredadas**:
`tests/test_observaciones_ruta.py`, 4 de la subcapa 1.4, y
`tests/test_observaciones_validaciones.py`, 4 del inventario de 0.0.
"""

import ast
import inspect
from contextlib import contextmanager
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.controllers import observacion_controller
from app.core import permissions
from app.repositories import estudiantes_repository
from app.routes import observaciones, plan_de_clases
from app.schemas.observacion import ObservacionCreate

RAIZ = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# Dobles
# --------------------------------------------------------------------------

class CursorFalso:
    def __init__(self, fila=(True,), secuencia_fetchone=None):
        # Por defecto la asignacion esta ACTIVA: es el camino normal. Pasar
        # `fila=None` simula una asignacion dada de baja.
        self.fila = fila
        self.secuencia_fetchone = list(secuencia_fetchone or [])
        self.calls = []
        self.closed = False

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        if self.secuencia_fetchone:
            return self.secuencia_fetchone.pop(0)
        return self.fila

    def close(self):
        self.closed = True


class ConexionFalsa:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self, **_kwargs):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class ContadorDeConexiones:
    """Cuenta cuantas veces se pide una conexion, sin simultanearlas."""

    def __init__(self):
        self.abiertas = 0

    def __call__(self):
        self.abiertas += 1
        return ConexionFalsa(CursorFalso(fila=(1,)))


def _sql_del_modulo(ruta_relativa):
    """Literales SQL de un modulo, extraidos por AST y no por texto."""
    arbol = ast.parse((RAIZ / ruta_relativa).read_text(encoding="utf-8"))
    literales = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        if getattr(nodo.func, "attr", None) != "execute":
            continue
        if nodo.args and isinstance(nodo.args[0], ast.Constant):
            valor = nodo.args[0].value
            if isinstance(valor, str):
                literales.append(valor)
    return literales


def _codigo_sin_docstrings(ruta_relativa):
    """Fuente de un modulo con sus docstrings retirados.

    Leccion 13 de la capa 6: sin excluirlos, la prosa que describe algo se
    cuenta como si fuera ese algo. Aqui el docstring del repositorio nombra
    `get_connection` y `get_cursor` justo para explicar que NO los usa.
    """
    fuente = (RAIZ / ruta_relativa).read_text(encoding="utf-8")
    arbol = ast.parse(fuente)

    docstrings = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            texto = ast.get_docstring(nodo, clean=False)
            if texto:
                docstrings.append(texto)

    for texto in docstrings:
        fuente = fuente.replace(texto, "")
    return fuente


def _paths_declarados(router):
    return {
        (ruta.path, tuple(sorted(ruta.methods)))
        for ruta in router.routes
        if hasattr(ruta, "methods")
    }


def _payload(**cambios):
    base = {
        "estudiante_id": 1,
        "asignacion_id": 10,
        "periodo": 2,
        "conductual": "Atento",
        "cognitivo": "",
        "lenguaje": "",
    }
    base.update(cambios)
    return base


# --------------------------------------------------------------------------
# Frontera del dominio
# --------------------------------------------------------------------------

def test_el_dominio_son_cuatro_archivos_y_sigue_sin_servicio():
    """Guardia de frontera, actualizada por 7.1.

    7.0 la dejo en tres archivos y sin repositorio. 7.1 anadio el undecimo
    repositorio del proyecto; el servicio sigue sin existir y crearlo seria otra
    decision, no un efecto colateral.

    El nombre del router va en plural y los de controlador y esquema en
    singular; el repositorio sigue al router, como la tabla. Queda fijado para
    que nadie lo "corrija" al pasar.
    """
    assert (RAIZ / "app/routes/observaciones.py").is_file()
    assert (RAIZ / "app/controllers/observacion_controller.py").is_file()
    assert (RAIZ / "app/schemas/observacion.py").is_file()
    assert (RAIZ / "app/repositories/observaciones_repository.py").is_file()

    assert not (RAIZ / "app/services/observacion_service.py").exists()


def test_el_router_declara_exactamente_las_dos_entradas_del_dominio():
    assert _paths_declarados(observaciones.router) == {
        ("/observaciones", ("POST",)),
        ("/observaciones/{estudiante_id}/{asignacion_id}/{periodo}", ("GET",)),
    }


def test_las_observaciones_de_plan_de_clases_son_otro_dominio_y_no_colisionan():
    """La trampa de frontera de esta capa.

    `plan_de_clases` tiene tres entradas con «observaciones» en el path. Son
    observaciones de planes de clase, no academicas, y **viven en otra tabla**.
    `plan_de_clases` sigue en espera: ni se toca ni se invade.
    """
    paths_plan = {
        path for path, _ in _paths_declarados(plan_de_clases.router)
        if "observacion" in path
    }
    assert paths_plan == {
        "/admin/plan-de-clases/{plan_id}/observaciones",
        "/plan-de-clases/{plan_id}/observaciones",
        "/plan-de-clases/{plan_id}/observaciones/{observacion_id}/vista",
    }

    paths_propios = {path for path, _ in _paths_declarados(observaciones.router)}
    assert paths_propios.isdisjoint(paths_plan)
    assert all(path.startswith("/observaciones") for path in paths_propios)


def test_las_dos_sentencias_viven_ahora_en_el_repositorio():
    """Linea base de SQL inline, actualizada por 7.1.

    7.0 conto **2 sentencias repartidas entre la ruta y el controlador**, y ese
    reparto era el rasgo que distinguia a este dominio. 7.1 movio **las dos** al
    repositorio: la capa HTTP se queda **sin SQL**, que es lo que resuelve el
    hallazgo 3.
    """
    en_repositorio = _sql_del_modulo("app/repositories/observaciones_repository.py")

    assert len(en_repositorio) == 3
    assert _sql_del_modulo("app/routes/observaciones.py") == []
    assert _sql_del_modulo("app/controllers/observacion_controller.py") == []
    assert _sql_del_modulo("app/schemas/observacion.py") == []

    assert any("SELECT conductual, cognitivo, lenguaje" in s for s in en_repositorio)
    assert any("INSERT INTO observaciones" in s for s in en_repositorio)


def test_el_repositorio_no_es_dueno_de_ningun_recurso():
    """Ninguna funcion del repositorio abre, cierra, confirma ni revierte.

    La propiedad de la conexion sigue **repartida entre dos capas**: la ruta en
    la lectura y el controlador en la escritura. Es lo que conserva los conteos
    que 7.0 fijo.
    """
    codigo = _codigo_sin_docstrings("app/repositories/observaciones_repository.py")
    for prohibido in ("get_connection", "get_cursor", "commit()", "rollback()", "close()"):
        assert prohibido not in codigo


def test_cada_llamador_del_repositorio_conserva_su_propia_capa():
    """La lectura lo llama desde la RUTA y la escritura desde el CONTROLADOR.

    Es deliberado: 7.1 saco el SQL de las dos capas sin mover la propiedad del
    cursor ni unificar los idiomas de conexion.
    """
    fuente_ruta = (RAIZ / "app/routes/observaciones.py").read_text(encoding="utf-8")
    fuente_ctrl = (RAIZ / "app/controllers/observacion_controller.py").read_text(encoding="utf-8")

    assert "observaciones_repository.leer_observacion(" in fuente_ruta
    assert "observaciones_repository.guardar_observacion(" not in fuente_ruta

    assert "observaciones_repository.guardar_observacion(" in fuente_ctrl
    assert "observaciones_repository.leer_observacion(" not in fuente_ctrl


def test_los_dos_caminos_conviven_con_dos_idiomas_de_conexion():
    """La ruta usa `get_cursor()`; el controlador, `get_connection()`.

    Es la misma herencia que tuvo `asistencia`. **Se conservan los dos**:
    unificarlos cambiaria los conteos que esta subcapa fija por asercion.
    """
    fuente_ruta = (RAIZ / "app/routes/observaciones.py").read_text(encoding="utf-8")
    fuente_ctrl = (RAIZ / "app/controllers/observacion_controller.py").read_text(encoding="utf-8")

    assert "get_cursor" in fuente_ruta
    assert "get_connection" not in fuente_ruta
    assert "get_connection" in fuente_ctrl
    assert "get_cursor" not in fuente_ctrl


def test_el_resolver_se_consume_desde_los_dos_lados_del_dominio():
    fuente_ruta = (RAIZ / "app/routes/observaciones.py").read_text(encoding="utf-8")
    fuente_ctrl = (RAIZ / "app/controllers/observacion_controller.py").read_text(encoding="utf-8")

    assert "resolver_asignacion_academica_id_cursor(" in fuente_ruta
    assert "resolver_asignacion_academica_id_cursor(" in fuente_ctrl


# --------------------------------------------------------------------------
# La tabla y sus ausencias
# --------------------------------------------------------------------------

def test_la_tabla_no_tiene_ninguna_clave_foranea():
    """Hallazgo registrado y NO corregido.

    `estudiante_id` y `asignacion_id` son enteros sueltos: nada en la base
    impide una observacion huerfana. La integridad depende **enteramente** del
    codigo de aplicacion. Lo unico que la tabla garantiza es la unicidad del
    trio, que es justo lo que sostiene el `UPSERT`.
    """
    ddl = (RAIZ / "migrations/base/20260813_esquema_base_tenant.sql").read_text(encoding="utf-8")
    inicio = ddl.index("CREATE TABLE IF NOT EXISTS observaciones (")
    bloque = ddl[inicio:ddl.index(");", inicio)]

    assert "REFERENCES" not in bloque
    assert "FOREIGN KEY" not in bloque
    assert "UNIQUE (estudiante_id, asignacion_id, periodo)" in bloque


def test_las_tres_dimensiones_son_text_sin_limite_a_diferencia_de_plan_de_clases():
    """Hallazgo registrado y NO corregido.

    La tabla del dominio academico esta **menos protegida** que la de
    `plan_de_clases`, que si acota el texto entre 1 y 3000 caracteres.
    """
    ddl = (RAIZ / "migrations/base/20260813_esquema_base_tenant.sql").read_text(encoding="utf-8")

    inicio = ddl.index("CREATE TABLE IF NOT EXISTS observaciones (")
    propio = ddl[inicio:ddl.index(");", inicio)]
    for columna in ("conductual text", "cognitivo text", "lenguaje text"):
        assert columna in propio
    assert "CHECK" not in propio

    inicio_plan = ddl.index("CREATE TABLE IF NOT EXISTS plan_de_clases_observaciones (")
    ajeno = ddl[inicio_plan:ddl.index(");", inicio_plan)]
    assert "length(btrim(observacion))" in ajeno


# --------------------------------------------------------------------------
# Escritura y semantica transaccional
# --------------------------------------------------------------------------

def test_guardar_observacion_hace_un_upsert_sobre_una_sola_tabla(monkeypatch):
    cursor = CursorFalso()
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(observacion_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        observacion_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _c, _a: 77,
    )

    resultado = observacion_controller.guardar_observacion_controller(_payload())

    assert resultado == {"mensaje": "Observación guardada/actualizada"}

    sentencias = [sql for sql, _ in cursor.calls]
    # Dos: la comprobacion de `activo` que anadio la correccion del hallazgo 6,
    # y el UPSERT. El resolver esta doblado en esta prueba y no emite consulta.
    assert len(sentencias) == 2
    assert "SELECT activo FROM asignaciones" in sentencias[0]
    sql = sentencias[-1]
    assert "INSERT INTO observaciones" in sql
    assert "ON CONFLICT (estudiante_id, asignacion_id, periodo)" in sql
    assert "DO UPDATE SET" in sql
    for dimension in ("conductual", "cognitivo", "lenguaje"):
        assert f"{dimension} = EXCLUDED.{dimension}" in sql

    assert conn.commits == 1
    assert conn.rollbacks == 0
    assert cursor.closed is True
    assert conn.closed is True


def test_guardar_observacion_escribe_el_asignacion_academica_id_resuelto(monkeypatch):
    cursor = CursorFalso()
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(observacion_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        observacion_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _c, _a: 77,
    )

    observacion_controller.guardar_observacion_controller(_payload(asignacion_id=10))

    _, params = cursor.calls[-1]
    assert params == (1, 77, 2, "Atento", "", "")


def test_guardar_observacion_revierte_y_propaga_el_error(monkeypatch):
    class CursorQueFalla(CursorFalso):
        def execute(self, query, params=None):
            super().execute(query, params)
            raise RuntimeError("fallo de escritura")

    cursor = CursorQueFalla()
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(observacion_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        observacion_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _c, _a: 77,
    )

    with pytest.raises(RuntimeError):
        observacion_controller.guardar_observacion_controller(_payload())

    assert conn.rollbacks == 1
    assert conn.commits == 0
    assert cursor.closed is True
    assert conn.closed is True


def test_el_upsert_no_comprueba_que_la_asignacion_siga_activa():
    """Hallazgo registrado y NO corregido, heredado de `dashboard`, `notas` y
    `boletin`: la asignacion resuelta se escribe sin mirar `activo`.

    Tras 7.1 el `UPSERT` vive en el repositorio; el hallazgo no cambia.
    """
    sql = _sql_del_modulo("app/repositories/observaciones_repository.py")
    upsert = [s for s in sql if "INSERT INTO observaciones" in s]
    assert len(upsert) == 1
    assert "activo" not in upsert[0]


# --------------------------------------------------------------------------
# Las dimensiones y el 422
# --------------------------------------------------------------------------

def test_las_tres_dimensiones_se_normalizan_recortando_espacios():
    """Esto es lo que el inventario de 0.0 llamaba «dimensiones normalizadas»."""
    data = ObservacionCreate(
        estudiante_id=1,
        asignacion_id=10,
        periodo=2,
        conductual="   Atento en clase   ",
        cognitivo="\n\tResuelve\n",
        lenguaje="   ",
    )

    assert data.conductual == "Atento en clase"
    assert data.cognitivo == "Resuelve"
    assert data.lenguaje == ""


def test_la_normalizacion_convierte_cualquier_valor_falsy_en_cadena_vacia():
    """Hallazgo registrado y NO corregido.

    `str(valor or "").strip()` no distingue tipos: un **0** numerico no llega
    como `"0"`, llega como cadena vacia, porque `0` es falsy. Lo mismo con
    `False` y con las listas vacias.
    """
    data = ObservacionCreate(
        estudiante_id=1,
        asignacion_id=10,
        periodo=2,
        conductual=0,
        cognitivo=False,
        lenguaje="Se comunica",
    )

    assert data.conductual == ""
    assert data.cognitivo == ""

    # En cambio un valor truthy si conserva su representacion.
    otro = ObservacionCreate(
        estudiante_id=1, asignacion_id=10, periodo=2, conductual=7
    )
    assert otro.conductual == "7"


def test_las_tres_dimensiones_vacias_producen_un_error_de_validacion():
    """El `422` del contrato de 0.0 lo produce el ESQUEMA, no el dominio.

    Lo lanza el `model_validator` y FastAPI lo traduce. Si esa validacion se
    moviera al controlador, el status pasaria de **422 a 500**: es fragil y
    queda anotado.
    """
    with pytest.raises(ValidationError) as exc:
        ObservacionCreate(
            estudiante_id=1, asignacion_id=10, periodo=2,
            conductual="  ", cognitivo="", lenguaje="\t",
        )

    assert "Escribe al menos una observación antes de guardar." in str(exc.value)

    fuente = (RAIZ / "app/schemas/observacion.py").read_text(encoding="utf-8")
    assert "model_validator" in fuente
    fuente_ruta = (RAIZ / "app/routes/observaciones.py").read_text(encoding="utf-8")
    assert "Escribe al menos" not in fuente_ruta


def test_el_esquema_no_acota_periodo_ni_la_longitud_del_texto():
    """Hallazgo registrado y NO corregido: `periodo` es un `int` sin cota y las
    tres dimensiones no tienen longitud maxima, ni aqui ni en la base."""
    data = ObservacionCreate(
        estudiante_id=1, asignacion_id=10, periodo=99, conductual="x" * 10000
    )

    assert data.periodo == 99
    assert len(data.conductual) == 10000


# --------------------------------------------------------------------------
# Permisos y contrato de la lectura
# --------------------------------------------------------------------------

def test_las_dos_entradas_comparten_un_unico_modelo_de_permiso():
    """`observaciones` es el segundo dominio de la capa 7 con permisos
    uniformes, despues de `ventas`: las dos entradas exigen exactamente los
    mismos tres guards."""
    fuente = (RAIZ / "app/routes/observaciones.py").read_text(encoding="utf-8")

    assert "dependencies=[Depends(get_current_user)]" in fuente
    assert fuente.count("require_asignacion_access(") == 2
    assert fuente.count("require_estudiante_in_asignacion(") == 2
    assert "get_current_active_admin" not in fuente


def test_las_dos_entradas_registran_el_fallo_y_devuelven_una_constante():
    """Sustituye a la guardia de linea base, que exigia lo contrario.

    Antes no habia `try/except` ni `logger`: la excepcion suba y el servidor ASGI
    devolvia un `Internal Server Error` en **texto plano**, sin el
    `{"detail": ...}` del resto de la API y **sin dejar ninguna traza** de la
    aplicacion. El hallazgo 7 de 7.0.
    """
    fuente = (RAIZ / "app/routes/observaciones.py").read_text(encoding="utf-8")

    assert fuente.count("except Exception:") == 2
    assert fuente.count("logger.exception(") == 2
    assert fuente.count("status_code=500") == 2

    # Las guardas de permiso siguen FUERA del `try`, y ademas se deja pasar
    # cualquier HTTPException: sin eso, un 403 se convertiria en 500.
    assert fuente.count("except HTTPException:") == 2

    # Nunca el texto de la excepcion: el frontend MUESTRA este campo al usuario.
    # Se comprueba que los dos unicos `detail=` sean las constantes; el
    # comentario del modulo menciona el otro caso para advertirlo.
    assert fuente.count("detail=") == 3
    assert "detail=_ERROR_GUARDAR" in fuente
    assert "detail=_ERROR_CONSULTAR" in fuente
    assert "detail=_ERROR_INACTIVA" in fuente


def test_el_fallo_al_guardar_sale_como_500_sin_filtrar_el_texto_interno(caplog):
    """Verificado por ASGI, con una respuesta HTTP real.

    Es la unica tecnica que observa un status code de verdad, y aqui importa
    doblemente: `Observaciones.jsx` muestra el campo `detail` **literalmente al
    usuario**, asi que si alli viajara `str(e)` un error de PostgreSQL acabaria
    en pantalla.
    """
    import asyncio
    import json
    import logging

    from fastapi import FastAPI

    from app.dependencies import get_current_user
    from app.routes import observaciones as ruta

    app = FastAPI()
    app.include_router(ruta.router)
    for r in app.router.routes:
        if getattr(r, "dependencies", None):
            r.dependencies = []
    app.dependency_overrides[get_current_user] = lambda: {"id": 7, "rol": "admin"}

    secreto = "FATAL: password authentication failed for user admin"

    def revienta(*_a, **_k):
        raise RuntimeError(secreto)

    original_guardar = ruta.guardar_observacion_controller
    original_asig = ruta.require_asignacion_access
    original_est = ruta.require_estudiante_in_asignacion
    ruta.guardar_observacion_controller = revienta
    ruta.require_asignacion_access = lambda *_a, **_k: None
    ruta.require_estudiante_in_asignacion = lambda *_a, **_k: None

    try:
        cuerpo = json.dumps(
            {"estudiante_id": 1, "asignacion_id": 2, "periodo": 1, "conductual": "x"}
        ).encode()
        mensajes = []

        async def receive():
            return {"type": "http.request", "body": cuerpo}

        async def send(m):
            mensajes.append(m)

        with caplog.at_level(logging.ERROR, logger=ruta.__name__):
            asyncio.run(
                app(
                    {
                        "type": "http", "asgi": {"version": "3.0"},
                        "http_version": "1.1", "method": "POST",
                        "path": "/observaciones", "raw_path": b"/observaciones",
                        "query_string": b"", "root_path": "", "scheme": "http",
                        "headers": [(b"content-type", b"application/json")],
                        "client": ("t", 1), "server": ("t", 80),
                    },
                    receive,
                    send,
                )
            )
    finally:
        ruta.guardar_observacion_controller = original_guardar
        ruta.require_asignacion_access = original_asig
        ruta.require_estudiante_in_asignacion = original_est

    estado = [m for m in mensajes if m["type"] == "http.response.start"]
    salida = b"".join(
        m.get("body", b"") for m in mensajes if m["type"] == "http.response.body"
    ).decode()

    assert estado and estado[0]["status"] == 500
    assert json.loads(salida) == {"detail": ruta._ERROR_GUARDAR}

    # El texto interno no llega al cliente...
    assert secreto not in salida
    assert "password" not in salida

    # ...pero si queda registrado, con su traceback.
    assert caplog.records, "el fallo debe registrarse"
    assert caplog.records[-1].exc_info is not None
    assert secreto in caplog.text


def test_los_guards_se_evaluan_antes_de_abrir_el_cursor_en_la_lectura():
    """Ya lo fijaba 1.4; aqui se fija ademas el ORDEN exacto en el codigo, para
    que una extraccion no lo invierta sin que nadie lo note."""
    fuente = inspect.getsource(observaciones.obtener_observacion)

    pos_asignacion = fuente.index("require_asignacion_access(")
    pos_estudiante = fuente.index("require_estudiante_in_asignacion(")
    pos_cursor = fuente.index("with get_cursor()")

    assert pos_asignacion < pos_estudiante < pos_cursor


def test_la_lectura_devuelve_none_y_no_un_diccionario_vacio(monkeypatch):
    """Contrato con el frontend: `200` con cuerpo `null`, ni `404` ni `{}`."""
    cursor = CursorFalso(fila=None)

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        yield cursor

    monkeypatch.setattr(observaciones, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(
        observaciones, "resolver_asignacion_academica_id_cursor", lambda _c, _a: 77
    )
    monkeypatch.setattr(observaciones, "require_asignacion_access", lambda *a, **k: None)
    monkeypatch.setattr(observaciones, "require_estudiante_in_asignacion", lambda *a, **k: None)

    resultado = observaciones.obtener_observacion(1, 10, 2, {"id": 3, "rol": "profesor"})

    assert resultado is None


# --------------------------------------------------------------------------
# Linea base de consultas y de conexiones
# --------------------------------------------------------------------------

def test_linea_base_de_consultas_de_la_lectura(monkeypatch):
    # Primera fila para el resolver, segunda para el SELECT del dominio.
    cursor = CursorFalso(secuencia_fetchone=[(77,), ("Atento", "Resuelve", "Claro")])

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        yield cursor

    monkeypatch.setattr(observaciones, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(observaciones, "require_asignacion_access", lambda *a, **k: None)
    monkeypatch.setattr(observaciones, "require_estudiante_in_asignacion", lambda *a, **k: None)

    resultado = observaciones.obtener_observacion(1, 10, 2, {"id": 3, "rol": "admin"})

    # Resolver + SELECT. El resolver NO esta doblado aqui: corre sobre el mismo
    # cursor y por eso suma.
    assert len(cursor.calls) == 2
    assert cursor.calls[1][1] == (1, 77, 2)
    assert resultado == {"conductual": "Atento", "cognitivo": "Resuelve", "lenguaje": "Claro"}


def test_linea_base_de_consultas_de_la_escritura(monkeypatch):
    cursor = CursorFalso(fila=(77,))
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(observacion_controller, "get_connection", lambda: conn)

    observacion_controller.guardar_observacion_controller(_payload())

    # Resolver + comprobacion de `activo` + UPSERT, los tres sobre el mismo
    # cursor. Eran dos hasta el 2026-08-27: la comprobacion la anadio la
    # correccion del hallazgo 6.
    assert len(cursor.calls) == 3


def test_linea_base_de_conexiones_por_entrada(monkeypatch):
    """El dominio NO tiene N+1 en conexiones: los dos guards se llaman una vez
    cada uno, fuera de todo bucle, y el coste no crece con nada.

    Pero **son dos guards**, el doble que `boletines`, asi que el suelo es mas
    alto: 2 conexiones como admin y 3 como profesor, en las DOS entradas.
    """
    contador = ContadorDeConexiones()
    monkeypatch.setattr(permissions, "get_connection", contador)

    # Admin: `require_asignacion_access` retorna antes de conectar.
    permissions.require_asignacion_access(10, {"rol": "admin", "id": 1})
    assert contador.abiertas == 0

    permissions.require_estudiante_in_asignacion(1, 10)
    assert contador.abiertas == 1

    # Profesor: si conecta para comprobar la asignacion.
    permissions.require_asignacion_access(10, {"rol": "profesor", "id": 7})
    assert contador.abiertas == 2


def test_la_escritura_abre_exactamente_una_conexion(monkeypatch):
    contador = ContadorDeConexiones()
    monkeypatch.setattr(observacion_controller, "get_connection", contador)
    monkeypatch.setattr(
        observacion_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _c, _a: 77,
    )

    observacion_controller.guardar_observacion_controller(_payload())
    assert contador.abiertas == 1


# --------------------------------------------------------------------------
# Consumidor ajeno ya migrado
# --------------------------------------------------------------------------

def test_estudiantes_repository_lee_esta_tabla_y_su_contrato_debe_seguir_pasando():
    """`estudiantes_repository` la lee desde el bloque del expediente.

    Romper su contrato **no haria fallar las pruebas de este dominio**, solo la
    compuerta global. Por eso hay que ejecutarla siempre completa.
    """
    assert hasattr(estudiantes_repository, "leer_observaciones")

    sql = _sql_del_modulo("app/repositories/estudiantes_repository.py")
    lecturas = [s for s in sql if "FROM observaciones o" in s]
    assert len(lecturas) == 1
    assert "ORDER BY o.periodo DESC" in lecturas[0]


def test_no_se_puede_escribir_contra_una_asignacion_dada_de_baja(monkeypatch):
    """Hallazgo 6, corregido el 2026-08-27.

    Desactivar una asignacion es su baja real: el proyecto nunca borra esa fila
    porque el historial academico cuelga de ella. Escribir observaciones nuevas
    ahi equivalia a escribir en una clase eliminada.
    """
    cursor = CursorFalso(fila=None)  # `activo` no devuelve fila: dada de baja
    conn = ConexionFalsa(cursor)
    monkeypatch.setattr(observacion_controller, "get_connection", lambda: conn)
    monkeypatch.setattr(
        observacion_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _c, _a: 77,
    )

    with pytest.raises(observacion_controller.AsignacionInactivaError):
        observacion_controller.guardar_observacion_controller(_payload())

    # No se escribio nada y la transaccion se revirtio.
    sentencias = [sql for sql, _ in cursor.calls]
    assert not any("INSERT INTO observaciones" in sql for sql in sentencias)
    assert conn.commits == 0
    assert conn.rollbacks == 1
    assert conn.closed is True


def test_la_asignacion_inactiva_sale_como_403_y_no_como_500():
    """El rechazo es un permiso, no un fallo del servidor.

    Sin la clase de error propia caeria en el `except Exception` y saldria como
    500. Por eso el hallazgo 7 se corrigio antes que este.
    """
    fuente = (RAIZ / "app/routes/observaciones.py").read_text(encoding="utf-8")

    assert "except AsignacionInactivaError:" in fuente
    assert "status_code=403, detail=_ERROR_INACTIVA" in fuente

    # Va ANTES del manejador generico, o nunca se alcanzaria.
    assert fuente.index("except AsignacionInactivaError:") < fuente.index("except Exception:")


def test_la_lectura_no_bloquea_las_asignaciones_dadas_de_baja():
    """Decision deliberada: solo se bloquea la escritura.

    Consultar una observacion antigua de una asignacion ya dada de baja es
    legitimo; bloquearlo esconderia historial.
    """
    fuente = (RAIZ / "app/repositories/observaciones_repository.py").read_text(encoding="utf-8")
    ruta = (RAIZ / "app/routes/observaciones.py").read_text(encoding="utf-8")

    assert "def asignacion_esta_activa(" in fuente
    # La ruta de lectura no la llama: solo la usa el controlador de escritura.
    assert "asignacion_esta_activa" not in ruta
