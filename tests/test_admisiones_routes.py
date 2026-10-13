"""Entrevista de admisión, paso E2: las rutas.

Ver docs/funcionalidades/ENTREVISTA_ADMISION.md. Como en
`test_listas_seguimiento_routes.py`, se conduce la aplicación real por su
interfaz ASGI: llamar las funciones de ruta a mano no observa el código de
estado, y es justo lo que esta capa decide. El controlador va doblado; sus
reglas tienen sus propias pruebas.
"""
import asyncio
import json

import pytest

from app.controllers import admisiones_controller as controlador
from app.routes import admisiones as rutas
from app.services.anio_lectivo import AnioLectivoInexistenteError


ADMIN = {"id": 1, "rol": "admin"}
PROFESOR = {"id": 7, "rol": "profesor"}

ASPIRANTE = {
    "nombre": "Lina",
    "apellido": "Díaz",
    "autoriza_datos": True,
    "autoriza_nombre": "Marta Díaz",
}


def peticion(aplicacion, metodo, ruta, cuerpo=None, query=b""):
    """Una petición HTTP real contra la app. Devuelve (status, cuerpo)."""
    crudo = json.dumps(cuerpo).encode() if cuerpo is not None else b""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1",
        "method": metodo,
        "scheme": "http",
        "path": ruta,
        "raw_path": ruta.encode(),
        "query_string": query,
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
    """La aplicación real, con un admin autenticado y el controlador doblado."""
    from app.dependencies import get_current_user
    from app.main import app

    llamadas = []

    def doblar(nombre, resultado=None, error=None):
        def falso(*args, **kwargs):
            llamadas.append((nombre, args, kwargs))
            if error is not None:
                raise error
            return resultado

        monkeypatch.setattr(rutas, nombre, falso)

    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        yield app, doblar, llamadas
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
# Solo admin, en el router, y las rutas del documento.
# ---------------------------------------------------------------------------


def test_la_proteccion_vive_en_el_router():
    """Así una ruta nueva nace protegida: son datos de menores (Ley 1581)."""
    from app.dependencies import get_current_active_admin

    assert get_current_active_admin in [d.dependency for d in rutas.router.dependencies]


@pytest.mark.parametrize(
    "metodo,ruta,cuerpo",
    [
        ("GET", "/anios-lectivos/3/admisiones", None),
        ("POST", "/anios-lectivos/3/admisiones", ASPIRANTE),
        ("GET", "/admisiones/7", None),
        ("PUT", "/admisiones/7", ASPIRANTE),
        ("DELETE", "/admisiones/7", None),
    ],
)
def test_un_profesor_no_entra_a_ninguna(app_profesor, metodo, ruta, cuerpo):
    estado, _ = peticion(app_profesor, metodo, ruta, cuerpo)

    assert estado == 403


def test_las_rutas_son_las_del_documento():
    """Un renombre aquí rompe el frontend sin que falle nada más."""
    declaradas = {
        (ruta.path, metodo)
        for ruta in rutas.router.routes
        for metodo in ruta.methods
        if metodo != "HEAD"
    }

    assert declaradas == {
        ("/anios-lectivos/{anio_lectivo_id}/admisiones", "GET"),
        ("/anios-lectivos/{anio_lectivo_id}/admisiones", "POST"),
        ("/admisiones/{admision_id}", "GET"),
        ("/admisiones/{admision_id}", "PUT"),
        ("/admisiones/{admision_id}", "DELETE"),
    }


def test_el_router_esta_registrado_en_la_aplicacion():
    from app.main import app

    caminos = set(app.openapi()["paths"])

    assert "/anios-lectivos/{anio_lectivo_id}/admisiones" in caminos
    assert "/admisiones/{admision_id}" in caminos


# ---------------------------------------------------------------------------
# Respuestas y códigos.
# ---------------------------------------------------------------------------


def test_listar_pasa_el_filtro_y_responde_200(app_admin):
    app, doblar, llamadas = app_admin
    doblar("listar_admisiones_controller", resultado={"admisiones": []})

    estado, cuerpo = peticion(
        app, "GET", "/anios-lectivos/3/admisiones", query=b"resultado=aprobado"
    )

    assert estado == 200
    assert cuerpo == {"admisiones": []}
    assert llamadas[0][1] == (3, "aprobado")


def test_un_filtro_inventado_da_422_sin_llegar_al_controlador(app_admin):
    app, doblar, llamadas = app_admin
    doblar("listar_admisiones_controller", resultado={})

    estado, _ = peticion(
        app, "GET", "/anios-lectivos/3/admisiones", query=b"resultado=matriculado"
    )

    assert estado == 422
    assert llamadas == []


def test_registrar_responde_201(app_admin):
    app, doblar, llamadas = app_admin
    doblar("registrar_admision_controller", resultado={"id": 99})

    estado, cuerpo = peticion(app, "POST", "/anios-lectivos/3/admisiones", ASPIRANTE)

    assert estado == 201
    assert cuerpo == {"id": 99}
    anio_id, datos = llamadas[0][1]
    assert anio_id == 3
    assert datos.autoriza_nombre == "Marta Díaz"


def test_sin_autorizacion_da_422_sin_llegar_al_controlador(app_admin):
    app, doblar, llamadas = app_admin
    doblar("registrar_admision_controller", resultado={"id": 99})

    estado, cuerpo = peticion(
        app,
        "POST",
        "/anios-lectivos/3/admisiones",
        {**ASPIRANTE, "autoriza_datos": False},
    )

    assert estado == 422
    assert "autorización" in json.dumps(cuerpo, ensure_ascii=False)
    assert llamadas == []


def test_ver_editar_y_borrar_responden_200(app_admin):
    app, doblar, llamadas = app_admin
    doblar("obtener_admision_controller", resultado={"id": 7})
    doblar("actualizar_admision_controller", resultado={"id": 7})
    doblar("borrar_admision_controller", resultado={"mensaje": "Admisión borrada", "id": 7})

    assert peticion(app, "GET", "/admisiones/7") == (200, {"id": 7})
    assert peticion(app, "PUT", "/admisiones/7", ASPIRANTE) == (200, {"id": 7})
    assert peticion(app, "DELETE", "/admisiones/7") == (
        200,
        {"mensaje": "Admisión borrada", "id": 7},
    )
    assert [llamada[1][0] for llamada in llamadas] == [7, 7, 7]


@pytest.mark.parametrize(
    "error,codigo",
    [
        (AnioLectivoInexistenteError("El año lectivo seleccionado no existe."), 404),
        (controlador.AdmisionNoEncontradaError("La admisión no existe."), 404),
        (controlador.AnioNoEnPreparacionError("El año lectivo 2026 no está en preparación."), 409),
        (controlador.AdmisionMatriculadaError("Ya está matriculada."), 409),
        (controlador.CursoAdmisionInvalidoError("Curso de otro año."), 409),
        (controlador.DocumentoAdmisionRepetidoError("Documento repetido."), 409),
    ],
)
def test_cada_error_sale_con_su_codigo_y_su_mensaje(app_admin, error, codigo):
    app, doblar, _ = app_admin
    for nombre in (
        "listar_admisiones_controller",
        "registrar_admision_controller",
        "obtener_admision_controller",
        "actualizar_admision_controller",
        "borrar_admision_controller",
    ):
        doblar(nombre, error=error)

    llamadas = [
        ("GET", "/anios-lectivos/3/admisiones", None),
        ("POST", "/anios-lectivos/3/admisiones", ASPIRANTE),
        ("GET", "/admisiones/7", None),
        ("PUT", "/admisiones/7", ASPIRANTE),
        ("DELETE", "/admisiones/7", None),
    ]
    for metodo, ruta, cuerpo in llamadas:
        estado, respuesta = peticion(app, metodo, ruta, cuerpo)
        assert estado == codigo, (metodo, ruta)
        assert respuesta == {"detail": str(error)}


def test_un_id_que_no_es_positivo_da_422(app_admin):
    app, doblar, llamadas = app_admin
    doblar("obtener_admision_controller", resultado={"id": 0})

    estado, _ = peticion(app, "GET", "/admisiones/0")

    assert estado == 422
    assert llamadas == []
