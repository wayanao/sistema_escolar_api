"""Caracterizacion del dominio planilla migrado en la subcapa 1.4j.

Cubre los tres sitios: los dos de planilla_controller y el de
planilla_excel_controller.

Lo que mas importa fijar:
- registrar_nota_planilla_controller escribe la celda en la MISMA transaccion.
  Desde 2026-11-23 una nota que ya existe se cambia en su lugar (conserva su
  `id` y su tarjeta en Boletin final) y se quitan las repetidas; una que no
  existia se inserta. Siguen siendo dos sentencias y sigue quedando una sola
  nota por descripcion.
- planilla_excel_controller descarta la descripcion "Desde React", una cadena
  magica heredada, y devuelve el promedio como CADENA VACIA cuando el estudiante
  no tiene ninguna nota numerica.
"""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app.controllers import planilla_controller, planilla_excel_controller

PROFESOR = {"id": 3, "rol": "profesor"}


@pytest.fixture(autouse=True)
def guardia_del_anio(monkeypatch):
    """Año lectivo, paso 3.7: la guardia de escritura se dobla aqui, igual que
    los resolutores. Sus pruebas viven en `test_anio_lectivo_guardia.py` y la
    cuenta `test_anio_lectivo_guardia_conteos.py`."""
    llamadas = []
    monkeypatch.setattr(
        planilla_controller,
        "exigir_asignacion_editable",
        lambda _cursor, asignacion_id, usuario: llamadas.append((asignacion_id, usuario)),
    )
    return llamadas


@pytest.fixture(autouse=True)
def sin_subnotas(monkeypatch):
    """Subnotas, paso A1: la comprobacion del 409 se dobla aqui como la guardia
    del año, y responde "sin subnotas", que es el caso de estas pruebas. Sus
    pruebas viven en `test_subnotas_planilla.py`."""
    llamadas = []
    monkeypatch.setattr(
        planilla_controller.subnotas_planilla_repository,
        "hay_subnotas_calificadas",
        lambda _cursor, *argumentos: llamadas.append(argumentos) or False,
    )
    return llamadas


class CursorFalso:
    def __init__(self, fila=None, filas=(), respuestas=None):
        self.fila = fila
        self.filas = list(filas)
        # Si llega, cada `fetchone` devuelve la siguiente; si no, siempre `fila`.
        self.respuestas = None if respuestas is None else list(respuestas)
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        if self.respuestas is not None:
            return self.respuestas.pop(0)
        return self.fila

    def fetchall(self):
        return self.filas


def _instalador(modulo, monkeypatch):
    def instalar(fila=None, filas=(), asignacion_resuelta=77, nivel_curso=None, respuestas=None):
        cursor = CursorFalso(fila=fila, filas=filas, respuestas=respuestas)
        commits = []
        resueltos = []
        niveles_consultados = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        def fake_resolver(_cursor, asignacion_id):
            resueltos.append(asignacion_id)
            return asignacion_resuelta

        def fake_resolver_nivel(_cursor, asignacion_id):
            niveles_consultados.append(asignacion_id)
            return nivel_curso

        monkeypatch.setattr(modulo, "get_cursor", fake_get_cursor)
        monkeypatch.setattr(
            modulo, "resolver_asignacion_academica_id_cursor", fake_resolver
        )
        if hasattr(modulo, "resolver_nivel_curso_cursor"):
            monkeypatch.setattr(
                modulo, "resolver_nivel_curso_cursor", fake_resolver_nivel
            )
        return cursor, commits, resueltos, niveles_consultados

    return instalar


@pytest.fixture
def cursor_planilla(monkeypatch):
    monkeypatch.setattr(
        planilla_controller,
        "validar_estudiante_asignacion",
        lambda _e, _a, cursor=None: True,
    )
    return _instalador(planilla_controller, monkeypatch)


@pytest.fixture
def cursor_excel(monkeypatch):
    return _instalador(planilla_excel_controller, monkeypatch)


DATOS = SimpleNamespace(
    estudiante_id=11,
    asignacion_id=12,
    periodo=2,
    nota=4.5,
    descripcion="  Parcial 1  ",
    tipo_evaluacion="numerica",
    valoracion=None,
)


def test_registrar_nota_cambia_la_existente_en_su_lugar(cursor_planilla):
    """2026-11-23: la nota que ya existe no se borra; se cambia y conserva su
    `id` (asi su tarjeta no se mueve en Boletin final). Despues se quitan las
    repetidas, las que antes quitaba el borrado previo."""
    cursor, commits, resueltos, _ = cursor_planilla(fila=(901,))

    respuesta = planilla_controller.registrar_nota_planilla_controller(DATOS, usuario=PROFESOR)

    (cambio, params_cambio), (repetidas, params_repetidas) = cursor.calls
    assert cambio.lstrip().startswith("UPDATE notas_detalle")
    assert "TRIM(%s)" in cambio
    assert "SELECT MIN(id) FROM notas_detalle" in cambio
    assert params_cambio == (4.5, "  Parcial 1  ", "numerica", None, 11, 77, 2, "  Parcial 1  ")
    assert repetidas.lstrip().startswith("DELETE FROM notas_detalle")
    assert "id <> %s" in repetidas
    assert params_repetidas == (11, 77, 2, "  Parcial 1  ", 901)
    # Un solo bloque para las dos sentencias.
    assert commits == [True]
    assert resueltos == [12]
    assert respuesta == {"mensaje": "Nota registrada correctamente", "nota_id": 901}


def test_registrar_nota_nueva_la_inserta(cursor_planilla):
    """Si no habia nota, el UPDATE no cambia nada y se inserta, como siempre."""
    cursor, commits, _, _ = cursor_planilla(respuestas=[None, (902,)])

    respuesta = planilla_controller.registrar_nota_planilla_controller(DATOS, usuario=PROFESOR)

    (cambio, _), (insercion, params_insercion) = cursor.calls
    assert cambio.lstrip().startswith("UPDATE notas_detalle")
    assert "INSERT INTO notas_detalle" in insercion
    assert "TRIM(%s)" in insercion
    assert params_insercion == (11, 77, 2, 4.5, "  Parcial 1  ", "numerica", None)
    assert commits == [True]
    assert respuesta == {"mensaje": "Nota registrada correctamente", "nota_id": 902}


def test_registrar_nota_de_desarrollo_guarda_valoracion_y_no_nota(cursor_planilla):
    cursor, _, _, _ = cursor_planilla(fila=(902,))
    datos = SimpleNamespace(
        estudiante_id=11, asignacion_id=12, periodo=1, nota=4.5,
        descripcion="Ensayo", tipo_evaluacion="desarrollo", valoracion="Alto",
    )

    planilla_controller.registrar_nota_planilla_controller(datos, usuario=PROFESOR)

    _, params = cursor.calls[0]  # el UPDATE de la nota
    assert params[0] is None
    assert params[2] == "desarrollo"
    assert params[3] == "Alto"


def test_registrar_nota_en_curso_preescolar_fuerza_desarrollo_aunque_pidan_numerica(
    cursor_planilla,
):
    """El nivel del curso manda sobre lo que pida el cliente.

    Antes de esta funcionalidad, tipo_evaluacion venia siempre de data. Ahora
    un curso preescolar guarda "desarrollo" aunque el cliente mande
    "numerica" -un frontend desactualizado, un bug, o una llamada directa al
    servidor no pueden colarse.
    """
    cursor, _, resueltos, niveles = cursor_planilla(fila=(903,), nivel_curso="preescolar")
    datos = SimpleNamespace(
        estudiante_id=11, asignacion_id=12, periodo=1, nota=4.5,
        descripcion="Parcial 1", tipo_evaluacion="numerica", valoracion=None,
    )

    planilla_controller.registrar_nota_planilla_controller(datos, usuario=PROFESOR)

    _, params = cursor.calls[0]  # el UPDATE de la nota
    assert params[0] is None  # nota numerica descartada
    assert params[2] == "desarrollo"
    # El nivel se consulta sobre la asignacion academica YA resuelta (77),
    # no sobre la asignacion original que llego en el payload (12).
    assert niveles == [77]
    assert resueltos == [12]


def test_registrar_nota_en_curso_primaria_fuerza_numerica_aunque_pidan_desarrollo(
    cursor_planilla,
):
    """Primaria fuerza numerica, igual que preescolar fuerza desarrollo:
    ningun nivel definido es libre. Solo un curso sin nivel sigue siendolo
    (ver el siguiente test)."""
    cursor, _, _, niveles = cursor_planilla(fila=(904,), nivel_curso="primaria")
    datos = SimpleNamespace(
        estudiante_id=11, asignacion_id=12, periodo=1, nota=4.5,
        descripcion="Ensayo", tipo_evaluacion="desarrollo", valoracion="Alto",
    )

    planilla_controller.registrar_nota_planilla_controller(datos, usuario=PROFESOR)

    _, params = cursor.calls[0]  # el UPDATE de la nota
    assert params[0] == 4.5  # nota numerica si se guarda
    assert params[2] == "numerica"
    assert params[3] is None  # valoracion descartada
    assert niveles == [77]


def test_registrar_nota_sin_nivel_definido_mantiene_comportamiento_actual(
    cursor_planilla,
):
    """Un curso sin `nivel` (NULL) no fuerza nada: es el estado de todos los
    cursos existentes antes de esta funcionalidad."""
    cursor, _, _, niveles = cursor_planilla(fila=(905,), nivel_curso=None)

    planilla_controller.registrar_nota_planilla_controller(DATOS, usuario=PROFESOR)

    _, params = cursor.calls[0]  # el UPDATE de la nota
    assert params[2] == "numerica"
    assert niveles == [77]


def test_registrar_nota_rechaza_estudiante_ajeno_sin_escribir_nada(cursor_planilla, monkeypatch):
    cursor, commits, _, _ = cursor_planilla()
    monkeypatch.setattr(
        planilla_controller,
        "validar_estudiante_asignacion",
        lambda _e, _a, cursor=None: False,
    )

    respuesta = planilla_controller.registrar_nota_planilla_controller(DATOS, usuario=PROFESOR)

    assert respuesta == {"error": "El estudiante no pertenece a esta asignación"}
    # La validacion ahora ocurre dentro del bloque que ya abria el controlador,
    # asi que se pide un cursor -antes eran dos conexiones-, pero el rechazo
    # sigue sin ejecutar ni un DELETE ni un INSERT.
    assert cursor.calls == []
    assert commits == [True]


def test_eliminar_tipo_borra_la_columna_del_periodo(cursor_planilla):
    cursor, commits, resueltos, _ = cursor_planilla()

    respuesta = planilla_controller.eliminar_tipo_controller(12, "Parcial 1", periodo=3, usuario=PROFESOR)

    query, params = cursor.calls[0]
    assert "DELETE FROM notas_detalle" in query
    assert "LOWER(TRIM(descripcion)) = LOWER(TRIM(%s))" in query
    assert params == (77, 3, "Parcial 1")
    assert resueltos == [12]
    assert commits == [True]
    assert respuesta == {"mensaje": "Tipo eliminado correctamente"}


def test_eliminar_tipo_usa_periodo_uno_por_defecto(cursor_planilla):
    cursor, _, _, _ = cursor_planilla()

    planilla_controller.eliminar_tipo_controller(12, "Parcial 1", usuario=PROFESOR)

    _, params = cursor.calls[0]
    assert params == (77, 1, "Parcial 1")


def test_excel_agrupa_notas_por_estudiante_y_calcula_promedio(cursor_excel):
    filas = [
        (11, "Ana", "Ríos", "Matemáticas", "Parcial 1", 4.0, "numerica", None, 101),
        (11, "Ana", "Ríos", "Matemáticas", "Parcial 2", 3.0, "numerica", None, 102),
    ]
    cursor, commits, resueltos, _ = cursor_excel(filas=filas)

    resultado = planilla_excel_controller.planilla_excel_controller(12, periodo=2)

    _, params = cursor.calls[0]
    assert params == (2, 77)
    assert resueltos == [12]
    assert commits == [False]
    assert resultado["columnas"] == ["Parcial 1", "Parcial 2"]
    assert resultado["data"][0]["promedio"] == 3.5
    assert resultado["data"][0]["notas"] == {"Parcial 1": 4.0, "Parcial 2": 3.0}


def test_excel_ordena_columnas_por_orden_de_creacion_no_alfabetico(cursor_excel):
    filas = [
        (11, "Ana", "Ríos", "Matemáticas", "Segundo parcial", 3.0, "numerica", None, 202),
        (11, "Ana", "Ríos", "Matemáticas", "Autoevaluación", 4.0, "numerica", None, 201),
    ]
    cursor_excel(filas=filas)

    resultado = planilla_excel_controller.planilla_excel_controller(12)

    assert resultado["columnas"] == ["Autoevaluación", "Segundo parcial"]


def test_excel_descarta_la_descripcion_heredada_desde_react(cursor_excel):
    filas = [(11, "Ana", "Ríos", "Matemáticas", "Desde React", 4.0, "numerica", None, 301)]
    cursor_excel(filas=filas)

    resultado = planilla_excel_controller.planilla_excel_controller(12)

    assert resultado["columnas"] == []
    assert resultado["data"][0]["notas"] == {}


def test_excel_devuelve_promedio_como_cadena_vacia_si_no_hay_notas_numericas(cursor_excel):
    filas = [(11, "Ana", "Ríos", "Matemáticas", "Ensayo", None, "desarrollo", "Alto", 401)]
    cursor_excel(filas=filas)

    resultado = planilla_excel_controller.planilla_excel_controller(12)

    assert resultado["data"][0]["promedio"] == ""
    assert resultado["data"][0]["valoraciones"] == {"Ensayo": "Alto"}


def test_excel_excluye_las_de_desarrollo_del_promedio(cursor_excel):
    filas = [
        (11, "Ana", "Ríos", "Matemáticas", "Parcial 1", 4.0, "numerica", None, 501),
        (11, "Ana", "Ríos", "Matemáticas", "Ensayo", 1.0, "desarrollo", "Alto", 502),
    ]
    cursor_excel(filas=filas)

    resultado = planilla_excel_controller.planilla_excel_controller(12)

    assert resultado["data"][0]["promedio"] == 4.0


def test_excel_ordena_por_apellido_y_nombre(cursor_excel):
    filas = [
        (12, "Beto", "Sáenz", "Matemáticas", "Parcial 1", 3.0, "numerica", None, 601),
        (11, "Ana", "Ríos", "Matemáticas", "Parcial 1", 4.0, "numerica", None, 602),
    ]
    cursor_excel(filas=filas)

    resultado = planilla_excel_controller.planilla_excel_controller(12)

    assert [e["apellido"] for e in resultado["data"]] == ["Ríos", "Sáenz"]
