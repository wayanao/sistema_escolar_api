"""SISBÉN y lugar de residencia, paso S1 (docs/funcionalidades/SISBEN_RESIDENCIA.md).

Ocho datos nuevos de la ficha del estudiante. Se guardan aparte de los 34
datos globales, sin mover esa tupla, y solo si llegó alguno: una pestaña
abierta antes del cambio no los manda y no debe borrarlos. Si llega alguno, se
reemplazan los ocho, para que el SISBÉN nunca quede a medias.

Con dobles de los repositorios: no se escribe en ningún tenant real. Los
caminos de matricular desde una admisión están en
``test_admisiones_matricular.py``.
"""

import asyncio
import json
from contextlib import contextmanager

import pytest
from pydantic import ValidationError

from app.controllers import estudiante_controller
from app.repositories import estudiantes_repository
from app.schemas.estudiante import EstudianteCreate


OCHO = (
    "sisben",
    "sisben_grupo",
    "sisben_subgrupo",
    "sisben_nivel",
    "barrio",
    "municipio",
    "zona_residencia",
    "punto_referencia",
)

BASE = {"nombre": "Lina", "apellido": "Díaz", "curso_id": 20}

COMPLETO = {
    "sisben": True,
    "sisben_grupo": "B",
    "sisben_subgrupo": "B4",
    "sisben_nivel": 2,
    "barrio": "El Carmen",
    "municipio": "Galapa",
    "zona_residencia": "urbana",
    "punto_referencia": "Frente a la tienda La Esquina",
}


def _ficha(**datos):
    # `model_validate` con un diccionario se comporta como el cuerpo JSON de
    # la petición: solo cuenta como enviado lo que trae.
    return EstudianteCreate.model_validate({**BASE, **datos})


def _mensaje(error):
    return " ".join(detalle["msg"] for detalle in error.value.errors())


# ---------------------------------------------------------------------------
# Lo que acepta la ficha
# ---------------------------------------------------------------------------


def test_las_columnas_del_repositorio_son_campos_de_la_ficha():
    assert estudiantes_repository.COLUMNAS_SISBEN_Y_RESIDENCIA == OCHO
    for campo in OCHO:
        assert campo in EstudianteCreate.model_fields


def test_acepta_la_ficha_completa():
    ficha = _ficha(**COMPLETO)

    assert {campo: getattr(ficha, campo) for campo in OCHO} == COMPLETO


def test_sin_los_campos_nuevos_quedan_sin_dato():
    ficha = _ficha()

    assert all(getattr(ficha, campo) is None for campo in OCHO)


@pytest.mark.parametrize(
    "grupo,subgrupo",
    [("A", "A1"), ("A", "A5"), ("B", "B7"), ("C", "C18"), ("D", "D21"), ("D", "D1")],
)
def test_acepta_cada_subgrupo_del_sisben_iv(grupo, subgrupo):
    ficha = _ficha(sisben=True, sisben_grupo=grupo, sisben_subgrupo=subgrupo)

    assert ficha.sisben_subgrupo == subgrupo


@pytest.mark.parametrize(
    "grupo,subgrupo,rango",
    [
        ("A", "A6", "A1 a A5"),
        ("A", "A0", "A1 a A5"),
        ("B", "B9", "B1 a B7"),
        ("C", "C19", "C1 a C18"),
        ("D", "D22", "D1 a D21"),
        ("B", "A2", "B1 a B7"),
        ("A", "A01", "A1 a A5"),
        ("A", "AA", "A1 a A5"),
    ],
)
def test_rechaza_un_subgrupo_que_no_es_de_su_grupo(grupo, subgrupo, rango):
    with pytest.raises(ValidationError) as error:
        _ficha(sisben=True, sisben_grupo=grupo, sisben_subgrupo=subgrupo)

    assert f"El subgrupo {subgrupo} no existe" in _mensaje(error)
    assert rango in _mensaje(error)


def test_el_subgrupo_necesita_el_grupo():
    with pytest.raises(ValidationError) as error:
        _ficha(sisben=True, sisben_subgrupo="B4")

    assert "hace falta el grupo" in _mensaje(error)


def test_acepta_el_grupo_sin_subgrupo():
    ficha = _ficha(sisben=True, sisben_grupo="C")

    assert ficha.sisben_grupo == "C"
    assert ficha.sisben_subgrupo is None


def test_acepta_solo_el_nivel_del_sisben_anterior():
    ficha = _ficha(sisben=True, sisben_nivel=3)

    assert ficha.sisben_nivel == 3


@pytest.mark.parametrize("sisben", [None, False])
@pytest.mark.parametrize(
    "clasificacion",
    [
        {"sisben_grupo": "A"},
        {"sisben_grupo": "A", "sisben_subgrupo": "A2"},
        {"sisben_nivel": 1},
    ],
)
def test_sin_sisben_no_hay_clasificacion(sisben, clasificacion):
    with pytest.raises(ValidationError) as error:
        _ficha(sisben=sisben, **clasificacion)

    assert "Sin SISBÉN" in _mensaje(error)


def test_acepta_que_no_tenga_sisben():
    ficha = _ficha(sisben=False)

    assert ficha.sisben is False


@pytest.mark.parametrize("grupo", ["E", "a", "AB"])
def test_rechaza_un_grupo_que_no_existe(grupo):
    with pytest.raises(ValidationError):
        _ficha(sisben=True, sisben_grupo=grupo)


@pytest.mark.parametrize("nivel", [0, 4])
def test_el_nivel_va_de_1_a_3(nivel):
    with pytest.raises(ValidationError):
        _ficha(sisben=True, sisben_nivel=nivel)


@pytest.mark.parametrize("zona", ["centro", "Urbana", ""])
def test_la_zona_es_urbana_o_rural(zona):
    with pytest.raises(ValidationError):
        _ficha(zona_residencia=zona)


@pytest.mark.parametrize(
    "campo,largo", [("barrio", 150), ("municipio", 100), ("punto_referencia", 255)]
)
def test_los_textos_respetan_el_largo_de_su_columna(campo, largo):
    assert getattr(_ficha(**{campo: "x" * largo}), campo) == "x" * largo
    with pytest.raises(ValidationError):
        _ficha(**{campo: "x" * (largo + 1)})


# ---------------------------------------------------------------------------
# Cómo se guardan
# ---------------------------------------------------------------------------


class CursorFalso:
    def __init__(self):
        self.calls = []
        self.rowcount = 1

    def execute(self, query, params=None):
        self.calls.append((query, params))


def test_el_repositorio_reemplaza_solo_los_ocho_datos():
    cursor = CursorFalso()
    valores = tuple(COMPLETO[campo] for campo in OCHO)

    filas = estudiantes_repository.guardar_sisben_y_residencia(cursor, 55, valores)

    query, params = cursor.calls[0]
    texto = " ".join(query.split())
    asignaciones = ", ".join(f"{campo} = %s" for campo in OCHO)
    assert f"UPDATE estudiantes SET {asignaciones} WHERE id = %s" in texto
    assert "direccion" not in texto
    assert params == (*valores, 55)
    assert filas == 1


@pytest.fixture
def escrituras(monkeypatch):
    """Dobles de lo que escribe el controlador, en el orden en que pasa."""
    estado = {"eventos": [], "existe": True}

    @contextmanager
    def get_cursor_falso(commit=False, cursor_factory=None):
        yield "cursor"

    def insertar(_cursor, valores):
        estado["eventos"].append(("insertar", len(valores)))
        return 55

    def actualizar(_cursor, valores):
        estado["eventos"].append(("actualizar", len(valores)))
        return (valores[-1],) if estado["existe"] else None

    def guardar(_cursor, estudiante_id, valores):
        estado["eventos"].append(("sisben", estudiante_id, valores))
        return 1

    def curso(_cursor, estudiante_id, curso_id):
        estado["eventos"].append(("curso", estudiante_id, curso_id))

    monkeypatch.setattr(estudiante_controller, "get_cursor", get_cursor_falso)
    monkeypatch.setattr(estudiantes_repository, "insertar_estudiante", insertar)
    monkeypatch.setattr(estudiantes_repository, "actualizar_estudiante", actualizar)
    monkeypatch.setattr(estudiantes_repository, "guardar_sisben_y_residencia", guardar)
    monkeypatch.setattr(estudiante_controller, "_guardar_curso_vigente", curso)
    return estado


def _sisben(estado):
    return [evento for evento in estado["eventos"] if evento[0] == "sisben"]


def test_crear_con_los_datos_nuevos_los_guarda_en_la_misma_transaccion(escrituras):
    estudiante_controller.crear_estudiante_controller(_ficha(**COMPLETO))

    assert escrituras["eventos"] == [
        ("insertar", 34),
        ("sisben", 55, tuple(COMPLETO[campo] for campo in OCHO)),
        ("curso", 55, 20),
    ]


def test_crear_sin_los_datos_nuevos_no_los_toca(escrituras):
    estudiante_controller.crear_estudiante_controller(_ficha(direccion="Calle 1"))

    assert _sisben(escrituras) == []
    assert escrituras["eventos"] == [("insertar", 34), ("curso", 55, 20)]


def test_editar_con_los_datos_nuevos_los_reemplaza(escrituras):
    estudiante_controller.actualizar_estudiante_controller(55, _ficha(**COMPLETO))

    assert escrituras["eventos"] == [
        ("actualizar", 35),
        ("sisben", 55, tuple(COMPLETO[campo] for campo in OCHO)),
        ("curso", 55, 20),
    ]


def test_una_pestana_vieja_no_borra_los_datos_nuevos(escrituras):
    # El formulario de antes del cambio no manda ninguno de los ocho.
    estudiante_controller.actualizar_estudiante_controller(
        55, _ficha(direccion="Calle 1", estrato="2")
    )

    assert _sisben(escrituras) == []


def test_si_llega_alguno_se_reemplazan_los_ocho(escrituras):
    estudiante_controller.actualizar_estudiante_controller(
        55, _ficha(municipio="Galapa")
    )

    assert _sisben(escrituras) == [
        ("sisben", 55, (None, None, None, None, None, "Galapa", None, None))
    ]


def test_llegar_vacio_tambien_cuenta_como_enviado(escrituras):
    # El formulario nuevo manda null para lo que se borró: eso sí se guarda.
    estudiante_controller.actualizar_estudiante_controller(
        55, _ficha(**{campo: None for campo in OCHO})
    )

    assert _sisben(escrituras) == [("sisben", 55, (None,) * 8)]


def test_editar_un_estudiante_que_no_existe_no_guarda_nada_mas(escrituras):
    escrituras["existe"] = False

    respuesta = estudiante_controller.actualizar_estudiante_controller(
        999, _ficha(**COMPLETO)
    )

    assert respuesta == {"mensaje": "Estudiante no encontrado"}
    assert escrituras["eventos"] == [("actualizar", 35)]


# ---------------------------------------------------------------------------
# Por HTTP: lo que cuenta como "llegó" es lo que trae el cuerpo JSON
# ---------------------------------------------------------------------------


def _peticion(aplicacion, metodo, ruta, cuerpo):
    """Una petición HTTP real contra la app (sin httpx, como en
    ``test_listas_seguimiento_routes.py``). Devuelve (status, cuerpo)."""
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
def put_estudiante(monkeypatch):
    """La app real con un admin; el controlador doblado guarda lo que recibe."""
    from app.dependencies import get_current_user
    from app.main import app
    from app.routes import estudiantes as rutas

    recibidos = []

    def controlador_falso(estudiante_id, est):
        recibidos.append(est)
        return {"mensaje": "Estudiante actualizado correctamente", "id": estudiante_id}

    monkeypatch.setattr(rutas, "actualizar_estudiante_controller", controlador_falso)
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "rol": "admin"}
    try:
        yield lambda cuerpo: _peticion(app, "PUT", "/estudiantes/55", cuerpo), recibidos
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_por_http_un_cuerpo_viejo_no_trae_ninguno_de_los_ocho(put_estudiante):
    enviar, recibidos = put_estudiante

    estado, _ = enviar({**BASE, "direccion": "Calle 1"})

    assert estado == 200
    assert recibidos[0].model_fields_set.isdisjoint(OCHO)


def test_por_http_el_cuerpo_nuevo_trae_los_ocho(put_estudiante):
    enviar, recibidos = put_estudiante

    estado, _ = enviar({**BASE, **COMPLETO})

    assert estado == 200
    assert set(OCHO) <= recibidos[0].model_fields_set


def test_por_http_un_subgrupo_equivocado_responde_422_con_el_motivo(put_estudiante):
    enviar, recibidos = put_estudiante

    estado, cuerpo = enviar({**BASE, "sisben": True, "sisben_grupo": "B", "sisben_subgrupo": "B9"})

    assert estado == 422
    assert "el grupo B va de B1 a B7" in json.dumps(cuerpo, ensure_ascii=False)
    assert recibidos == []
