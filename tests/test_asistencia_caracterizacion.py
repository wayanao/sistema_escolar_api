"""Caracterizacion de la subcapa 7.0 del dominio `asistencia`.

Complementa lo que ya existe y no lo repite. Este dominio llega con pruebas
heredadas de la capa 1, cosa que no le paso a `dashboard`, `notas` ni `ventas`:
`test_asistencia_historial.py` fija cinco comportamientos de la lectura y
`test_asistencia_validaciones.py` siete de la escritura y sus validaciones.

Lo que ninguno de los dos toca, y este archivo fija:

- la frontera de persistencia, cerrada por 7.1 en el noveno repositorio. Las dos
  guardias de linea base que 7.0 dejo puestas fallaron al extraer, que era la
  senal esperada, y estan sustituidas por sus versiones positivas;
- la frontera real del dominio, que resulto ser de tres archivos y no de dos;
- los DOS idiomas de conexion que conviven, herencia de que 1.4g migrase
  1 sitio de 2;
- los conteos de consultas y de conexiones, incluido el perfil O(1) que deja la
  correccion puntual posterior al cierre para los permisos de escritura;
- el contrato HTTP real de las dos entradas, medido por ASGI;
- los dos consumidores ajenos ya migrados que leen esta tabla;
- los hallazgos que 7.0 registra; el N+1 de permisos ya queda corregido.

La mayor parte del archivo conserva la caracterizacion de 7.0. El bloque 6 se
actualiza con la correccion puntual posterior al cierre que elimina el N+1 de
permisos, sin cambiar el contrato HTTP ni la persistencia del controlador.
"""

import ast
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.controllers import asistencia_controller
from app.schemas.asistencia import AsistenciaCreate

RAIZ = Path(__file__).resolve().parents[1]

CONTROLADOR = "app/controllers/asistencia_controller.py"
RUTA = "app/routes/asistencia.py"
ESQUEMA = "app/schemas/asistencia.py"
REPOSITORIO = "app/repositories/asistencia_repository.py"

ADMIN = {"id": 7, "rol": "admin", "tenant": "tenant_demo"}
PROFESOR = {"id": 3, "rol": "profesor", "tenant": "tenant_demo"}

PALABRAS_SQL = ("SELECT", "INSERT", "UPDATE", "DELETE", "WITH ")

ASIGNACION_RESUELTA = 42
# Año lectivo, paso 3.7: la guardia de escritura lee el año de la clase.
SQL_GUARDIA = "SELECT al.anio, al.estado"
GUARDIA_HOY = (2026, "activo")


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


def _funciones_publicas(ruta_relativa):
    arbol = ast.parse((RAIZ / ruta_relativa).read_text(encoding="utf-8"))
    return [
        nodo.name
        for nodo in arbol.body
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not nodo.name.startswith("_")
    ]


class CursorInstrumentado:
    """Cursor doble que registra cada consulta y sirve resultados en orden.

    `fetchone` y `fetchall` comparten la misma cola, que es el idioma que ya
    usan las caracterizaciones de `ventas` y de `notas`.

    Año lectivo, paso 3.7: la consulta de la guardia (el año de la clase) se
    anota como cualquier otra, pero responde "2026 activo" sin gastar la cola,
    para que cada prueba siga sirviendo las mismas respuestas.
    """

    def __init__(self, fetches=()):
        self.fetches = list(fetches)
        self.calls = []
        self.closed = False

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        if self.calls and SQL_GUARDIA in self.calls[-1][0]:
            return GUARDIA_HOY
        return self.fetches.pop(0) if self.fetches else None

    def fetchall(self):
        return self.fetches.pop(0) if self.fetches else []

    def close(self):
        self.closed = True

    @property
    def sql(self):
        return [query for query, _params in self.calls]


class ConexionInstrumentada:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self, *args, **kwargs):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


@pytest.fixture
def instrumentado(monkeypatch):
    """Instrumenta el controlador contando conexiones y consultas.

    Hay que doblar DOS fabricas, no una: `guardar_asistencia_controller` abre
    con `get_connection()` y `obtener_historial_asistencia` con `get_cursor()`.
    Es el rasgo que 1.4g dejo al migrar 1 sitio de 2, y ningun dominio anterior
    de la capa 7 lo tenia.
    """

    def instalar(fetches=()):
        registro = SimpleNamespace(conexiones=0, conexiones_abiertas=[])
        cursor = CursorInstrumentado(fetches=fetches)

        def fake_get_connection():
            registro.conexiones += 1
            conn = ConexionInstrumentada(cursor)
            registro.conexiones_abiertas.append(conn)
            return conn

        @contextmanager
        def fake_get_cursor(*args, **kwargs):
            conn = fake_get_connection()
            try:
                yield conn.cursor()
            finally:
                conn.close()

        monkeypatch.setattr(asistencia_controller, "get_connection", fake_get_connection)
        monkeypatch.setattr(asistencia_controller, "get_cursor", fake_get_cursor)

        registro.cursor = cursor
        registro.conexion = lambda: registro.conexiones_abiertas[-1]
        return registro

    return instalar


def _registro(estudiante_id=1, asignacion_id=10, fecha=date(2026, 7, 15), periodo=2, estado="presente"):
    return AsistenciaCreate(
        estudiante_id=estudiante_id,
        asignacion_id=asignacion_id,
        fecha=fecha,
        periodo=periodo,
        estado=estado,
    )


# ---------------------------------------------------------------------------
# Bloque 1: la frontera de persistencia, ya cerrada por 7.1.
#
# Las dos primeras pruebas de este bloque son las versiones POSITIVAS de las dos
# guardias de linea base que 7.0 dejo puestas y que 7.1 hizo fallar, que era la
# senal esperada. Leccion 14 de la capa 6, aplicada por quinta vez. La tercera
# valia antes y sigue valiendo.
# ---------------------------------------------------------------------------


def test_el_repositorio_de_asistencia_es_el_noveno():
    """Sustituye a `test_el_dominio_todavia_no_tiene_repositorio_propio`.

    Enumera el conjunto EXACTO a proposito: obliga a que cada migracion nueva se
    reconozca en vez de colarse. Es la misma severidad deliberada que llevan las
    guardias gemelas de dashboard, notas y ventas.
    """
    repositorios = sorted(
        ruta.stem for ruta in (RAIZ / "app/repositories").glob("*_repository.py")
    )

    assert repositorios == [
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
        # Puntualidad de pagos del panel del admin (2026-11-11): solo lee.
        "puntualidad_repository",
        "reportes_repository",
        "subnotas_planilla_repository",
        "super_admin_repository",
        "ventas_repository",
    ]
    # 24 -> 25 el 2026-11-11 con el de puntualidad de pagos.
    assert len(repositorios) == 25


def test_las_tres_sentencias_viven_ahora_en_el_repositorio():
    """Sustituye a `test_las_tres_sentencias_viven_hoy_en_el_controlador`."""
    literales = _literales_sql(REPOSITORIO)

    assert len(literales) == 3
    assert sum("DELETE FROM asistencia" in s for s in literales) == 1
    assert sum("INSERT INTO asistencia" in s for s in literales) == 1
    assert sum("JOIN asistencia a" in s for s in literales) == 1

    assert _literales_sql(CONTROLADOR) == set()


def test_la_ruta_no_contiene_sql():
    """GUARDIA: valia antes de 7.1 y sigue valiendo despues."""
    assert _literales_sql(RUTA) == set()


def test_las_tres_funciones_publicas_reciben_el_cursor():
    arbol = ast.parse((RAIZ / REPOSITORIO).read_text(encoding="utf-8"))
    funciones = [
        nodo
        for nodo in arbol.body
        if isinstance(nodo, ast.FunctionDef) and not nodo.name.startswith("_")
    ]

    assert [f.name for f in funciones] == [
        "borrar_asistencia_del_lote",
        "insertar_asistencia",
        "leer_historial_de_asignacion",
    ]
    for funcion in funciones:
        assert funcion.args.args[0].arg == "cursor"


def test_el_repositorio_no_es_dueno_de_ningun_recurso():
    """No abre, no cierra, no confirma y no revierte. Esa propiedad es del
    controlador, y en los DOS idiomas."""
    arbol = ast.parse((RAIZ / REPOSITORIO).read_text(encoding="utf-8"))

    metodos = {
        nodo.func.attr
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
    }
    nombres = {
        nodo.func.id
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
    }
    importados = {
        alias.name
        for nodo in ast.walk(arbol)
        if isinstance(nodo, (ast.Import, ast.ImportFrom))
        for alias in nodo.names
    }

    assert metodos <= {"execute", "fetchall"}
    assert "commit" not in metodos and "rollback" not in metodos and "close" not in metodos
    assert nombres == set()
    assert importados == set()


def test_el_repositorio_no_conoce_detalles_http():
    """Convencion de `app/repositories/README.md`: datos simples, nada de FastAPI."""
    fuente = (RAIZ / REPOSITORIO).read_text(encoding="utf-8")

    assert "fastapi" not in fuente.lower()
    assert "HTTPException" not in fuente


# ---------------------------------------------------------------------------
# Bloque 2: la frontera real del dominio.
# ---------------------------------------------------------------------------


def test_el_dominio_son_tres_archivos_y_no_dos():
    """El supuesto heredado decia dos. Hay un esquema propio ademas.

    Es el mismo tipo de correccion que hizo falta en `notas`, donde el supuesto
    daba dos archivos y eran cuatro, aunque aqui es menos grave: el tercero es
    el contrato de entrada y NO contiene persistencia.
    """
    assert (RAIZ / CONTROLADOR).exists()
    assert (RAIZ / RUTA).exists()
    assert (RAIZ / ESQUEMA).exists()

    assert not (RAIZ / "app/services/asistencia_service.py").exists()
    assert _literales_sql(ESQUEMA) == set()


def test_el_controlador_expone_exactamente_dos_funciones():
    """El supuesto 4 estaba marcado como INFERENCIA DE PATRON y acerto.

    Se dedujo del «1 sitio de 2» de 1.4g, donde «sitio» significaba apertura de
    conexion y no funcion. Que coincida es una casualidad afortunada, no una
    regla: la inferencia se marco como tal precisamente porque podia fallar.
    """
    assert _funciones_publicas(CONTROLADOR) == [
        "guardar_asistencia_controller",
        "obtener_historial_asistencia",
    ]


def test_el_esquema_pydantic_vive_en_app_schemas():
    """Contraste con `ventas`, unico dominio cuyos esquemas viven en la ruta."""
    fuente = (RAIZ / RUTA).read_text(encoding="utf-8")

    assert "from app.schemas.asistencia import AsistenciaCreate" in fuente
    assert "class AsistenciaCreate" not in fuente


def test_el_estado_admite_solo_dos_valores_en_minuscula():
    with pytest.raises(Exception):
        _registro(estado="Ausente")

    assert _registro(estado="ausente").estado == "ausente"
    assert _registro(estado="presente").estado == "presente"


# ---------------------------------------------------------------------------
# Bloque 3: los dos idiomas de conexion.
#
# Es el rasgo que distingue a este dominio de los tres anteriores de la capa 7.
# ---------------------------------------------------------------------------


def test_el_dominio_usa_dos_idiomas_de_conexion():
    """1.4g migro `obtener_historial_asistencia` y NO toco la escritura."""
    fuente = (RAIZ / CONTROLADOR).read_text(encoding="utf-8")

    escritura = fuente.split("def guardar_asistencia_controller")[1].split("def obtener_historial")[0]
    lectura = fuente.split("def obtener_historial_asistencia")[1]

    assert "get_connection()" in escritura
    assert "with get_cursor() as cursor" not in escritura

    assert "with get_cursor() as cursor" in lectura
    assert "get_connection()" not in lectura


def test_la_escritura_es_duena_de_su_ciclo_de_vida(instrumentado):
    registro = instrumentado([(ASIGNACION_RESUELTA,), (None, "Matemáticas")])

    asistencia_controller.guardar_asistencia_controller([_registro()], usuario=ADMIN)

    assert registro.conexiones == 1
    assert registro.conexion().committed is True
    assert registro.conexion().rolled_back is False
    assert registro.conexion().closed is True
    assert registro.cursor.closed is True


def test_la_escritura_revierte_y_cierra_ante_un_fallo(instrumentado):
    registro = instrumentado([(ASIGNACION_RESUELTA,), (None, "Matemáticas")])

    def explota(query, params=None):
        raise RuntimeError("fallo de infraestructura")

    original = registro.cursor.execute
    llamadas = {"n": 0}

    def execute(query, params=None):
        llamadas["n"] += 1
        # Llamada 1: guardia del año lectivo (paso 3.7). 2: resolver
        # asignacion. 3: resolver nivel/materia. 4: DELETE. 5: primer INSERT,
        # donde se hace fallar la escritura.
        if llamadas["n"] == 5:
            explota(query, params)
        original(query, params)

    registro.cursor.execute = execute

    with pytest.raises(RuntimeError):
        asistencia_controller.guardar_asistencia_controller([_registro()], usuario=ADMIN)

    assert registro.conexion().committed is False
    assert registro.conexion().rolled_back is True
    assert registro.conexion().closed is True


# ---------------------------------------------------------------------------
# Bloque 4: linea base de consultas y conexiones del controlador.
# ---------------------------------------------------------------------------


def test_guardar_cuesta_una_conexion_y_dos_consultas_mas_una_por_estudiante(instrumentado):
    """La funcionalidad de nivel academico agrega una consulta de solo
    lectura (nivel + materia de la asignacion) dentro de la MISMA
    conexion/transaccion ya abierta -no abre una conexion nueva-. El conteo
    fijo sube de dos a tres; el costo por estudiante no cambia.

    Año lectivo, paso 3.7: la guardia de escritura suma otra lectura fija, la
    primera, en la misma conexion. De tres a cuatro fijas."""
    registro = instrumentado([(ASIGNACION_RESUELTA,), (None, "Matemáticas")])

    asistencia_controller.guardar_asistencia_controller(
        [_registro(estudiante_id=1), _registro(estudiante_id=2), _registro(estudiante_id=3)],
        usuario=ADMIN,
    )

    assert registro.conexiones == 1
    assert len(registro.cursor.calls) == 7

    tipos = [s.strip().split()[0].upper() for s in registro.cursor.sql]
    assert tipos == ["SELECT", "SELECT", "SELECT", "DELETE", "INSERT", "INSERT", "INSERT"]
    assert SQL_GUARDIA in registro.cursor.sql[0]


def test_historial_cuesta_una_conexion_y_dos_consultas(instrumentado):
    registro = instrumentado([(ASIGNACION_RESUELTA,), []])

    asistencia_controller.obtener_historial_asistencia(10, 2)

    assert registro.conexiones == 1
    assert len(registro.cursor.calls) == 2

    tipos = [s.strip().split()[0].upper() for s in registro.cursor.sql]
    assert tipos == ["SELECT", "SELECT"]


def test_los_dos_caminos_resuelven_la_asignacion_academica(instrumentado):
    registro = instrumentado([(ASIGNACION_RESUELTA,), (None, "Matemáticas")])
    asistencia_controller.guardar_asistencia_controller([_registro(asignacion_id=10)], usuario=ADMIN)
    # calls[0] es la guardia del año lectivo, sobre la clase pedida (paso 3.7).
    assert registro.cursor.calls[0][1] == (10,)
    assert registro.cursor.calls[1][1] == (10,)
    assert registro.cursor.calls[2][1][0] == ASIGNACION_RESUELTA

    registro = instrumentado([(ASIGNACION_RESUELTA,), []])
    asistencia_controller.obtener_historial_asistencia(10, 2)
    assert registro.cursor.calls[0][1] == (10,)
    assert registro.cursor.calls[1][1] == (ASIGNACION_RESUELTA, 2)


# ---------------------------------------------------------------------------
# Bloque 5: la escritura, en detalle.
# ---------------------------------------------------------------------------


def test_el_borrado_solo_alcanza_a_los_estudiantes_del_lote(instrumentado):
    registro = instrumentado([(ASIGNACION_RESUELTA,), (None, "Matemáticas")])

    asistencia_controller.guardar_asistencia_controller(
        [_registro(estudiante_id=4), _registro(estudiante_id=9)], usuario=ADMIN
    )

    # calls[0] es la guardia del año lectivo (paso 3.7), calls[1] resuelve la
    # asignacion academica, calls[2] el nivel/materia (funcionalidad de nivel
    # academico), calls[3] es el DELETE.
    _sql, params = registro.cursor.calls[3]
    assert params == (ASIGNACION_RESUELTA, date(2026, 7, 15), 2, [4, 9])


def test_el_borrado_toma_el_contexto_del_primer_registro(instrumentado):
    """HALLAZGO. El DELETE usa fecha y periodo de `data[0]`; los INSERT, los suyos.

    Hoy es inocuo porque la RUTA valida antes que los tres campos coincidan,
    pero esa validacion no vive en el controlador. Ver el hallazgo del bloque 8.
    """
    fuente = (RAIZ / CONTROLADOR).read_text(encoding="utf-8")

    assert "data[0].fecha" in fuente
    assert "data[0].periodo" in fuente
    assert "item.fecha" in fuente
    assert "item.periodo" in fuente


def test_la_escritura_no_valida_el_estado(instrumentado):
    """HALLAZGO. El controlador inserta `item.estado` crudo.

    El Literal del esquema solo protege el camino HTTP. Quien llame al
    controlador directamente puede escribir cualquier cadena.
    """
    registro = instrumentado([(ASIGNACION_RESUELTA,), (None, "Matemáticas")])

    asistencia_controller.guardar_asistencia_controller(
        [SimpleNamespace(estudiante_id=1, asignacion_id=10, fecha=date(2026, 7, 15), periodo=2, estado="EXCUSA")],
        usuario=ADMIN,
    )

    # calls[4] es el primer (y unico) INSERT: 0=guardia del año (paso 3.7),
    # 1=asignacion, 2=nivel/materia, 3=DELETE.
    _sql, params = registro.cursor.calls[4]
    assert params[3] == "EXCUSA"


# ---------------------------------------------------------------------------
# Bloque 6: perfil O(1) de conexiones en los permisos de escritura.
#
# La correccion puntual posterior al cierre valida una vez la asignacion y una
# vez el lote completo de estudiantes. El numero ya no crece con el curso.
# ---------------------------------------------------------------------------


@pytest.fixture
def ruta_instrumentada(monkeypatch, instrumentado):
    """Cuenta las conexiones de TODO el camino: permisos mas controlador."""
    from app.core import permissions

    def instalar(fetches=(), respuestas_permisos=()):
        registro = instrumentado(fetches)
        registro.conexiones_permisos = 0
        respuestas = list(respuestas_permisos)

        def fake_get_connection():
            registro.conexiones_permisos += 1
            return ConexionInstrumentada(CursorInstrumentado(fetches=[respuestas.pop(0)]))

        monkeypatch.setattr(permissions, "get_connection", fake_get_connection)
        return registro

    return instalar


@pytest.mark.parametrize("cantidad", [1, 5, 30])
def test_la_escritura_admin_mantiene_dos_conexiones_sin_importar_el_lote(
    ruta_instrumentada,
    cantidad,
):
    from app.routes import asistencia as ruta

    registro = ruta_instrumentada(
        [(ASIGNACION_RESUELTA,), (None, "Matemáticas")],
        respuestas_permisos=[(cantidad,)],
    )
    lote = [_registro(estudiante_id=i) for i in range(1, cantidad + 1)]

    ruta.guardar_asistencia(lote, current_user=ADMIN)

    assert registro.conexiones_permisos == 1
    assert registro.conexiones == 1
    assert registro.conexiones_permisos + registro.conexiones == 2


def test_el_rechazo_por_nivel_no_abre_una_conexion_extra(ruta_instrumentada):
    """Funcionalidad de nivel academico: si el curso es preescolar y la
    asignacion no es la reservada de jornada, se rechaza sin escribir, con
    el mismo perfil de una conexion que el camino que si escribe."""
    from app.routes import asistencia as ruta

    registro = ruta_instrumentada(
        [(ASIGNACION_RESUELTA,), ("preescolar", "Matemáticas")],
        respuestas_permisos=[(1,)],
    )

    respuesta = ruta.guardar_asistencia([_registro()], current_user=ADMIN)

    assert respuesta == {
        "error": 'Este curso es de preescolar. Usa la asignación "Asistencia diaria" '
        "para registrar asistencia."
    }
    assert registro.conexiones == 1
    # Guardia del año lectivo (paso 3.7), asignacion y nivel/materia.
    assert len(registro.cursor.calls) == 3
    assert registro.conexion().committed is False


@pytest.mark.parametrize("cantidad", [1, 5, 30])
def test_la_escritura_profesor_mantiene_tres_conexiones_sin_importar_el_lote(
    ruta_instrumentada,
    cantidad,
):
    from app.routes import asistencia as ruta

    registro = ruta_instrumentada(
        [(ASIGNACION_RESUELTA,), (None, "Matemáticas")],
        respuestas_permisos=[(1,), (cantidad,)],
    )
    lote = [_registro(estudiante_id=i) for i in range(1, cantidad + 1)]

    ruta.guardar_asistencia(lote, current_user=PROFESOR)

    assert registro.conexiones_permisos == 2
    assert registro.conexiones == 1
    assert registro.conexiones_permisos + registro.conexiones == 3


def test_los_permisos_se_comprueban_una_vez_para_el_lote_completo(monkeypatch):
    from app.routes import asistencia as ruta

    asignaciones = []
    lotes = []
    monkeypatch.setattr(ruta, "require_asignacion_access", lambda a, u: asignaciones.append(a))
    monkeypatch.setattr(
        ruta,
        "require_estudiantes_in_asignacion",
        lambda estudiantes, asignacion: lotes.append((estudiantes, asignacion)),
    )
    monkeypatch.setattr(
        ruta, "guardar_asistencia_controller", lambda lote, usuario: {"mensaje": "ok"}
    )

    ruta.guardar_asistencia([_registro(estudiante_id=i) for i in range(1, 5)], current_user=ADMIN)

    assert asignaciones == [10]
    assert lotes == [([1, 2, 3, 4], 10)]


def test_la_lectura_abre_una_sola_conexion_siendo_admin(ruta_instrumentada):
    from app.routes import asistencia as ruta

    registro = ruta_instrumentada([(ASIGNACION_RESUELTA,), []])

    ruta.historial(10, 2, current_user=ADMIN)

    assert registro.conexiones_permisos == 0
    assert registro.conexiones == 1


# ---------------------------------------------------------------------------
# Bloque 7: permisos.
# ---------------------------------------------------------------------------


def test_el_router_exige_usuario_autenticado():
    fuente = (RAIZ / RUTA).read_text(encoding="utf-8")

    assert 'dependencies=[Depends(get_current_user)]' in fuente
    assert "get_current_active_admin" not in fuente


def test_las_dos_entradas_exigen_acceso_a_la_asignacion():
    fuente = (RAIZ / RUTA).read_text(encoding="utf-8")

    assert fuente.count("require_asignacion_access(") == 2


def test_solo_la_escritura_exige_que_el_estudiante_pertenezca():
    """Los permisos NO son uniformes: son dos modelos en dos entradas.

    Contraste con `ventas`, primer dominio del programa con un solo modelo.
    """
    fuente = (RAIZ / RUTA).read_text(encoding="utf-8")
    escritura = fuente.split("def guardar_asistencia")[1].split("def historial")[0]
    lectura = fuente.split("def historial")[1]

    assert "require_estudiantes_in_asignacion(" in escritura
    assert "require_estudiantes_in_asignacion(" not in lectura


# ---------------------------------------------------------------------------
# Bloque 8: las validaciones de dominio viven en la capa de rutas.
# ---------------------------------------------------------------------------


def test_las_tres_validaciones_de_lote_viven_en_la_ruta():
    """HALLAZGO. Es el mismo patron que la capa 6 registro para `/mis-clases`,
    pero al reves: alli era SQL en la ruta; aqui es una regla de dominio.

    El controlador NO las repite, asi que llamarlo directamente con un lote
    heterogeneo borraria por el contexto de `data[0]` e insertaria por el de
    cada item.
    """
    ruta_fuente = (RAIZ / RUTA).read_text(encoding="utf-8")
    controlador_fuente = (RAIZ / CONTROLADOR).read_text(encoding="utf-8")

    assert "al menos un estudiante" in ruta_fuente
    assert "misma asignación, fecha y período" in ruta_fuente
    assert "estudiantes duplicados" in ruta_fuente

    assert "al menos un estudiante" not in controlador_fuente
    assert "duplicados" not in controlador_fuente


def test_el_dominio_no_tiene_ningun_try_except_propio_en_la_lectura():
    """HALLAZGO. Solo la escritura tiene `try`, y su `except` reenvia.

    Un fallo de infraestructura en la lectura sale como 500, no como 4xx. Es el
    mismo hallazgo que 7.0 de `notas` registro para su dominio entero.
    """
    fuente = (RAIZ / CONTROLADOR).read_text(encoding="utf-8")
    lectura = fuente.split("def obtener_historial_asistencia")[1]

    assert "try:" not in lectura
    assert "except Exception:" in fuente
    assert "raise" in fuente.split("except Exception:")[1]


# ---------------------------------------------------------------------------
# Bloque 9: los dos consumidores ajenos, ya migrados.
# ---------------------------------------------------------------------------


def test_dos_repositorios_ya_migrados_leen_la_tabla():
    """Romper su contrato NO haria fallar las pruebas de `asistencia`."""
    estudiantes = _literales_sql("app/repositories/estudiantes_repository.py")
    dashboard = _literales_sql("app/repositories/dashboard_repository.py")

    assert sum("FROM asistencia" in s for s in estudiantes) == 1
    assert sum("FROM asistencia a" in s for s in dashboard) == 1


def test_los_dos_consumidores_filtran_el_estado_con_ilike():
    """HALLAZGO, registrado y no corregido.

    El dominio escribe `estado` restringido por un `Literal` en minuscula, pero
    los dos lectores ajenos comparan con `ILIKE 'ausente'`, sin apoyarse en esa
    restriccion. 7.0 lo MAPEA; no lo arregla.
    """
    estudiantes = _literales_sql("app/repositories/estudiantes_repository.py")
    dashboard = _literales_sql("app/repositories/dashboard_repository.py")

    assert any("estado ILIKE 'ausente'" in s for s in estudiantes)
    assert any("a.estado ILIKE 'ausente'" in s for s in dashboard)

    assert not any("ILIKE" in s for s in _literales_sql(CONTROLADOR))


def test_el_dominio_no_toca_almacenamiento_de_archivos():
    for ruta_relativa in (CONTROLADOR, RUTA, ESQUEMA):
        assert "storage" not in (RAIZ / ruta_relativa).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Bloque 10: contrato HTTP real, medido por ASGI.
#
# No se usa TestClient porque httpx no esta instalado y esta subcapa no cambia
# dependencias. No se toca PostgreSQL: la capa de datos va con dobles.
# ---------------------------------------------------------------------------


def _peticion_asgi(aplicacion, metodo, ruta, cuerpo=None):
    """Ejecuta una peticion HTTP real contra la app y devuelve status y cuerpo."""
    import asyncio
    import json

    crudo = json.dumps(cuerpo).encode() if cuerpo is not None else b""
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


CUERPO_LOTE = [
    {
        "estudiante_id": 1,
        "asignacion_id": 10,
        "fecha": "2026-07-15",
        "estado": "presente",
        "periodo": 2,
    }
]


@pytest.fixture
def app_http(monkeypatch):
    """La aplicacion real con un admin autenticado y la capa de datos doblada."""
    from app.core import permissions
    from app.dependencies import get_current_user
    from app.main import app

    estado = SimpleNamespace(cursor=None)

    def instalar(fetches):
        cursor = CursorInstrumentado(fetches=fetches)
        estado.cursor = cursor
        monkeypatch.setattr(
            asistencia_controller,
            "get_connection",
            lambda: ConexionInstrumentada(cursor),
        )

        @contextmanager
        def fake_get_cursor(*args, **kwargs):
            yield cursor

        monkeypatch.setattr(asistencia_controller, "get_cursor", fake_get_cursor)
        monkeypatch.setattr(
            permissions,
            "get_connection",
            lambda: ConexionInstrumentada(CursorInstrumentado(fetches=[(1,)] * 50)),
        )

    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        yield app, instalar, estado
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_http_guardar_responde_200_con_el_mensaje_fijo(app_http):
    app, instalar, _estado = app_http
    instalar([(ASIGNACION_RESUELTA,), (None, "Matemáticas")])

    estado, cuerpo = _peticion_asgi(app, "POST", "/asistencia", CUERPO_LOTE)

    assert estado == 200
    assert cuerpo == {"mensaje": "Asistencia guardada"}


def test_http_guardar_en_preescolar_con_materia_normal_responde_200_con_error(app_http):
    """Funcionalidad de nivel academico: el rechazo es un 200 logico con
    error en el cuerpo, igual que el resto de reglas de dominio de este
    programa (ver planilla, boletin)."""
    app, instalar, _estado = app_http
    instalar([(ASIGNACION_RESUELTA,), ("preescolar", "Matemáticas")])

    estado, cuerpo = _peticion_asgi(app, "POST", "/asistencia", CUERPO_LOTE)

    assert estado == 200
    assert cuerpo == {
        "error": 'Este curso es de preescolar. Usa la asignación "Asistencia diaria" '
        "para registrar asistencia."
    }


def test_http_un_lote_vacio_responde_422(app_http):
    app, instalar, _estado = app_http
    instalar([])

    estado, cuerpo = _peticion_asgi(app, "POST", "/asistencia", [])

    assert estado == 422
    assert "al menos un estudiante" in cuerpo["detail"]


def test_http_un_estado_desconocido_responde_422(app_http):
    """Lo rechaza Pydantic antes de llegar al controlador."""
    app, instalar, _estado = app_http
    instalar([])

    cuerpo_malo = [dict(CUERPO_LOTE[0], estado="excusa")]
    estado, _cuerpo = _peticion_asgi(app, "POST", "/asistencia", cuerpo_malo)

    assert estado == 422


def test_http_un_lote_heterogeneo_responde_422(app_http):
    app, instalar, _estado = app_http
    instalar([])

    cuerpo_malo = [CUERPO_LOTE[0], dict(CUERPO_LOTE[0], estudiante_id=2, asignacion_id=11)]
    estado, cuerpo = _peticion_asgi(app, "POST", "/asistencia", cuerpo_malo)

    assert estado == 422
    assert "misma asignación" in cuerpo["detail"]


def test_http_el_historial_responde_200_con_la_lista_agrupada(app_http):
    app, instalar, _estado = app_http
    instalar([(ASIGNACION_RESUELTA,), [(1, "Ana", "Gomez", date(2026, 7, 15), "ausente")]])

    estado, cuerpo = _peticion_asgi(app, "GET", "/asistencia/historial/10/2")

    assert estado == 200
    assert cuerpo == [
        {
            "estudiante_id": 1,
            "nombre": "Ana",
            "apellido": "Gomez",
            "historial": [{"fecha": "2026-07-15", "estado": "ausente"}],
        }
    ]


def test_http_el_historial_no_declara_response_model(app_http):
    """Ninguna de las dos entradas lo declara. Anadirlo NO entra por inferencia."""
    fuente = (RAIZ / RUTA).read_text(encoding="utf-8")

    assert "response_model" not in fuente
