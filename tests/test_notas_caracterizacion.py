"""Caracterizacion de la subcapa 7.0 del dominio `notas`.

Complementa lo que ya existe y no lo repite. `test_notas_controlador.py`, de la
subcapa 1.4h, fija los calculos del controlador; `test_notas_permissions.py`
fija la delegacion de permisos de tres de las cinco entradas.

Lo que ninguno de los dos toca, y este archivo fija:

- las guardias estructurales de la linea base previa a cualquier extraccion;
- el contrato HTTP real de `POST /notas`, la unica entrada que escribe;
- los conteos de consultas y de conexiones medidos **a traves de la ruta**,
  incluida la capa de permisos, que es la unica forma de ver el coste real;
- `app/services/nota_service.py`, que no tenia ninguna cobertura;
- la formula de promedio de este dominio, que es la **cuarta** del sistema;
- el tratamiento de `periodo`, que la escritura no fija y solo una lectura filtra.

Nada de lo que aqui se fija se corrige: 7.0 inventaria y caracteriza, no arregla.
Varias de estas pruebas documentan comportamiento que parece defectuoso; se
fijan tal como estan hoy para que una extraccion posterior no los cambie sin que
alguien lo note.
"""

import ast
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.controllers import notas_controller
from app.core import permissions
from app.routes import notas as ruta_notas
from app.services import nota_service

RAIZ = Path(__file__).resolve().parents[1]

NOTA = SimpleNamespace(asignacion_id=12, estudiante_id=11, nota=4.2, descripcion="Parcial 1")
ADMIN = {"id": 7, "rol": "admin", "tenant": "tenant_demo"}
PROFESOR = {"id": 7, "rol": "profesor", "tenant": "tenant_demo"}


@pytest.fixture(autouse=True)
def guardia_del_anio(monkeypatch):
    """Año lectivo, paso 3.7: la guardia de escritura se dobla aqui, igual que
    el resolutor de la asignacion academica, asi que no suma en los conteos de
    este archivo (en produccion es una consulta mas; la cuenta
    `test_anio_lectivo_guardia_conteos.py`). Sus pruebas viven en
    `test_anio_lectivo_guardia.py`; aqui solo se anota a quien se le pidio."""
    llamadas = []
    monkeypatch.setattr(
        notas_controller,
        "exigir_asignacion_editable",
        lambda _cursor, asignacion_id, usuario: llamadas.append((asignacion_id, usuario)),
    )
    return llamadas

PALABRAS_SQL = ("SELECT", "INSERT", "UPDATE", "DELETE", "WITH ")


def _literales_sql(ruta_relativa):
    """Literales de cadena con SQL, excluyendo docstrings.

    Excluir docstrings es la leccion 13 de la capa 6: sin ella, la prosa que
    describe una consulta se cuenta como si fuera la consulta.
    """
    arbol = ast.parse((RAIZ / ruta_relativa).read_text(encoding="utf-8"))

    docstrings = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            texto = ast.get_docstring(nodo, clean=False)
            if texto:
                docstrings.add(texto)

    literales = {
        nodo.value
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)
    }
    return {
        literal
        for literal in literales - docstrings
        if any(palabra in literal.upper() for palabra in PALABRAS_SQL)
    }


def _puntos_de_ejecucion(ruta_relativa):
    arbol = ast.parse((RAIZ / ruta_relativa).read_text(encoding="utf-8"))
    return [
        nodo
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
        and nodo.func.attr == "execute"
    ]


class CursorInstrumentado:
    """Cursor doble que registra cada consulta y devuelve resultados en orden."""

    def __init__(self, resultados=(), fila=None):
        self.resultados = list(resultados)
        self.fila = fila
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.fila

    def fetchall(self):
        return self.resultados.pop(0) if self.resultados else []

    def close(self):
        pass


@pytest.fixture
def instrumentado(monkeypatch):
    """Instrumenta el dominio entero para medirlo a traves de la ruta.

    Cuenta por separado las conexiones que abre la capa de permisos y las que
    abren el controlador y su servicio. Medir solo el controlador escondería el
    coste de las validaciones, que es donde esta el grueso de este dominio.
    """

    def instalar(resultados=(), fila=(501,), asignacion_resuelta=77, permiso_ok=True):
        registro = SimpleNamespace(
            cursores=[], conexiones_permiso=0, consultas_permiso=[]
        )
        cursor = CursorInstrumentado(resultados=resultados, fila=fila)

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            registro.cursores.append(commit)
            yield cursor

        monkeypatch.setattr(notas_controller, "get_cursor", fake_get_cursor)
        monkeypatch.setattr(nota_service, "get_cursor", fake_get_cursor)
        monkeypatch.setattr(
            notas_controller,
            "resolver_asignacion_academica_id_cursor",
            lambda _cursor, asignacion_id: asignacion_resuelta,
        )

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

        registro.cursor = cursor
        return registro

    return instalar


# ---------------------------------------------------------------------------
# Bloque 1 — guardias estructurales
#
# Las tres primeras describian en 7.0 el estado ANTERIOR a la extraccion y
# **fallaron al ejecutarse 7.1**, que era la señal esperada: una guardia que no
# puede fallar no esta protegiendo nada. Es la leccion 14 de la capa 6, aplicada
# por tercera vez en el programa. Aqui estan ya en su version positiva.
# ---------------------------------------------------------------------------


def test_el_repositorio_de_notas_es_el_septimo():
    repositorios = {p.stem for p in (RAIZ / "app" / "repositories").glob("*_repository.py")}

    assert repositorios == {
        "admisiones_repository",
        "anios_lectivos_repository",
        "asignaciones_repository",
        "asistencia_repository",
        "boletin_repository",
        "branding_repository",
        "cuadros_plan_de_clases_repository",
        "dashboard_repository",
        # «Mi curso» del director de grupo (2026-11-07): solo lee.
        "director_grupo_repository",
        "estudiantes_repository",
        "listas_seguimiento_repository",
        "notas_repository",
        "observaciones_repository",
        "observador_repository",
        "pagos_repository",
        "plan_de_clases_repository",
        "planeador_anual_repository",
        "planilla_repository",
        "porcentajes_planilla_repository",
        "profesores_repository",
        "reportes_repository",
        "subnotas_planilla_repository",
        "super_admin_repository",
        "ventas_repository",
    }


def test_el_sql_del_dominio_vive_solo_en_el_repositorio():
    """Las 9 sentencias salieron del controlador y del servicio, intactas."""
    for modulo in (
        "app/controllers/notas_controller.py",
        "app/services/nota_service.py",
        "app/routes/notas.py",
    ):
        assert _literales_sql(modulo) == set(), modulo
        assert _puntos_de_ejecucion(modulo) == [], modulo

    assert len(_literales_sql("app/repositories/notas_repository.py")) == 9
    assert len(_puntos_de_ejecucion("app/repositories/notas_repository.py")) == 9


def test_las_nueve_funciones_publicas_reciben_el_cursor():
    import inspect

    from app.repositories import notas_repository

    publicas = {
        nombre: funcion
        for nombre, funcion in inspect.getmembers(notas_repository, inspect.isfunction)
        if not nombre.startswith("_")
    }

    assert len(publicas) == 9
    for nombre, funcion in publicas.items():
        primero = list(inspect.signature(funcion).parameters)[0]
        assert primero == "cursor", nombre


def test_el_repositorio_no_es_dueno_de_ningun_recurso():
    """No importa nada, no abre conexiones y no confirma ni revierte.

    La propiedad del ciclo de vida sigue siendo del controlador y del servicio,
    igual que en los seis repositorios anteriores.
    """
    arbol = ast.parse(
        (RAIZ / "app" / "repositories" / "notas_repository.py").read_text(encoding="utf-8")
    )

    importaciones = [
        nodo for nodo in ast.walk(arbol) if isinstance(nodo, (ast.Import, ast.ImportFrom))
    ]
    assert importaciones == []

    metodos = {
        nodo.func.attr
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
    }
    assert metodos == {"execute", "fetchone", "fetchall"}


def test_la_ruta_no_contiene_sql():
    """Invariante que dejo 6.5: ninguna ruta del programa lleva SQL de dominio."""
    assert _literales_sql("app/routes/notas.py") == set()
    assert _puntos_de_ejecucion("app/routes/notas.py") == []


# ---------------------------------------------------------------------------
# Bloque 2 — contrato HTTP real de POST /notas
#
# La unica entrada que escribe. Su respuesta NO es la que devuelve el
# controlador: la ruta mete el diccionario entero del controlador dentro de su
# propio campo `id`. Se fija tal cual, sin corregirlo.
# ---------------------------------------------------------------------------


def test_crear_nota_anida_la_respuesta_del_controlador_dentro_de_id(instrumentado):
    registro = instrumentado(fila=(501,))

    respuesta = ruta_notas.crear_nota(NOTA, ADMIN)

    # El campo `id` NO es un entero: es el diccionario completo del controlador.
    assert respuesta == {
        "mensaje": "Nota registrada",
        "id": {"mensaje": "Nota creada", "id": 501},
    }
    assert registro.cursores[-1] is True


@pytest.mark.parametrize(
    "validador,mensaje",
    [
        ("validar_asignacion", "La asignación no existe"),
        ("validar_estudiante", "El estudiante no existe"),
        ("validar_estudiante_en_curso", "El estudiante no pertenece a ese curso"),
    ],
)
def test_crear_nota_responde_nota_registrada_aunque_no_registre_nada(
    instrumentado, monkeypatch, validador, mensaje
):
    """Una validacion fallida no produce 4xx: produce 200 y «Nota registrada».

    El error viaja dentro del campo `id`. Nada se escribe: cero conexiones.
    """
    registro = instrumentado()
    monkeypatch.setattr(notas_controller, validador, lambda *_args: False)

    respuesta = ruta_notas.crear_nota(NOTA, ADMIN)

    assert respuesta["mensaje"] == "Nota registrada"
    assert respuesta["id"] == {"error": mensaje}
    assert True not in registro.cursores  # ninguna transaccion se confirmo


# ---------------------------------------------------------------------------
# Bloque 3 — conteos de consultas y conexiones, medidos a traves de la ruta
# ---------------------------------------------------------------------------


def test_post_notas_como_admin_abre_cuatro_conexiones(instrumentado):
    registro = instrumentado(fila=(501,))

    ruta_notas.crear_nota(NOTA, ADMIN)

    # Tres validaciones de solo lectura mas la insercion que confirma.
    assert registro.cursores == [False, False, False, True]
    assert registro.conexiones_permiso == 0


def test_post_notas_como_profesor_abre_cinco_conexiones(instrumentado):
    registro = instrumentado(fila=(501,))

    ruta_notas.crear_nota(NOTA, PROFESOR)

    assert len(registro.cursores) == 4
    assert registro.conexiones_permiso == 1
    assert len(registro.cursores) + registro.conexiones_permiso == 5


@pytest.mark.parametrize(
    "llamada,usuario,cursores,permiso",
    [
        (lambda: ruta_notas.notas_estudiante(11, ADMIN), ADMIN, 1, 0),
        (lambda: ruta_notas.notas_estudiante(11, PROFESOR), PROFESOR, 1, 1),
        (lambda: ruta_notas.boletin(11, ADMIN), ADMIN, 1, 0),
        (lambda: ruta_notas.boletin(11, PROFESOR), PROFESOR, 1, 1),
        (lambda: ruta_notas.planilla(12, ADMIN), ADMIN, 1, 0),
        (lambda: ruta_notas.planilla(12, PROFESOR), PROFESOR, 1, 1),
    ],
)
def test_las_lecturas_abren_una_conexion_mas_la_del_permiso(
    instrumentado, llamada, usuario, cursores, permiso
):
    registro = instrumentado(resultados=[[]])

    llamada()

    assert len(registro.cursores) == cursores
    assert registro.conexiones_permiso == permiso
    assert registro.cursores == [False] * cursores  # ninguna lectura confirma


def test_el_boletin_detallado_es_un_n_mas_1(instrumentado):
    """Unico N+1 del dominio: una consulta por cada materia del estudiante.

    Dashboard no tenia ninguno. Aqui el conteo SI depende de los datos.
    """
    una = [(5, "Matemáticas", "Ana Ríos", 77)]
    tres = [
        (5, "Matemáticas", "Ana Ríos", 77),
        (6, "Lenguaje", "Beto Sáenz", 78),
        (7, "Ciencias", "Cira Toro", 79),
    ]

    registro = instrumentado(resultados=[una, []])
    ruta_notas.boletin_detallado(11, 1, ADMIN)
    con_una = len(registro.cursor.calls)

    registro = instrumentado(resultados=[tres, [], [], []])
    ruta_notas.boletin_detallado(11, 1, ADMIN)
    con_tres = len(registro.cursor.calls)

    assert con_una == 2  # 1 + 1
    assert con_tres == 4  # 1 + 3
    # Una sola conexion, pero N+1 consultas dentro de ella.
    assert len(registro.cursores) == 1


# ---------------------------------------------------------------------------
# Bloque 4 — app/services/nota_service.py, sin cobertura previa
# ---------------------------------------------------------------------------


def test_cada_validacion_abre_su_propia_conexion(instrumentado):
    registro = instrumentado(fila=(1,))

    assert nota_service.validar_asignacion(12) is True
    assert nota_service.validar_estudiante(11) is True
    assert nota_service.validar_estudiante_en_curso(11, 12) is True

    assert registro.cursores == [False, False, False]
    assert [params for _query, params in registro.cursor.calls] == [(12,), (11,), (11, 12)]


def test_las_validaciones_devuelven_false_sin_fila(instrumentado):
    instrumentado(fila=None)

    assert nota_service.validar_asignacion(12) is False
    assert nota_service.validar_estudiante(11) is False
    assert nota_service.validar_estudiante_en_curso(11, 12) is False


def test_validar_asignacion_no_filtra_por_activo(instrumentado):
    """Hallazgo, fijado sin corregir: una asignacion desactivada sigue valiendo.

    Es el mismo patron que 7.0 de dashboard registro en sus dos precondiciones
    de permiso. Cambiarlo altera quien puede escribir notas.
    """
    registro = instrumentado(fila=(1,))

    nota_service.validar_asignacion(12)

    query, _params = registro.cursor.calls[0]
    assert "FROM asignaciones" in query
    assert "activo" not in query.lower()


# ---------------------------------------------------------------------------
# Bloque 5 — contrato de calculo: la cuarta formula de promedio del sistema
# ---------------------------------------------------------------------------


def test_el_promedio_se_redondea_en_python_no_se_trunca(instrumentado):
    """`round(..., 2)` en Python, no `TRUNC(..., 2)` como dashboard.

    Con 3.0, 4.0 y 4.0 el promedio real es 3.666...: redondear da 3.67 y
    truncar daria 3.66. La diferencia es visible para el usuario final.
    """
    registro = instrumentado(
        resultados=[[(3.0, "Parcial 1"), (4.0, "Parcial 2"), (4.0, "Parcial 3")]]
    )

    respuesta = notas_controller.notas_estudiante_controller(11)

    assert respuesta["promedio"] == 3.67
    assert respuesta["promedio"] != 3.66
    assert registro.cursores == [False]


def test_el_promedio_general_del_boletin_promedia_valores_sin_redondear(instrumentado):
    """Las materias se muestran redondeadas, pero el general suma las crudas.

    3.456 y 2.0 se muestran como 3.46 y 2.0, y el general es (3.456+2.0)/2 =
    2.728 -> 2.73. Promediar los valores ya redondeados daria 2.73 tambien aqui,
    pero no en general: se fija la formula real, no una equivalente.
    """
    filas = [
        ("Ana", "Ríos", "Quinto A", "Matemáticas", 3.456),
        ("Ana", "Ríos", "Quinto A", "Lenguaje", 2.0),
    ]
    instrumentado(resultados=[filas])

    respuesta = notas_controller.boletin_estudiante_controller(11)

    assert respuesta["materias"][0]["promedio"] == 3.46
    assert respuesta["promedio_general"] == round((3.456 + 2.0) / 2, 2)
    assert respuesta["promedio_general"] == 2.73


def test_el_corte_de_aprobado_es_mayor_o_igual_que_tres(instrumentado):
    filas = [
        ("Ana", "Ríos", "Quinto A", "Justo", 3.0),
        ("Ana", "Ríos", "Quinto A", "Debajo", 2.999),
    ]
    instrumentado(resultados=[filas])

    respuesta = notas_controller.boletin_estudiante_controller(11)

    assert respuesta["materias"][0]["estado"] == "Aprobado"
    assert respuesta["materias"][1]["estado"] == "Reprobado"


def test_el_boletin_detallado_no_calcula_promedio(instrumentado):
    """Devuelve 0 fijo y delega el calculo al frontend. Contrato observable."""
    asignaciones = [(5, "Matemáticas", "Ana Ríos", 77)]
    instrumentado(resultados=[asignaciones, [(901, "Parcial 1", 4.0)]])

    respuesta = ruta_notas.boletin_detallado(11, 1, ADMIN)

    assert respuesta[0]["actividades"][0]["nota"] == 4.0
    assert respuesta[0]["promedio"] == 0


# ---------------------------------------------------------------------------
# Bloque 6 — el tratamiento de `periodo`, divergente dentro del mismo dominio
# ---------------------------------------------------------------------------


def test_la_escritura_no_fija_la_columna_periodo(instrumentado):
    """`POST /notas` inserta cuatro columnas y `periodo` no esta entre ellas.

    El camino de escritura emite cuatro consultas: las tres validaciones del
    servicio y el INSERT, que va el ultimo.
    """
    registro = instrumentado(fila=(501,))

    notas_controller.crear_nota_controller(NOTA, usuario=ADMIN)

    assert len(registro.cursor.calls) == 4
    query, params = registro.cursor.calls[3]
    assert "INSERT INTO notas_detalle" in query
    assert "periodo" not in query.lower()
    assert params == (11, 77, 4.2, "Parcial 1")


@pytest.mark.parametrize(
    "llamada,resultados",
    [
        (lambda: notas_controller.notas_estudiante_controller(11), [[]]),
        (lambda: notas_controller.boletin_estudiante_controller(11), [[]]),
        (lambda: notas_controller.planilla_asignacion_controller(12), [[]]),
    ],
)
def test_las_tres_lecturas_agregadas_ignoran_el_periodo(instrumentado, llamada, resultados):
    """Promedian todos los periodos juntos. Solo el boletin detallado filtra."""
    registro = instrumentado(resultados=resultados)

    llamada()

    query, _params = registro.cursor.calls[0]
    assert "periodo" not in query.lower()


def test_solo_el_boletin_detallado_filtra_por_periodo(instrumentado):
    asignaciones = [(5, "Matemáticas", "Ana Ríos", 77)]
    registro = instrumentado(resultados=[asignaciones, []])

    ruta_notas.boletin_detallado(11, 3, ADMIN)

    _query_asignaciones, _ = registro.cursor.calls[0]
    query_notas, params_notas = registro.cursor.calls[1]
    assert "periodo = %s" in query_notas
    assert params_notas == (11, 77, 3)


# ---------------------------------------------------------------------------
# Bloque 7 — contrato HTTP real de la escritura, medido por ASGI
#
# El resto del archivo, y toda la suite del repositorio, llama a las funciones
# de ruta directamente. Eso NO observa el status code: lo infiere. Como el
# hallazgo mas grave de 7.0 es precisamente que una validacion fallida responde
# 200, aqui se conduce la aplicacion por su interfaz ASGI, que es el camino real
# de una peticion: middleware, enrutado, dependencias y serializacion.
#
# No se usa TestClient porque httpx no esta instalado y esta subcapa no cambia
# dependencias. No se toca PostgreSQL: la capa de datos va con dobles.
# ---------------------------------------------------------------------------

CUERPO_NOTA = {
    "estudiante_id": 11,
    "asignacion_id": 12,
    "nota": 4.2,
    "descripcion": "Parcial 1",
}


def _peticion_asgi(aplicacion, metodo, ruta, cuerpo):
    """Ejecuta una peticion HTTP real contra la app y devuelve status y cuerpo."""
    import asyncio
    import json

    crudo = json.dumps(cuerpo).encode()
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1",
        "method": metodo,
        "scheme": "http",
        "path": ruta,
        "raw_path": ruta.encode(),
        "query_string": b"",
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
    """La aplicacion real con un admin autenticado y la capa de datos doblada."""
    from app.dependencies import get_current_user
    from app.main import app

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        yield CursorInstrumentado(fila=(501,))

    monkeypatch.setattr(notas_controller, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(nota_service, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(
        notas_controller,
        "resolver_asignacion_academica_id_cursor",
        lambda _cursor, asignacion_id: 77,
    )

    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        yield app
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_http_crear_nota_responde_200_con_el_id_anidado(app_http):
    estado, cuerpo = _peticion_asgi(app_http, "POST", "/notas", CUERPO_NOTA)

    assert estado == 200
    assert cuerpo == {"mensaje": "Nota registrada", "id": {"mensaje": "Nota creada", "id": 501}}
    # El id real esta anidado dos niveles: `cuerpo["id"]` NO es un entero.
    assert not isinstance(cuerpo["id"], int)
    assert cuerpo["id"]["id"] == 501


@pytest.mark.parametrize(
    "validador,mensaje",
    [
        ("validar_asignacion", "La asignación no existe"),
        ("validar_estudiante", "El estudiante no existe"),
        ("validar_estudiante_en_curso", "El estudiante no pertenece a ese curso"),
    ],
)
def test_http_una_validacion_fallida_responde_200_nota_registrada(
    app_http, monkeypatch, validador, mensaje
):
    """El hallazgo mas grave de 7.0, fijado con el status code real.

    No es un 4xx: es un 200 cuyo `mensaje` afirma que la nota quedo registrada.
    El error viaja dentro del campo `id`, donde un cliente no lo busca.
    """
    monkeypatch.setattr(notas_controller, validador, lambda *_args: False)

    estado, cuerpo = _peticion_asgi(app_http, "POST", "/notas", CUERPO_NOTA)

    assert estado == 200
    assert cuerpo["mensaje"] == "Nota registrada"
    assert cuerpo["id"] == {"error": mensaje}


def test_http_la_nota_fuera_de_rango_si_responde_422(app_http):
    """Contraste: la validacion de Pydantic si produce un status code correcto."""
    estado, cuerpo = _peticion_asgi(app_http, "POST", "/notas", {**CUERPO_NOTA, "nota": 9.9})

    assert estado == 422
    assert cuerpo["detail"][0]["loc"] == ["body", "nota"]
