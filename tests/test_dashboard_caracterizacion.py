"""Caracterizacion del dominio dashboard. Capa 7, subcapa 7.0.

Fija lo que hoy no estaba cubierto y lo que una extraccion posterior podria
alterar sin que fallara nada:

1. las cuatro funciones que siguen usando get_connection y que
   test_dashboard_controlador.py no cubre, porque aquel documento se escribio
   para las cuatro que migraron a get_cursor en la subcapa 1.4d;
2. el conteo real de consultas y de conexiones de cada camino, incluidas las
   precondiciones de permiso que se ejecutan en la capa de rutas;
3. guardias estructurales sobre lo que este dominio no hace: no escribe, no
   toca storage y no tiene SQL en las rutas.

La subcapa 7.1 sustituyo las dos guardias que fijaban la linea base previa a
la extraccion —ocho sentencias en el controlador y ningun repositorio— por sus
versiones positivas. Fallaron al extraer, que era la senal esperada.

Los conteos excluyen autenticacion, search_path y la sentencia de timeouts,
igual que los de las capas 5 y 6. Todo se mide con dobles: ninguna prueba de
este archivo abre una conexion real.
"""

import ast
import re
from contextlib import contextmanager
from datetime import date
from pathlib import Path

import pytest

from app.controllers import dashboard_controller
from app.core import permissions
from app.routes import dashboard

RAIZ = Path(__file__).resolve().parents[1]
CONTROLADOR = RAIZ / "app" / "controllers" / "dashboard_controller.py"
RUTAS = RAIZ / "app" / "routes" / "dashboard.py"
REPOSITORIO = RAIZ / "app" / "repositories" / "dashboard_repository.py"

ADMIN = {"id": 1, "rol": "admin", "tenant": "tenant_demo"}
PROFESOR = {"id": 7, "rol": "profesor", "tenant": "tenant_demo"}

ESCRITURA = re.compile(r"^\s*(INSERT|UPDATE|DELETE)\b", re.IGNORECASE)
CONSULTA = re.compile(r"\bSELECT\b", re.IGNORECASE)


# --------------------------------------------------------------------------
# Dobles: cuentan conexiones y consultas sin tocar PostgreSQL
# --------------------------------------------------------------------------


class Registro:
    def __init__(self):
        self.consultas = []
        self.conexiones = []
        self.commits = []

    @property
    def textos(self):
        return [texto for texto, _ in self.consultas]

    @property
    def parametros(self):
        return [params for _, params in self.consultas]


class CursorFalso:
    def __init__(self, registro, filas, unicos, fallo):
        self._registro = registro
        self._filas = list(filas)
        self._unicos = list(unicos)
        self._fallo = fallo
        self.cerrado = False

    def execute(self, query, params=None):
        self._registro.consultas.append((query, params))
        if self._fallo is not None:
            raise self._fallo

    def fetchall(self):
        return list(self._filas)

    def fetchone(self):
        if self._unicos:
            return self._unicos.pop(0)
        return None

    def close(self):
        self.cerrado = True


class ConexionFalsa:
    def __init__(self, registro, filas, unicos, fallo):
        self.cursor_creado = CursorFalso(registro, filas, unicos, fallo)
        self.cerrada = False
        self.revertida = False

    def cursor(self, cursor_factory=None):
        return self.cursor_creado

    def commit(self):
        raise AssertionError("el dominio dashboard es de solo lectura")

    def rollback(self):
        self.revertida = True

    def close(self):
        self.cerrada = True


@pytest.fixture
def espia(monkeypatch):
    def instalar(filas=(), unicos=(), fallo=None, unicos_por_conexion=None):
        registro = Registro()
        secuencias = iter(unicos_por_conexion) if unicos_por_conexion is not None else None

        def fake_get_connection():
            unicos_de_esta_conexion = next(secuencias) if secuencias is not None else unicos
            conexion = ConexionFalsa(registro, filas, unicos_de_esta_conexion, fallo)
            registro.conexiones.append(conexion)
            return conexion

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            registro.commits.append(commit)
            conexion = fake_get_connection()
            cursor = conexion.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            except Exception:
                conexion.rollback()
                raise
            finally:
                cursor.close()
                conexion.close()

        monkeypatch.setattr(dashboard_controller, "get_connection", fake_get_connection)
        monkeypatch.setattr(dashboard_controller, "get_cursor", fake_get_cursor)
        monkeypatch.setattr(permissions, "get_connection", fake_get_connection)
        return registro

    return instalar


def _literales_sql(path):
    arbol = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            texto = ast.get_docstring(nodo, clean=False)
            if texto is not None:
                docstrings.add(texto)
    return [
        nodo.value
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant)
        and isinstance(nodo.value, str)
        and nodo.value not in docstrings
    ]


def _llamadas_execute(path):
    arbol = ast.parse(path.read_text(encoding="utf-8"))
    return [
        nodo
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
        and nodo.func.attr == "execute"
    ]


# --------------------------------------------------------------------------
# Bloque 1: lo que este dominio NO hace. Guardias estructurales
# --------------------------------------------------------------------------


def test_el_dominio_no_escribe_en_la_base():
    """Las 7 entradas son GET y ninguna sentencia es de escritura."""
    for path in (CONTROLADOR, RUTAS, REPOSITORIO):
        escrituras = [texto for texto in _literales_sql(path) if ESCRITURA.match(texto)]
        assert escrituras == [], f"{path.name} contiene una escritura"


def test_el_dominio_no_confirma_ni_revierte():
    """Ninguna funcion es duena de commit o rollback: no abre transaccion propia."""
    for path in (CONTROLADOR, RUTAS, REPOSITORIO):
        fuente = path.read_text(encoding="utf-8")
        assert ".commit()" not in fuente
        assert ".rollback()" not in fuente
        assert "get_cursor(commit=True)" not in fuente


def test_el_dominio_no_toca_storage():
    """Refuta para dashboard el supuesto heredado de archivos.

    Solo branding y plan de clases usan app/services/storage.py. Si alguien
    introduce aqui una escritura de archivo, el rollback de la capa deja de ser
    reversible y esta prueba debe fallar antes.
    """
    for path in (CONTROLADOR, RUTAS, REPOSITORIO):
        assert "storage" not in path.read_text(encoding="utf-8")


def test_las_rutas_del_dominio_no_contienen_sql():
    """Invariante que dejo 6.5: ninguna ruta lleva SQL de dominio."""
    consultas = [texto for texto in _literales_sql(RUTAS) if CONSULTA.search(texto)]
    assert consultas == []


def test_el_sql_del_dominio_vive_solo_en_el_repositorio():
    """Senal esperada de 7.1: la linea base de ocho sentencias baja a cero.

    La version anterior de esta prueba fijaba las ocho **en el controlador** y
    fallo al extraerlas, que era exactamente lo que debia ocurrir. Se sustituye
    por su version positiva, igual que 6.5 hizo con la guardia de `/mis-clases`.
    """
    assert len(_llamadas_execute(CONTROLADOR)) == 0
    assert len(_llamadas_execute(RUTAS)) == 0
    assert len(_llamadas_execute(REPOSITORIO)) == 8


def test_el_dominio_tiene_su_repositorio():
    """Segunda senal esperada de 7.1 de dashboard: el repositorio existe.

    La lista enumera **todos** los repositorios del proyecto, asi que esta
    guardia se dispara en cada migracion de dominio nueva y obliga a
    reconocerla. `notas_repository` se añadio al migrar `notas`, que lo
    convirtio en el septimo, y `ventas_repository` al migrar `ventas`, que lo
    convirtio en el octavo; el de dashboard sigue existiendo y sigue siendo el
    que esta prueba protege.

    La severidad de enumerar el conjunto exacto es **deliberada** y se conserva:
    obliga a que cada migracion nueva se reconozca aqui a proposito.
    """
    repositorios = {
        path.stem for path in (RAIZ / "app" / "repositories").glob("*_repository.py")
    }
    assert "dashboard_repository" in repositorios
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
        "porcentajes_planilla_repository",
        "profesores_repository",
        "reportes_repository",
        "subnotas_planilla_repository",
        "super_admin_repository",
        "ventas_repository",
    }


def test_el_repositorio_recibe_el_cursor_y_no_abre_recursos():
    """El patron de los cuatro repositorios anteriores, aplicado al quinto."""
    fuente = REPOSITORIO.read_text(encoding="utf-8")
    assert "get_connection" not in fuente
    assert "get_cursor" not in fuente
    assert "app.database" not in fuente

    arbol = ast.parse(fuente)
    publicas = [
        nodo
        for nodo in arbol.body
        if isinstance(nodo, ast.FunctionDef) and not nodo.name.startswith("_")
    ]
    assert len(publicas) == 8
    for funcion in publicas:
        assert funcion.args.args[0].arg == "cursor", funcion.name


# --------------------------------------------------------------------------
# Bloque 2: cumpleanos. Las dos funciones que seguian sin caracterizar
# --------------------------------------------------------------------------


def test_cumpleanos_admin_devuelve_el_payload_exacto(espia):
    registro = espia(filas=[(11, "Ana", "Rios", "Quinto A", date(2015, 3, 4))])

    resultado = dashboard_controller.obtener_cumpleanos_admin_controller(dias=11)

    assert resultado == [{
        "estudiante_id": 11,
        "nombre": "Ana",
        "apellido": "Rios",
        "curso": "Quinto A",
        "fecha_nacimiento": "2015-03-04",
    }]
    assert registro.parametros == [(11,)]


def test_cumpleanos_admin_deja_la_fecha_en_nulo_cuando_falta(espia):
    espia(filas=[(11, "Ana", "Rios", None, None)])

    resultado = dashboard_controller.obtener_cumpleanos_admin_controller()

    assert resultado[0]["fecha_nacimiento"] is None
    assert resultado[0]["curso"] is None


def test_cumpleanos_profesor_pasa_los_parametros_en_el_orden_del_cte(espia):
    """El CTE del rango va primero, asi que los dias preceden al profesor."""
    registro = espia(filas=[])

    dashboard_controller.obtener_cumpleanos_profesor_controller(7, dias=9)

    assert registro.parametros == [(9, 7)]


def test_cumpleanos_admin_incluye_estudiantes_sin_curso_y_profesor_no(espia):
    """Diferencia observable entre las dos consultas: LEFT JOIN frente a JOIN."""
    registro_admin = espia(filas=[])
    dashboard_controller.obtener_cumpleanos_admin_controller()
    admin = registro_admin.textos[0]

    registro_profesor = espia(filas=[])
    dashboard_controller.obtener_cumpleanos_profesor_controller(7)
    profesor = registro_profesor.textos[0]

    assert "LEFT JOIN cursos c ON e.curso_id = c.id" in admin
    assert "LEFT JOIN cursos" not in profesor
    assert "JOIN cursos c ON e.curso_id = c.id" in profesor


def test_cumpleanos_solo_cuenta_estudiantes_activos(espia):
    registro = espia(filas=[])

    dashboard_controller.obtener_cumpleanos_admin_controller()

    assert "COALESCE(LOWER(e.estado), 'activo') = 'activo'" in registro.textos[0]


def test_cumpleanos_profesor_exige_asignacion_activa_y_curso_activo(espia):
    registro = espia(filas=[])

    dashboard_controller.obtener_cumpleanos_profesor_controller(7)

    consulta = registro.textos[0]
    assert "a.activo = TRUE" in consulta
    assert "COALESCE(LOWER(c.estado), 'activo') = 'activo'" in consulta


def test_cumpleanos_cubre_el_cambio_de_ano(espia):
    """El rango se compara por MMDD, asi que diciembre a enero necesita el OR."""
    registro = espia(filas=[])

    dashboard_controller.obtener_cumpleanos_admin_controller()

    consulta = registro.textos[0]
    assert "r.inicio_mmdd <= r.fin_mmdd" in consulta
    assert "r.inicio_mmdd > r.fin_mmdd" in consulta
    assert "AT TIME ZONE 'America/Bogota'" in consulta


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [(40, 31), (-5, 0), (7, 7), (0, 0), ("12", 12), ("abc", 7), (None, 7)],
)
def test_normalizar_dias_recorta_en_vez_de_fallar(entrada, esperado):
    """El controlador recorta en silencio; la ruta rechaza con 422.

    Son dos validaciones distintas para el mismo dato: por HTTP el recorte es
    inalcanzable, porque Query(ge=0, le=31) responde antes.
    """
    assert dashboard_controller._normalizar_dias_cumpleanos(entrada) == esperado


def test_cumpleanos_cierra_cursor_y_conexion_aunque_falle(espia):
    registro = espia(fallo=RuntimeError("fallo de infraestructura"))

    with pytest.raises(RuntimeError):
        dashboard_controller.obtener_cumpleanos_admin_controller()

    conexion = registro.conexiones[0]
    assert conexion.cerrada is True
    assert conexion.cursor_creado.cerrado is True


# --------------------------------------------------------------------------
# Bloque 3: precondiciones de permiso. Tampoco estaban caracterizadas
# --------------------------------------------------------------------------


def test_profesor_tiene_curso_responde_si_encuentra_fila(espia):
    registro = espia(unicos=[(1,)])

    assert dashboard_controller.profesor_tiene_curso_controller(7, 4) is True
    assert registro.parametros == [(7, 4)]


def test_profesor_tiene_curso_responde_no_cuando_no_hay_fila(espia):
    espia(unicos=[])

    assert dashboard_controller.profesor_tiene_curso_controller(7, 4) is False


def test_pertenencia_resuelve_la_asignacion_academica_antes_de_comprobar(espia):
    registro = espia(unicos=[(77,), (1,)])

    resultado = dashboard_controller.profesor_tiene_asignacion_en_curso_controller(7, 4, 12)

    assert resultado is True
    assert len(registro.consultas) == 2
    assert "asignacion_academica_id" in registro.textos[0]
    assert registro.parametros[0] == (12,)
    assert registro.parametros[1] == (77, 7, 4)


def test_las_precondiciones_de_permiso_exigen_asignacion_activa(espia):
    """Una asignacion desactivada no sirve como prueba de acceso al rendimiento."""
    registro = espia(unicos=[(77,), (1,)])
    dashboard_controller.profesor_tiene_curso_controller(7, 4)
    dashboard_controller.profesor_tiene_asignacion_en_curso_controller(7, 4, 12)

    assert "AND activo = TRUE" in registro.textos[0]
    assert "AND activo = TRUE" in registro.textos[2]
    assert registro.parametros == [(7, 4), (12,), (77, 7, 4)]


def test_las_precondiciones_comparten_conexion_y_conservan_orden_sql(espia):
    registro = espia(unicos=[(1,), (1,), (77,), (1,)])

    resultado = dashboard_controller.validar_filtro_rendimiento_profesor_controller(
        7,
        4,
        12,
        PROFESOR,
    )

    assert resultado == (True, True, 77)
    assert len(registro.conexiones) == 1
    assert registro.parametros == [(7, 4), (12, 7), (12,), (77, 7, 4)]
    assert registro.conexiones[0].cerrada is True
    assert registro.conexiones[0].cursor_creado.cerrado is True


# --------------------------------------------------------------------------
# Bloque 4: conteo de consultas y de conexiones por camino
# --------------------------------------------------------------------------


def test_cumpleanos_admin_cuesta_una_consulta_y_una_conexion(espia):
    registro = espia(filas=[])

    dashboard_controller.obtener_cumpleanos_admin_controller()

    assert (len(registro.consultas), len(registro.conexiones)) == (1, 1)


def test_cumpleanos_profesor_cuesta_una_consulta_y_una_conexion(espia):
    registro = espia(filas=[])

    dashboard_controller.obtener_cumpleanos_profesor_controller(7)

    assert (len(registro.consultas), len(registro.conexiones)) == (1, 1)


def test_inasistencias_cuesta_una_consulta_y_una_conexion(espia):
    registro = espia(filas=[])

    dashboard_controller.obtener_inasistencias_profesor_controller(7)

    assert (len(registro.consultas), len(registro.conexiones)) == (1, 1)
    assert registro.commits == [False]


def test_ranking_de_un_admin_cuesta_dos_consultas_y_una_conexion(espia):
    """El admin sale de require_asignacion_access sin consultar."""
    registro = espia(filas=[], unicos=[(77,)])

    dashboard.obtener_ranking_rendimiento(12, periodo=2, current_user=ADMIN)

    assert (len(registro.consultas), len(registro.conexiones)) == (2, 1)


def test_ranking_de_un_profesor_cuesta_tres_consultas_y_dos_conexiones(espia):
    """La comprobacion de acceso abre su propia conexion antes del controlador."""
    registro = espia(filas=[], unicos=[(77,)])

    dashboard.obtener_ranking_rendimiento(12, periodo=2, current_user=PROFESOR)

    assert (len(registro.consultas), len(registro.conexiones)) == (3, 2)


def test_ranking_mejor_de_un_profesor_cuesta_lo_mismo_que_el_bajo(espia):
    registro = espia(filas=[], unicos=[(77,)])

    dashboard.obtener_ranking_mejor_rendimiento(12, periodo=2, current_user=PROFESOR)

    assert (len(registro.consultas), len(registro.conexiones)) == (3, 2)


def test_notas_sin_asignacion_cuestan_dos_consultas_y_dos_conexiones(espia):
    registro = espia(filas=[], unicos=[(1,)])

    dashboard.obtener_notas_bajas_profesor(
        7, curso_id=4, asignacion_id=None, current_user=PROFESOR
    )

    assert (len(registro.consultas), len(registro.conexiones)) == (2, 2)


def test_notas_con_asignacion_de_un_profesor_cuestan_cinco_consultas_y_dos_conexiones(espia):
    """La lectura reutiliza el id academico resuelto por las precondiciones."""
    registro = espia(
        filas=[],
        unicos_por_conexion=[[(1,), (1,), (77,), (1,)], []],
    )

    dashboard.obtener_notas_bajas_profesor(
        7, curso_id=4, asignacion_id=12, current_user=PROFESOR
    )

    assert (len(registro.consultas), len(registro.conexiones)) == (5, 2)
    resoluciones = [texto for texto in registro.textos if "asignacion_academica_id" in texto]
    assert len(resoluciones) == 1


def test_notas_con_asignacion_de_un_admin_ahorran_la_comprobacion_de_acceso(espia):
    registro = espia(
        filas=[],
        unicos_por_conexion=[[(1,), (77,), (1,)], []],
    )

    dashboard.obtener_notas_bajas_profesor(
        7, curso_id=4, asignacion_id=12, current_user=ADMIN
    )

    assert (len(registro.consultas), len(registro.conexiones)) == (4, 2)


def test_ningun_camino_del_dominio_depende_del_numero_de_estudiantes(espia):
    """No hay N+1: el conteo no cambia con el tamano del resultado."""
    filas_muchas = [(i, f"E{i}", "Rios", "Quinto A", date(2015, 3, 4)) for i in range(50)]

    registro_una = espia(filas=[(1, "Ana", "Rios", "Quinto A", date(2015, 3, 4))])
    dashboard_controller.obtener_cumpleanos_admin_controller()

    registro_muchas = espia(filas=filas_muchas)
    resultado = dashboard_controller.obtener_cumpleanos_admin_controller()

    assert len(resultado) == 50
    assert len(registro_una.consultas) == len(registro_muchas.consultas) == 1


# --------------------------------------------------------------------------
# Bloque 5: el calculo es el contrato
# --------------------------------------------------------------------------


def test_el_dominio_usa_dos_definiciones_distintas_de_promedio(espia):
    """Registrado, no corregido: no son la misma cifra.

    Notas altas y bajas promedian los promedios por clase; los rankings
    promedian las notas planas. Con 4,0 en una clase de dos notas y 2,0 en otra
    de seis, la primera formula da 3,00 y la segunda 2,50.
    """
    registro_notas = espia(filas=[])
    dashboard_controller.obtener_notas_bajas_profesor_controller(7, 4)

    registro_ranking = espia(filas=[], unicos=[(77,)])
    dashboard_controller.obtener_ranking_rendimiento_controller(12, 1)

    assert "TRUNC(AVG(promedio_clase), 2)" in registro_notas.textos[0]
    assert "AVG(CAST(n.nota AS numeric)) as promedio_clase" in registro_notas.textos[0]
    assert "TRUNC(AVG(CAST(n.nota AS numeric)), 2)" in registro_ranking.textos[1]
    assert "promedio_clase" not in registro_ranking.textos[1]


def test_las_notas_se_truncan_a_dos_decimales_y_no_se_redondean(espia):
    """TRUNC, no ROUND. 2,999 se presenta como 2,99 y sigue contando como baja."""
    registro = espia(filas=[("Ana Rios", "Quinto A", "Matematicas", 2.99)])

    resultado = dashboard_controller.obtener_notas_bajas_profesor_controller(7, 4)

    assert "TRUNC" in registro.textos[0]
    assert "ROUND" not in registro.textos[0]
    assert resultado[0]["promedio"] == 2.99


def test_las_notas_bajas_devuelven_como_mucho_cinco_filas(espia):
    registro = espia(filas=[])

    dashboard_controller.obtener_notas_bajas_profesor_controller(7, 4)

    assert "LIMIT 5" in registro.textos[0]


def test_las_inasistencias_devuelven_los_tres_peores_de_cada_curso(espia):
    registro = espia(filas=[])

    dashboard_controller.obtener_inasistencias_profesor_controller(7)

    consulta = registro.textos[0]
    assert "WHERE posicion_curso <= 3" in consulta
    assert "PARTITION BY c.id" in consulta
    assert "a.estado ILIKE 'ausente'" in consulta


def test_el_sql_dinamico_de_notas_no_recibe_entrada_del_cliente(espia):
    """Guarda: comparador, orden y filtro salen de literales del propio codigo.

    Hoy no es inyectable. Ninguna extraccion futura debe abrir esa construccion
    a un valor que venga de la peticion.
    """
    registro = espia(filas=[])

    dashboard_controller.obtener_notas_altas_profesor_controller(7, 4, asignacion_id=None)

    consulta = registro.textos[0]
    assert "HAVING TRUNC(AVG(promedio_clase), 2) >= 3.0" in consulta
    assert "ORDER BY promedio DESC" in consulta
    assert "AND asi.id = %s" not in consulta
    assert registro.parametros[0] == (7, 4, None)


def test_las_dos_consultas_de_ranking_son_gemelas_salvo_el_signo(espia):
    """Cuarta pareja de literales gemelos del programa. No se unifica sin orden."""
    registro_bajo = espia(filas=[], unicos=[(77,)])
    dashboard_controller.obtener_ranking_rendimiento_controller(12, 1)

    registro_alto = espia(filas=[], unicos=[(77,)])
    dashboard_controller.obtener_ranking_mejor_rendimiento_controller(12, 1)

    bajo = registro_bajo.textos[1]
    alto = registro_alto.textos[1]
    assert bajo != alto
    assert bajo.replace("< 3.0", ">= 3.0").replace("ASC", "DESC") == alto
