"""Fase 2 del observador unificado: la lectura de la bitacora.

Ver `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`. Fija lo que el documento
llama invariantes, no el detalle de la implementacion: quien puede leer, que el
periodo nunca oculta historial, que se pide **una sola** conexion y que no
existe forma de borrar.
"""
from contextlib import contextmanager

import pytest
from fastapi import HTTPException

from app.core import permissions
from app.routes import observador


FILA = (
    "primaria",              # nivel del curso
    12,                      # id
    7,                       # profesor_id
    "Ana",                   # nombre
    "Gomez",                 # apellido
    "Matematicas",           # materia
    1,                       # periodo
    False,                   # positiva
    "Se para mucho.",        # conductual
    "",                      # cognitivo
    "",                      # lenguaje
    "2026-03-20T14:03:00Z",  # creada_en
    None,                    # editada_en
    None,                    # editada_por
)

# Un alumno real que todavia no tiene ninguna anotacion: la consulta arranca en
# `estudiantes`, asi que devuelve su nivel y el resto en NULL. Hoy es el caso de
# TODOS los alumnos, porque la escritura no existe.
FILA_SIN_ANOTACIONES = ("preescolar",) + (None,) * 13

PROFESOR = {"id": 7, "rol": "profesor"}
ADMIN = {"id": 1, "rol": "admin"}


class CursorFalso:
    def __init__(self, filas=(), fila_permiso=(1,)):
        self.filas = list(filas)
        self.fila_permiso = fila_permiso
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.fila_permiso

    def fetchall(self):
        return self.filas


class ConexionFalsa:
    def __init__(self):
        self.cursor_obj = CursorFalso()

    def cursor(self, **_kwargs):
        return self.cursor_obj

    def close(self):
        pass


class ContadorDeConexiones:
    """Cuenta cuantas veces se pide una conexion al pool."""

    def __init__(self):
        self.abiertas = 0

    def __call__(self):
        self.abiertas += 1
        return ConexionFalsa()


def _ruta_de_lectura():
    return next(
        r
        for r in observador.router.routes
        if getattr(r, "path", "") == "/observador/{estudiante_id}"
    )


def cursor_de(monkeypatch, filas=(FILA,), fila_permiso=(1,)):
    cursor = CursorFalso(filas=filas, fila_permiso=fila_permiso)

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        yield cursor

    monkeypatch.setattr(observador, "get_cursor", fake_get_cursor)
    return cursor


# ---------------------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------------------


def test_un_profesor_del_alumno_ve_la_bitacora(monkeypatch):
    cursor_de(monkeypatch)

    resultado = observador.obtener_observador(55, None, PROFESOR)

    assert len(resultado["anotaciones"]) == 1
    assert resultado["anotaciones"][0]["conductual"] == "Se para mucho."


def test_un_profesor_que_no_comparte_curso_no_la_ve(monkeypatch):
    """El guard no encuentra asignacion compartida: 403, no lista vacia.

    Devolver una lista vacia diria que el nino no tiene anotaciones, que es
    mentira y ademas revelaria que el alumno existe.
    """
    cursor_de(monkeypatch, fila_permiso=None)

    with pytest.raises(HTTPException) as exc:
        observador.obtener_observador(55, None, PROFESOR)

    assert exc.value.status_code == 403


def test_el_admin_lee_cualquier_bitacora_sin_compartir_curso(monkeypatch):
    """Decision 9 del documento, primera mitad: el admin ve todo.

    La segunda mitad -que NO edita- se fija en la fase 3, y es una excepcion
    deliberada a la norma del proyecto.
    """
    cursor = cursor_de(monkeypatch)

    resultado = observador.obtener_observador(55, None, ADMIN)

    assert len(resultado["anotaciones"]) == 1
    # El admin ni siquiera consulta el permiso: solo queda la consulta de lectura.
    assert len(cursor.calls) == 1


def test_un_403_del_guard_no_se_convierte_en_500(monkeypatch):
    """El guard vive dentro del `try`, y `HTTPException` tambien es `Exception`:
    sin el `except HTTPException` que va primero, un permiso denegado saldria
    como error del servidor. El frontend muestra `detail` en pantalla."""
    cursor_de(monkeypatch)

    def denegar(*_a, **_k):
        raise HTTPException(status_code=403, detail="No autorizado")

    monkeypatch.setattr(observador, "require_estudiante_access", denegar)

    with pytest.raises(HTTPException) as exc:
        observador.obtener_observador(55, None, PROFESOR)

    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# El nivel del curso, y el alumno sin anotaciones
# ---------------------------------------------------------------------------


def test_el_nivel_del_curso_llega_fuera_de_las_anotaciones(monkeypatch):
    """Es del alumno, no de la anotacion. Repetirlo en cada una seria ruido, y
    ademas no llegaria cuando no hay ninguna."""
    cursor_de(monkeypatch)

    resultado = observador.obtener_observador(55, None, PROFESOR)

    assert resultado["nivel"] == "primaria"
    assert "nivel" not in resultado["anotaciones"][0]


def test_un_alumno_sin_anotaciones_devuelve_el_nivel_igual(monkeypatch):
    """La prueba que justifica arrancar la consulta en `estudiantes`.

    Si arrancara en las anotaciones, un alumno sin ninguna daria cero filas y
    con ellas ningun nivel: la pantalla no podria ni escribir su titulo. Y no es
    un caso raro, hoy es el caso de todos.
    """
    cursor_de(monkeypatch, filas=[FILA_SIN_ANOTACIONES])

    resultado = observador.obtener_observador(55, None, PROFESOR)

    assert resultado["nivel"] == "preescolar"
    assert resultado["anotaciones"] == []


def test_un_curso_sin_nivel_no_rompe_la_lectura(monkeypatch):
    """`cursos.nivel` es nulable y al decidirlo habia 20 cursos asi en
    tenant_colegio_1. La pantalla los trata como primaria."""
    cursor_de(monkeypatch, filas=[(None,) + FILA[1:]])

    resultado = observador.obtener_observador(55, None, PROFESOR)

    assert resultado["nivel"] is None
    assert len(resultado["anotaciones"]) == 1


def test_un_estudiante_que_no_existe_no_se_confunde_con_uno_vacio(monkeypatch):
    """Cero filas solo puede significar que el estudiante no existe: uno real
    siempre trae al menos su fila de relleno. En pantalla son mensajes
    distintos, asi que no pueden dar la misma respuesta."""
    cursor_de(monkeypatch, filas=[])

    with pytest.raises(HTTPException) as exc:
        observador.obtener_observador(9999, None, ADMIN)

    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# El periodo es una etiqueta, no un filtro obligatorio
# ---------------------------------------------------------------------------


def test_sin_periodo_devuelve_el_ano_entero(monkeypatch):
    """Invariante 5: cambiar de periodo nunca oculta historial, y todas es el
    caso por defecto."""
    cursor = cursor_de(monkeypatch)

    observador.obtener_observador(55, None, PROFESOR)

    consulta, parametros = cursor.calls[-1]
    assert "a.periodo = %s" not in consulta
    assert parametros == (55,)


def test_con_periodo_filtra_por_esa_etiqueta(monkeypatch):
    cursor = cursor_de(monkeypatch)

    observador.obtener_observador(55, 2, PROFESOR)

    consulta, parametros = cursor.calls[-1]
    assert "a.periodo = %s" in consulta
    assert parametros == (2, 55)


def test_el_filtro_de_periodo_va_en_la_union_y_no_en_el_where(monkeypatch):
    """La trampa de este endpoint.

    En el `WHERE`, filtrar por periodo descartaria tambien la fila del
    estudiante cuando ese periodo no tuviera anotaciones, y la pantalla se
    quedaria sin nivel justo al cambiar de periodo. En el `ON` de la union
    izquierda, el estudiante sobrevive siempre.
    """
    cursor = cursor_de(monkeypatch)

    observador.obtener_observador(55, 2, PROFESOR)

    consulta = cursor.calls[-1][0]
    antes_del_where, _, despues_del_where = consulta.partition("WHERE")
    assert "a.periodo = %s" in antes_del_where
    assert "a.periodo" not in despues_del_where


def test_las_uniones_del_alumno_son_izquierdas(monkeypatch):
    """Las dos `LEFT JOIN` son lo que sostiene los dos casos de arriba, y las
    dos se pierden con solo borrar una palabra al reordenar la consulta:

    - `cursos`, porque `estudiantes.curso_id` es NULABLE. Con union interna, un
      alumno sin curso desapareceria de su propia bitacora: sin error y sin
      aviso, la pantalla diria que no existe.
    - `observador_anotaciones`, porque sin ella el alumno sin anotaciones
      desapareceria igual.

    No lo cubre ninguna prueba de comportamiento: los cursores falsos no
    ejecutan SQL, y al escribir esto no habia ningun alumno sin curso en la base
    con el que comprobarlo de verdad.
    """
    cursor = cursor_de(monkeypatch)

    observador.obtener_observador(55, None, PROFESOR)

    consulta = cursor.calls[-1][0]
    assert "FROM estudiantes e" in consulta, "la consulta arranca en el estudiante"
    assert "LEFT JOIN cursos c" in consulta
    assert "LEFT JOIN observador_anotaciones a" in consulta


def test_el_periodo_solo_admite_del_1_al_4():
    """Misma regla que el CHECK de la tabla, para que un periodo imposible salga
    como 422 y no como una lista vacia que parece un alumno sin anotaciones.

    Se mira lo que FastAPI validara de verdad -el `dependant` de la ruta-, no la
    firma de la funcion: es lo que decide la respuesta HTTP.
    """
    ruta = _ruta_de_lectura()
    periodo = next(p for p in ruta.dependant.query_params if p.name == "periodo")
    limites = {type(m).__name__.lower(): m for m in periodo.field_info.metadata}

    assert limites["ge"].ge == 1
    assert limites["le"].le == 4
    assert periodo.field_info.default is None, "sin periodo devuelve todas"
    assert not periodo.field_info.is_required(), (
        "el periodo es una etiqueta, no un filtro obligatorio"
    )


# ---------------------------------------------------------------------------
# Orden, coste y forma de la respuesta
# ---------------------------------------------------------------------------


def test_la_mas_nueva_va_primero_y_el_empate_se_rompe(monkeypatch):
    """Dos anotaciones de la misma transaccion comparten `creada_en`, porque
    `now()` es el instante de la transaccion y no el de la fila. Sin desempate,
    su orden entre si podria cambiar entre dos lecturas identicas."""
    cursor = cursor_de(monkeypatch)

    observador.obtener_observador(55, None, PROFESOR)

    consulta = cursor.calls[-1][0]
    assert "ORDER BY a.creada_en DESC NULLS LAST, a.id DESC NULLS LAST" in consulta


def test_la_lectura_pide_una_sola_conexion_al_pool(monkeypatch):
    """El motivo de existir de esta funcionalidad, fijado por asercion.

    La pantalla vieja hacia una peticion HTTP por alumno y con 12 tardaba
    16-20 s, por encima del limite de 10 s del frontend. Aqui el guard corre
    sobre el cursor que ya abrio la ruta: si abriera el suyo serian dos
    arranques de conexion, y cada arranque cuesta dos consultas de arranque
    antes de la util.
    """
    aperturas = []
    cursor = CursorFalso(filas=[FILA])

    @contextmanager
    def fake_get_cursor(commit=False, cursor_factory=None):
        aperturas.append(commit)
        yield cursor

    contador = ContadorDeConexiones()
    monkeypatch.setattr(observador, "get_cursor", fake_get_cursor)
    monkeypatch.setattr(permissions, "get_connection", contador)

    observador.obtener_observador(55, None, PROFESOR)

    assert aperturas == [False]
    assert contador.abiertas == 0


def test_el_nivel_no_cuesta_una_consulta_aparte(monkeypatch):
    """Sale de la misma consulta que las anotaciones. Contra Neon lo que se paga
    es el numero de idas y vueltas, no lo complicada que sea cada una."""
    cursor = cursor_de(monkeypatch)

    observador.obtener_observador(55, None, PROFESOR)

    # Una del permiso y una de la lectura. Ninguna mas.
    assert len(cursor.calls) == 2


def test_un_fallo_de_base_no_filtra_el_mensaje_de_postgresql(monkeypatch, caplog):
    """El frontend muestra `detail` tal cual. El texto de psycopg2 lleva el DSN
    y nombres internos, asi que va al log y nunca a la pantalla."""
    secreto = "FATAL: password authentication failed for user admin"
    cursor_de(monkeypatch)

    def revienta(*_a, **_k):
        raise RuntimeError(secreto)

    monkeypatch.setattr(observador.observador_repository, "leer_bitacora", revienta)

    with caplog.at_level("ERROR"):
        with pytest.raises(HTTPException) as exc:
            observador.obtener_observador(55, None, PROFESOR)

    assert exc.value.status_code == 500
    assert secreto not in str(exc.value.detail)
    assert caplog.records and caplog.records[-1].exc_info is not None
    assert secreto in caplog.text


def test_la_respuesta_lleva_profesor_id_para_pintar_editar(monkeypatch):
    """La pantalla decide con esto si muestra el boton Editar. Es comodidad
    visual: la regla de verdad la impone el servidor."""
    cursor_de(monkeypatch)

    anotacion = observador.obtener_observador(55, None, PROFESOR)["anotaciones"][0]

    assert anotacion["profesor_id"] == 7
    assert anotacion["profesor"] == "Ana Gomez"
    assert anotacion["materia"] == "Matematicas"
    assert anotacion["positiva"] is False


@pytest.mark.parametrize("apellido", [None, ""])
def test_el_nombre_del_profesor_sale_limpio_sin_apellido(monkeypatch, apellido):
    """`nombre` y `apellido` son nulables en el esquema, y ademas nada impide
    que se guarde la cadena vacia. Los dos casos deben dar `Ana`, sin `None`
    pegado detras ni un espacio sobrante que se vea en la pantalla."""
    cursor_de(monkeypatch, filas=[FILA[:4] + (apellido,) + FILA[5:]])

    anotacion = observador.obtener_observador(55, None, PROFESOR)["anotaciones"][0]

    assert anotacion["profesor"] == "Ana"


# El invariante 1 -nadie borra- se fija en
# `tests/test_observador_escritura.py::test_no_existe_endpoint_de_borrado`, que
# es donde viven los metodos de escritura. Tenerlo aqui tambien lo duplicaba, y
# la copia de aqui se quedo obsoleta en cuanto aparecieron el POST y el PUT.
