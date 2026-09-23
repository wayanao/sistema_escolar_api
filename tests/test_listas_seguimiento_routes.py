"""Paso 5 de "Listas de Seguimiento por Curso": las rutas.

Ver `docs/funcionalidades/LISTAS_SEGUIMIENTO.md`. Aqui se conduce la
aplicacion real por su interfaz ASGI, no se llaman las funciones de ruta a
mano: llamarlas directamente **no observa el codigo de estado, lo infiere**, y
es justo el codigo lo que esta capa decide. No se usa `TestClient` porque
`httpx` no esta instalado, igual que en `test_ventas_caracterizacion.py`.

El controlador va doblado: sus reglas ya tienen sus propias pruebas. Lo que se
fija aqui es lo que solo se ve al pasar por HTTP:

- que todas las rutas son **solo para admin**, y que la proteccion esta en el
  router y no en cada funcion;
- que cada error del controlador sale con el codigo que promete el documento;
- que el cuerpo del lote se valida como `LoteDeMarcas` **dentro de FastAPI**.
  Hasta ahora ese tipo solo se habia probado por separado; si la ruta lo
  declarara como una lista normal, las dos reglas del lote desaparecerian sin
  que ninguna prueba anterior se enterara.

La quinta ruta, el alta en todos los cursos, llego con la ampliacion del
2026-09-22 y se prueba al final del archivo.
"""
import asyncio
import json

import pytest

from app.controllers.listas_seguimiento_controller import (
    ColumnaDuplicadaError,
    ColumnaNoEncontradaError,
    CursoNoEncontradoError,
    MarcasFueraDelCursoError,
)
from app.routes import listas_seguimiento as rutas


ADMIN = {"id": 1, "rol": "admin"}
PROFESOR = {"id": 7, "rol": "profesor"}

RESPUESTA_GET = {
    "curso_id": 12,
    "columnas": [{"id": 5, "nombre": "Asistio a la cumbre"}],
    "estudiantes": [
        {
            "estudiante_id": 101,
            "nombre": "Juan",
            "apellido": "Perez",
            "marcas": {"5": {"marcado": True, "nota": "Llego tarde"}},
        }
    ],
}


def celda(columna_id=5, estudiante_id=101, marcado=True, nota=""):
    return {
        "columna_id": columna_id,
        "estudiante_id": estudiante_id,
        "marcado": marcado,
        "nota": nota,
    }


def peticion(aplicacion, metodo, ruta, cuerpo=None):
    """Una peticion HTTP real contra la app. Devuelve (status, cuerpo)."""
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


@pytest.fixture
def app_admin(monkeypatch):
    """La aplicacion real, con un admin autenticado y el controlador doblado."""
    from app.dependencies import get_current_user
    from app.main import app

    def doblar(nombre, resultado=None, error=None):
        def falso(*args, **kwargs):
            if error is not None:
                raise error
            return resultado

        monkeypatch.setattr(rutas, nombre, falso)

    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        yield app, doblar
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def app_profesor():
    from app.dependencies import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: PROFESOR
    try:
        yield app
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# Solo admin, y en el router.
# ---------------------------------------------------------------------------


def test_la_proteccion_vive_en_el_router_y_no_en_cada_funcion():
    """Asi un endpoint nuevo nace protegido en vez de nacer abierto y depender
    de que alguien se acuerde de anadirle el Depends."""
    assert rutas.router.dependencies, "el router perdio su dependencia de admin"


@pytest.mark.parametrize(
    "metodo,ruta,cuerpo",
    [
        ("GET", "/listas-seguimiento/12", None),
        ("POST", "/listas-seguimiento/12/columnas", {"nombre": "Nueva"}),
        ("DELETE", "/listas-seguimiento/12/columnas/5", None),
        ("POST", "/listas-seguimiento/12/marcas", [celda()]),
    ],
)
def test_un_profesor_no_entra_a_ninguna_de_las_cuatro(app_profesor, metodo, ruta, cuerpo):
    estado, _ = peticion(app_profesor, metodo, ruta, cuerpo)

    assert estado == 403


# ---------------------------------------------------------------------------
# Leer la lista.
# ---------------------------------------------------------------------------


def test_la_lista_sale_tal_cual_la_arma_el_controlador(app_admin):
    app, doblar = app_admin
    doblar("obtener_lista_seguimiento_controller", resultado=RESPUESTA_GET)

    estado, cuerpo = peticion(app, "GET", "/listas-seguimiento/12")

    assert estado == 200
    assert cuerpo == RESPUESTA_GET


def test_un_curso_inexistente_da_404(app_admin):
    app, doblar = app_admin
    doblar(
        "obtener_lista_seguimiento_controller",
        error=CursoNoEncontradoError("Ese curso no existe."),
    )

    estado, cuerpo = peticion(app, "GET", "/listas-seguimiento/999")

    assert estado == 404
    assert cuerpo["detail"] == "Ese curso no existe."


# ---------------------------------------------------------------------------
# Crear columna.
# ---------------------------------------------------------------------------


def test_crear_una_columna_responde_201_con_su_id(app_admin):
    app, doblar = app_admin
    doblar("crear_columna_controller", resultado=7)

    estado, cuerpo = peticion(
        app, "POST", "/listas-seguimiento/12/columnas", {"nombre": "Compro el libro"}
    )

    assert estado == 201
    assert cuerpo == {"id": 7, "nombre": "Compro el libro"}


def test_el_nombre_llega_recortado_al_controlador(app_admin):
    """Lo recorta el esquema antes de la ruta, asi que lo que se devuelve ya
    es lo que se guardo."""
    app, doblar = app_admin
    doblar("crear_columna_controller", resultado=7)

    _, cuerpo = peticion(
        app, "POST", "/listas-seguimiento/12/columnas", {"nombre": "  Con espacios  "}
    )

    assert cuerpo["nombre"] == "Con espacios"


def test_un_nombre_repetido_da_409(app_admin):
    app, doblar = app_admin
    doblar(
        "crear_columna_controller",
        error=ColumnaDuplicadaError("Ya existe una columna con ese nombre en este curso."),
    )

    estado, cuerpo = peticion(
        app, "POST", "/listas-seguimiento/12/columnas", {"nombre": "Ya existe"}
    )

    assert estado == 409
    assert "Ya existe una columna" in cuerpo["detail"]


def test_crear_en_un_curso_inexistente_da_404(app_admin):
    app, doblar = app_admin
    doblar("crear_columna_controller", error=CursoNoEncontradoError("Ese curso no existe."))

    estado, _ = peticion(
        app, "POST", "/listas-seguimiento/999/columnas", {"nombre": "Nueva"}
    )

    assert estado == 404


@pytest.mark.parametrize("nombre", ["", "   ", "A" * 101])
def test_un_nombre_invalido_ni_llega_al_controlador(app_admin, nombre):
    """Lo para el esquema, antes de la ruta."""
    app, doblar = app_admin
    doblar(
        "crear_columna_controller",
        error=AssertionError("el controlador no deberia ejecutarse"),
    )

    estado, _ = peticion(
        app, "POST", "/listas-seguimiento/12/columnas", {"nombre": nombre}
    )

    assert estado == 422


# ---------------------------------------------------------------------------
# Borrar columna.
# ---------------------------------------------------------------------------


def test_borrar_una_columna_responde_200(app_admin):
    app, doblar = app_admin
    doblar("eliminar_columna_controller", resultado=None)

    estado, cuerpo = peticion(app, "DELETE", "/listas-seguimiento/12/columnas/5")

    assert estado == 200
    assert cuerpo == {"mensaje": "Columna eliminada"}


def test_borrar_una_columna_que_no_esta_da_404(app_admin):
    app, doblar = app_admin
    doblar(
        "eliminar_columna_controller",
        error=ColumnaNoEncontradaError("Esa columna ya no existe."),
    )

    estado, cuerpo = peticion(app, "DELETE", "/listas-seguimiento/12/columnas/5")

    assert estado == 404
    assert cuerpo["detail"] == "Esa columna ya no existe."


# ---------------------------------------------------------------------------
# Guardar el lote. Las dos reglas del lote, ya dentro de FastAPI.
# ---------------------------------------------------------------------------


def test_guardar_un_lote_responde_200_con_el_conteo(app_admin):
    app, doblar = app_admin
    doblar("guardar_marcas_controller", resultado=2)

    estado, cuerpo = peticion(
        app,
        "POST",
        "/listas-seguimiento/12/marcas",
        [celda(estudiante_id=101), celda(estudiante_id=102)],
    )

    assert estado == 200
    assert cuerpo == {"mensaje": "Cambios guardados", "guardadas": 2}


def test_un_lote_vacio_da_422_sin_llegar_al_controlador(app_admin):
    app, doblar = app_admin
    doblar(
        "guardar_marcas_controller",
        error=AssertionError("el controlador no deberia ejecutarse"),
    )

    estado, _ = peticion(app, "POST", "/listas-seguimiento/12/marcas", [])

    assert estado == 422


def test_la_misma_celda_dos_veces_da_422_sin_llegar_al_controlador(app_admin):
    """La prueba que justifica que la ruta declare `LoteDeMarcas`.

    Con `list[MarcaSeguimientoItem]` esto pasaria de largo, llegaria a
    PostgreSQL -que aborta la sentencia entera por el ON CONFLICT- y saldria
    como 500. Ninguna prueba anterior lo habria notado: el tipo solo se habia
    ejercitado fuera de FastAPI.
    """
    app, doblar = app_admin
    doblar(
        "guardar_marcas_controller",
        error=AssertionError("el controlador no deberia ejecutarse"),
    )

    estado, _ = peticion(
        app,
        "POST",
        "/listas-seguimiento/12/marcas",
        [celda(nota="una"), celda(nota="otra")],
    )

    assert estado == 422


def test_una_celda_ajena_al_curso_da_422(app_admin):
    app, doblar = app_admin
    doblar(
        "guardar_marcas_controller",
        error=MarcasFueraDelCursoError(
            "El lote incluye una columna o un estudiante que no son de este curso."
        ),
    )

    estado, cuerpo = peticion(app, "POST", "/listas-seguimiento/12/marcas", [celda()])

    assert estado == 422
    assert "no son de este curso" in cuerpo["detail"]


def test_una_nota_demasiado_larga_da_422(app_admin):
    app, doblar = app_admin
    doblar(
        "guardar_marcas_controller",
        error=AssertionError("el controlador no deberia ejecutarse"),
    )

    estado, _ = peticion(
        app, "POST", "/listas-seguimiento/12/marcas", [celda(nota="N" * 241)]
    )

    assert estado == 422


# ---------------------------------------------------------------------------
# Las rutas son las que fija el documento.
# ---------------------------------------------------------------------------


def test_las_rutas_son_las_del_documento():
    """Un renombre o una errata aqui rompe el frontend sin que falle nada mas."""
    declaradas = {
        (ruta.path, metodo)
        for ruta in rutas.router.routes
        for metodo in ruta.methods
        if metodo != "HEAD"
    }

    assert declaradas == {
        ("/listas-seguimiento/{curso_id}", "GET"),
        ("/listas-seguimiento/{curso_id}/columnas", "POST"),
        ("/listas-seguimiento/{curso_id}/columnas/{columna_id}", "DELETE"),
        ("/listas-seguimiento/{curso_id}/marcas", "POST"),
        # La del alta masiva no lleva curso: actua sobre todos.
        ("/listas-seguimiento/columnas-en-todos-los-cursos", "POST"),
    }


def test_el_router_esta_registrado_en_la_aplicacion():
    """Sin esto el modulo existe, pasa sus pruebas y no responde a nadie."""
    from app.main import app

    caminos = {getattr(ruta, "path", "") for ruta in app.routes}

    assert "/listas-seguimiento/{curso_id}" in caminos


# ---------------------------------------------------------------------------
# Ampliacion: crear la columna en todos los cursos.
#
# Ver docs/funcionalidades/LISTAS_SEGUIMIENTO.md, seccion "Ampliacion".
# ---------------------------------------------------------------------------


RUTA_MASIVA = "/listas-seguimiento/columnas-en-todos-los-cursos"


def test_el_alta_masiva_responde_200_con_los_conteos(app_admin):
    app, doblar = app_admin
    doblar(
        "crear_columna_en_todos_los_cursos_controller",
        resultado={"creadas": 9, "omitidas": 16, "total": 25},
    )

    estado, cuerpo = peticion(app, "POST", RUTA_MASIVA, {"nombre": "Excursion"})

    assert estado == 200
    assert cuerpo == {"creadas": 9, "omitidas": 16, "total": 25}


def test_no_crear_ninguna_sigue_siendo_200(app_admin):
    """Responde 200 y no 201, al contrario que el alta de una sola columna.

    Que no cree nada es un resultado valido y frecuente -si todos los cursos ya
    la tenian-, asi que un 201 fijo estaria mintiendo la mitad de las veces.
    """
    app, doblar = app_admin
    doblar(
        "crear_columna_en_todos_los_cursos_controller",
        resultado={"creadas": 0, "omitidas": 25, "total": 25},
    )

    estado, cuerpo = peticion(app, "POST", RUTA_MASIVA, {"nombre": "Excursion"})

    assert estado == 200
    assert cuerpo["creadas"] == 0


def test_la_carrera_del_indice_sale_como_409(app_admin):
    app, doblar = app_admin
    doblar(
        "crear_columna_en_todos_los_cursos_controller",
        error=ColumnaDuplicadaError(
            "Otra persona estaba creando esa misma columna. Vuelve a intentarlo."
        ),
    )

    estado, cuerpo = peticion(app, "POST", RUTA_MASIVA, {"nombre": "Excursion"})

    assert estado == 409
    assert "Vuelve a intentarlo" in cuerpo["detail"]


@pytest.mark.parametrize("nombre", ["", "   ", "A" * 101])
def test_un_nombre_invalido_ni_llega_al_controlador_en_el_alta_masiva(app_admin, nombre):
    app, doblar = app_admin
    doblar(
        "crear_columna_en_todos_los_cursos_controller",
        error=AssertionError("el controlador no deberia ejecutarse"),
    )

    estado, _ = peticion(app, "POST", RUTA_MASIVA, {"nombre": nombre})

    assert estado == 422


def test_el_alta_masiva_tambien_es_solo_para_admin(app_profesor):
    estado, _ = peticion(app_profesor, "POST", RUTA_MASIVA, {"nombre": "Excursion"})

    assert estado == 403


def test_la_ruta_nueva_no_ensombrece_a_las_que_llevan_curso(app_admin):
    """`/listas-seguimiento/columnas-en-todos-los-cursos` encaja tambien en el
    molde de `/listas-seguimiento/{curso_id}`.

    Son metodos distintos, asi que no deberia haber choque, pero eso es
    razonarlo y no verlo. Aqui se ven las tres conviviendo.
    """
    app, doblar = app_admin
    doblar("obtener_lista_seguimiento_controller", resultado=RESPUESTA_GET)
    doblar("crear_columna_controller", resultado=7)
    doblar(
        "crear_columna_en_todos_los_cursos_controller",
        resultado={"creadas": 1, "omitidas": 0, "total": 1},
    )

    assert peticion(app, "GET", "/listas-seguimiento/12")[0] == 200
    assert peticion(app, "POST", "/listas-seguimiento/12/columnas", {"nombre": "X"})[0] == 201
    assert peticion(app, "POST", RUTA_MASIVA, {"nombre": "X"})[0] == 200
