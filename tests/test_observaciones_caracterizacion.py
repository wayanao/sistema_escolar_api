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
    def __init__(self, fila=None, secuencia_fetchone=None):
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

def test_el_dominio_son_tres_archivos_y_no_tiene_repositorio_ni_servicio():
    """Guardia de frontera. `observaciones` llega sin repositorio propio; que
    aparezca uno es trabajo de 7.1 y debe ser una decision, no un efecto
    colateral.

    El nombre del router va en plural y los de controlador y esquema en
    singular; queda fijado para que nadie lo "corrija" al pasar.
    """
    assert (RAIZ / "app/routes/observaciones.py").is_file()
    assert (RAIZ / "app/controllers/observacion_controller.py").is_file()
    assert (RAIZ / "app/schemas/observacion.py").is_file()

    assert not (RAIZ / "app/repositories/observaciones_repository.py").exists()
    assert not (RAIZ / "app/repositories/observacion_repository.py").exists()
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


def test_las_dos_sentencias_del_dominio_y_una_vive_en_la_capa_http():
    """Linea base de SQL inline, y **el rasgo que distingue a este dominio**.

    Es el primero de la capa 7 con persistencia en la ruta. Contar el SQL solo
    en el controlador daria un inventario falso: daria 1 de 2.
    """
    en_ruta = _sql_del_modulo("app/routes/observaciones.py")
    en_controlador = _sql_del_modulo("app/controllers/observacion_controller.py")

    assert len(en_ruta) == 1
    assert len(en_controlador) == 1
    assert _sql_del_modulo("app/schemas/observacion.py") == []

    assert "SELECT conductual, cognitivo, lenguaje" in en_ruta[0]
    assert "INSERT INTO observaciones" in en_controlador[0]


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
    assert len(sentencias) == 1
    sql = sentencias[0]
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

    _, params = cursor.calls[0]
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
    `boletin`: la asignacion resuelta se escribe sin mirar `activo`."""
    sql = _sql_del_modulo("app/controllers/observacion_controller.py")[0]
    assert "activo" not in sql


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


def test_ninguna_de_las_dos_entradas_envuelve_el_fallo_en_un_try():
    """Contraste con `boletin`, que mapeaba todo a 500 con mensaje fijo.

    Aqui no hay `try/except` en la capa HTTP: una excepcion sube y FastAPI la
    convierte en un 500 generico. **No se filtra el texto de la excepcion**,
    pero tampoco se registra nada.
    """
    fuente = (RAIZ / "app/routes/observaciones.py").read_text(encoding="utf-8")

    assert "try:" not in fuente
    assert "HTTPException" not in fuente
    assert "logger" not in fuente


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

    # Resolver + UPSERT, ambos sobre el mismo cursor.
    assert len(cursor.calls) == 2


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
