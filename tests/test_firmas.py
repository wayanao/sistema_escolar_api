"""Firmas guardadas para el boletin. Ver docs/funcionalidades/FIRMAS_BOLETIN.md.

Se fija:

- la imagen: un PNG aceptable, con mensajes para quien guarda (el admin o el
  propio profesor, no un acudiente);
- quien entra a cada ruta, conduciendo la aplicacion real por ASGI, como
  `test_listas_seguimiento_routes.py` (sin `TestClient`: `httpx` no esta
  instalado). La firma institucional, solo el admin, tambien para leerla; la
  propia, solo un profesor y siempre con el `id` de su sesion;
- el SQL del repositorio y que el controlador confirma solo cuando escribe.
"""
import asyncio
import base64
import json
import struct
import zlib
from contextlib import contextmanager
from datetime import datetime, timezone

import pytest
from fastapi.routing import APIRoute
from pydantic import ValidationError

from app.controllers import firmas_controller
from app.core.firma_observador import MAX_BYTES_IMAGEN
from app.core.firmas import (
    MENSAJE_FIRMA_GRANDE,
    MENSAJE_FIRMA_INVALIDA,
    a_data_url,
    decodificar_firma,
    firma_para_responder,
)
from app.dependencies import get_current_user
from app.repositories import firmas_repository
from app.routes import firmas as rutas
from app.schemas.firmas import FirmaIn

ADMIN = {"id": 1, "rol": "admin", "tenant": "tenant_demo"}
PROFESOR = {"id": 7, "rol": "profesor", "tenant": "tenant_demo"}
PREFIJO = "data:image/png;base64,"
GUARDADA_EN = datetime(2026, 11, 12, 15, 30, tzinfo=timezone.utc)


def _png(ancho=4, alto=2, relleno=b""):
    """Un PNG minimo de verdad: firma, IHDR e IEND."""

    def bloque(tipo, datos):
        crc = zlib.crc32(tipo + datos) & 0xFFFFFFFF
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", ancho, alto, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + bloque(b"IHDR", ihdr) + bloque(b"IEND", b"") + relleno


PNG = _png()
PNG_DATA_URL = PREFIJO + base64.b64encode(PNG).decode("ascii")


# --------------------------------------------------------------------------
# La imagen
# --------------------------------------------------------------------------

def test_una_firma_valida_vuelve_como_bytes_con_o_sin_prefijo():
    assert decodificar_firma(PNG_DATA_URL) == PNG
    assert decodificar_firma(base64.b64encode(PNG).decode("ascii")) == PNG


@pytest.mark.parametrize(
    "texto",
    [
        "esto no es base64 !!",
        base64.b64encode(b"\xff\xd8\xff\xe0 un jpeg").decode("ascii"),
        base64.b64encode(_png(ancho=0)).decode("ascii"),
        base64.b64encode(_png(alto=5000)).decode("ascii"),
        None,
    ],
)
def test_lo_que_no_es_un_png_aceptable_se_rechaza_con_un_mensaje_para_quien_guarda(texto):
    with pytest.raises(ValueError) as error:
        decodificar_firma(texto)
    assert str(error.value) == MENSAJE_FIRMA_INVALIDA


def test_una_firma_de_mas_de_100_kb_dice_que_pesa_demasiado():
    grande = _png(relleno=b"\0" * MAX_BYTES_IMAGEN)
    with pytest.raises(ValueError) as error:
        decodificar_firma(base64.b64encode(grande).decode("ascii"))
    assert str(error.value) == MENSAJE_FIRMA_GRANDE


def test_los_mensajes_no_hablan_del_acudiente():
    """La revision es la de la firma del acudiente, pero aqui guarda el admin
    o el propio profesor: «pide que firme de nuevo» no tendria sentido."""
    for mensaje in (MENSAJE_FIRMA_INVALIDA, MENSAJE_FIRMA_GRANDE):
        assert "Pide" not in mensaje
        assert "Vuelve a firmar" in mensaje


def test_la_imagen_sale_lista_para_un_img_y_sin_firma_sale_none():
    assert a_data_url(memoryview(PNG)) == PNG_DATA_URL
    assert a_data_url(PNG) == PNG_DATA_URL
    assert a_data_url(None) is None


def test_la_respuesta_trae_la_imagen_y_cuando_se_guardo():
    assert firma_para_responder(PNG, GUARDADA_EN) == {
        "imagen": PNG_DATA_URL,
        "actualizado_en": "2026-11-12T15:30:00+00:00",
    }
    assert firma_para_responder(None, None) == {"imagen": None, "actualizado_en": None}


def test_el_esquema_acepta_un_png_y_rechaza_lo_demas_con_422_legible():
    assert FirmaIn(imagen=PNG_DATA_URL).imagen == PNG_DATA_URL
    with pytest.raises(ValidationError) as error:
        FirmaIn(imagen="no es una imagen")
    assert MENSAJE_FIRMA_INVALIDA in str(error.value)
    with pytest.raises(ValidationError):
        FirmaIn(imagen="")
    with pytest.raises(ValidationError):
        FirmaIn(imagen="A" * 140_001)


def test_el_esquema_ignora_cualquier_id_que_venga_en_el_cuerpo():
    """De quien es la firma sale de la sesion, nunca del cuerpo."""
    datos = FirmaIn(imagen=PNG_DATA_URL, profesor_id=99, usuario_id=5)
    assert datos.model_dump() == {"imagen": PNG_DATA_URL}


# --------------------------------------------------------------------------
# Las rutas, por HTTP
# --------------------------------------------------------------------------

def peticion(aplicacion, metodo, ruta, cuerpo=None, consulta=""):
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
        "query_string": consulta.encode(),
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
def con_sesion(monkeypatch):
    """La aplicacion real con la sesion que se pida y los controladores
    doblados: cada llamada queda en `llamadas` como (nombre, argumentos)."""
    from app.main import app

    llamadas = []
    respuesta = {"imagen": PNG_DATA_URL, "actualizado_en": "2026-11-12T15:30:00+00:00"}

    for nombre in (
        "obtener_firma_institucional_controller",
        "guardar_firma_institucional_controller",
        "borrar_firma_institucional_controller",
        "obtener_mi_firma_controller",
        "guardar_mi_firma_controller",
        "borrar_mi_firma_controller",
        "obtener_firma_director_grupo_controller",
    ):
        def falso(*args, _nombre=nombre):
            llamadas.append((_nombre, args))
            return respuesta

        monkeypatch.setattr(rutas, nombre, falso)

    def abrir(usuario):
        app.dependency_overrides[get_current_user] = lambda: usuario
        return app

    try:
        yield abrir, llamadas, respuesta
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_las_rutas_quedan_fijadas_y_nacen_protegidas_en_el_router():
    rutas_declaradas = {
        (metodo, ruta.path)
        for ruta in rutas.router.routes
        if isinstance(ruta, APIRoute)
        for metodo in ruta.methods
    }
    assert rutas_declaradas == {
        ("GET", "/firmas/institucional"),
        ("PUT", "/firmas/institucional"),
        ("DELETE", "/firmas/institucional"),
        ("GET", "/firmas/mia"),
        ("PUT", "/firmas/mia"),
        ("DELETE", "/firmas/mia"),
        ("GET", "/firmas/director-grupo/{estudiante_id}"),
    }
    assert [d.dependency for d in rutas.router.dependencies] == [get_current_user]


@pytest.mark.parametrize(
    ("metodo", "cuerpo"),
    [("GET", None), ("PUT", {"imagen": PNG_DATA_URL}), ("DELETE", None)],
)
def test_un_profesor_no_ve_ni_cambia_la_firma_institucional(con_sesion, metodo, cuerpo):
    abrir, llamadas, _ = con_sesion

    estado, respuesta = peticion(abrir(PROFESOR), metodo, "/firmas/institucional", cuerpo)

    assert estado == 403
    assert respuesta == {"detail": "No tienes los permisos necesarios"}
    assert llamadas == []


def test_el_admin_lee_la_firma_institucional(con_sesion):
    abrir, llamadas, esperada = con_sesion

    estado, respuesta = peticion(abrir(ADMIN), "GET", "/firmas/institucional")

    assert estado == 200
    assert respuesta == esperada
    assert llamadas == [("obtener_firma_institucional_controller", ())]


def test_el_admin_guarda_la_firma_institucional_a_su_nombre(con_sesion):
    abrir, llamadas, _ = con_sesion

    estado, _ = peticion(
        abrir(ADMIN), "PUT", "/firmas/institucional", {"imagen": PNG_DATA_URL}
    )

    assert estado == 200
    assert llamadas == [("guardar_firma_institucional_controller", (PNG_DATA_URL, ADMIN))]


def test_el_admin_quita_la_firma_institucional(con_sesion):
    abrir, llamadas, _ = con_sesion

    estado, _ = peticion(abrir(ADMIN), "DELETE", "/firmas/institucional")

    assert estado == 200
    assert llamadas == [("borrar_firma_institucional_controller", ())]


@pytest.mark.parametrize("ruta", ["/firmas/institucional", "/firmas/mia"])
def test_una_imagen_mala_responde_422_con_el_mensaje_y_no_guarda(con_sesion, ruta):
    abrir, llamadas, _ = con_sesion
    usuario = ADMIN if ruta.endswith("institucional") else PROFESOR

    estado, respuesta = peticion(abrir(usuario), "PUT", ruta, {"imagen": "no es png"})

    assert estado == 422
    assert MENSAJE_FIRMA_INVALIDA in json.dumps(respuesta, ensure_ascii=False)
    assert llamadas == []


@pytest.mark.parametrize(
    ("metodo", "cuerpo"),
    [("GET", None), ("PUT", {"imagen": PNG_DATA_URL}), ("DELETE", None)],
)
def test_el_admin_no_tiene_firma_propia(con_sesion, metodo, cuerpo):
    abrir, llamadas, _ = con_sesion

    estado, respuesta = peticion(abrir(ADMIN), metodo, "/firmas/mia", cuerpo)

    assert estado == 403
    assert respuesta == {"detail": rutas.MENSAJE_SOLO_PROFESOR}
    assert llamadas == []


@pytest.mark.parametrize(
    ("metodo", "cuerpo", "controlador", "argumentos"),
    [
        ("GET", None, "obtener_mi_firma_controller", (7,)),
        ("PUT", {"imagen": PNG_DATA_URL}, "guardar_mi_firma_controller", (7, PNG_DATA_URL)),
        ("DELETE", None, "borrar_mi_firma_controller", (7,)),
    ],
)
def test_el_profesor_maneja_su_propia_firma_con_el_id_de_su_sesion(
    con_sesion, metodo, cuerpo, controlador, argumentos
):
    abrir, llamadas, _ = con_sesion

    estado, _ = peticion(abrir(PROFESOR), metodo, "/firmas/mia", cuerpo)

    assert estado == 200
    assert llamadas == [(controlador, argumentos)]


def test_un_profesor_no_puede_guardar_la_firma_de_otro_mandando_su_id(con_sesion):
    abrir, llamadas, _ = con_sesion

    peticion(
        abrir(PROFESOR), "PUT", "/firmas/mia", {"imagen": PNG_DATA_URL, "profesor_id": 99}
    )

    assert llamadas == [("guardar_mi_firma_controller", (7, PNG_DATA_URL))]


# --- Firma del director de grupo, para el observador del admin (2026-11-18) ---

def test_un_profesor_no_ve_la_firma_del_director_de_grupo(con_sesion):
    abrir, llamadas, _ = con_sesion

    estado, respuesta = peticion(abrir(PROFESOR), "GET", "/firmas/director-grupo/5")

    assert estado == 403
    assert respuesta == {"detail": "No tienes los permisos necesarios"}
    assert llamadas == []


def test_el_admin_lee_la_firma_del_director_de_grupo_del_estudiante(con_sesion):
    abrir, llamadas, esperada = con_sesion

    estado, respuesta = peticion(abrir(ADMIN), "GET", "/firmas/director-grupo/5")

    assert estado == 200
    assert respuesta == esperada
    assert llamadas == [("obtener_firma_director_grupo_controller", (5, None))]


def test_la_firma_del_director_de_grupo_sigue_el_anio_que_mira_el_admin(con_sesion):
    abrir, llamadas, _ = con_sesion

    estado, _ = peticion(
        abrir(ADMIN), "GET", "/firmas/director-grupo/5", consulta="anio_lectivo_id=3"
    )

    assert estado == 200
    assert llamadas == [("obtener_firma_director_grupo_controller", (5, 3))]


def test_un_anio_lectivo_invalido_responde_422_sin_consultar(con_sesion):
    abrir, llamadas, _ = con_sesion

    estado, _ = peticion(
        abrir(ADMIN), "GET", "/firmas/director-grupo/5", consulta="anio_lectivo_id=0"
    )

    assert estado == 422
    assert llamadas == []


def test_un_estudiante_que_no_existe_responde_404(monkeypatch):
    from app.main import app

    monkeypatch.setattr(rutas, "obtener_firma_director_grupo_controller", lambda *_args: None)
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        estado, respuesta = peticion(app, "GET", "/firmas/director-grupo/999")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert estado == 404
    assert respuesta == {"detail": "Estudiante no encontrado"}


def test_un_anio_lectivo_que_no_existe_responde_404_con_su_mensaje(monkeypatch):
    from app.main import app
    from app.services.anio_lectivo import AnioLectivoInexistenteError

    def falla(*_args):
        raise AnioLectivoInexistenteError("El año lectivo seleccionado no existe.")

    monkeypatch.setattr(rutas, "obtener_firma_director_grupo_controller", falla)
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        estado, respuesta = peticion(
            app, "GET", "/firmas/director-grupo/5", consulta="anio_lectivo_id=99"
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert estado == 404
    assert respuesta == {"detail": "El año lectivo seleccionado no existe."}


def test_un_fallo_al_leer_la_del_director_responde_500_sin_filtrar_el_texto(monkeypatch):
    from app.main import app

    def falla(*_args):
        raise RuntimeError("detalle interno de la base")

    monkeypatch.setattr(rutas, "obtener_firma_director_grupo_controller", falla)
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    try:
        estado, respuesta = peticion(app, "GET", "/firmas/director-grupo/5")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert estado == 500
    assert respuesta == {"detail": "No se pudo cargar la firma del director de grupo"}


def test_un_fallo_responde_500_sin_filtrar_el_texto(monkeypatch):
    from app.main import app

    def falla(*_args):
        raise RuntimeError("detalle interno de la base")

    monkeypatch.setattr(rutas, "obtener_mi_firma_controller", falla)
    app.dependency_overrides[get_current_user] = lambda: PROFESOR
    try:
        estado, respuesta = peticion(app, "GET", "/firmas/mia")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert estado == 500
    assert respuesta == {"detail": "No se pudo cargar tu firma"}


# --------------------------------------------------------------------------
# Repositorio
# --------------------------------------------------------------------------

class CursorFalso:
    """Registra cada `execute` y devuelve la fila que se le de."""

    def __init__(self, fila=None):
        self.fila = fila
        self.llamadas = []

    def execute(self, sql, params=None):
        self.llamadas.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self.fila


def test_la_firma_institucional_es_siempre_la_fila_1():
    cursor = CursorFalso()
    firmas_repository.leer_firma_institucional(cursor)
    firmas_repository.guardar_firma_institucional(cursor, PNG, 1)
    firmas_repository.borrar_firma_institucional(cursor)

    leer, guardar, borrar = cursor.llamadas
    assert "FROM firma_institucional WHERE id = 1" in leer[0]
    assert "VALUES (1, %s, CURRENT_TIMESTAMP, %s)" in guardar[0]
    assert "ON CONFLICT (id) DO UPDATE" in guardar[0]
    assert guardar[1] == (PNG, 1)
    assert borrar == ("DELETE FROM firma_institucional WHERE id = 1", None)


def test_la_firma_de_un_profesor_se_busca_guarda_y_borra_solo_por_su_id():
    cursor = CursorFalso()
    firmas_repository.leer_firma_de_profesor(cursor, 7)
    firmas_repository.guardar_firma_de_profesor(cursor, 7, PNG)
    firmas_repository.borrar_firma_de_profesor(cursor, 7)

    leer, guardar, borrar = cursor.llamadas
    assert "FROM firmas_profesores WHERE profesor_id = %s" in leer[0]
    assert leer[1] == (7,)
    assert "ON CONFLICT (profesor_id) DO UPDATE" in guardar[0]
    assert guardar[1] == (7, PNG)
    assert borrar == ("DELETE FROM firmas_profesores WHERE profesor_id = %s", (7,))


def test_las_dos_firmas_del_boletin_salen_en_una_sola_consulta():
    cursor = CursorFalso()
    firmas_repository.leer_firmas_del_boletin(cursor, 7)

    [(sql, params)] = cursor.llamadas
    assert "FROM firma_institucional WHERE id = 1" in sql
    assert "FROM firmas_profesores WHERE profesor_id = %s" in sql
    assert params == (7,)


def test_la_del_director_sale_del_curso_de_hoy_en_una_sola_consulta():
    cursor = CursorFalso()
    firmas_repository.leer_firma_del_director_de_grupo(cursor, 5)

    [(sql, params)] = cursor.llamadas
    assert "LEFT JOIN cursos c ON e.curso_id = c.id" in sql
    assert "LEFT JOIN profesor dg ON dg.id = c.director_grupo_id" in sql
    assert "LEFT JOIN firmas_profesores fp ON fp.profesor_id = dg.id" in sql
    assert "WHERE e.id = %s" in sql
    assert params == (5,)


def test_con_otro_anio_la_del_director_sale_del_curso_de_su_matricula():
    cursor = CursorFalso()
    firmas_repository.leer_firma_del_director_de_grupo(cursor, 5, 3)

    [(sql, params)] = cursor.llamadas
    assert (
        "(SELECT m.curso_id FROM matriculas m"
        " WHERE m.estudiante_id = e.id AND m.anio_lectivo_id = %s) = c.id"
    ) in sql
    assert params == (3, 5)


# --------------------------------------------------------------------------
# Controlador
# --------------------------------------------------------------------------

@pytest.fixture
def cursor_doblado(monkeypatch):
    """`get_cursor` doblado: anota si se pidio confirmar."""
    estado = {"cursor": CursorFalso(), "commits": []}

    @contextmanager
    def falso(commit=False, cursor_factory=None):
        estado["commits"].append(commit)
        yield estado["cursor"]

    monkeypatch.setattr(firmas_controller, "get_cursor", falso)
    return estado


def test_leer_sin_firma_guardada_devuelve_nones_y_no_confirma(cursor_doblado):
    assert firmas_controller.obtener_firma_institucional_controller() == {
        "imagen": None,
        "actualizado_en": None,
    }
    assert firmas_controller.obtener_mi_firma_controller(7) == {
        "imagen": None,
        "actualizado_en": None,
    }
    assert cursor_doblado["commits"] == [False, False]


def test_leer_con_firma_la_devuelve_lista_para_mostrar(cursor_doblado):
    cursor_doblado["cursor"].fila = (memoryview(PNG), GUARDADA_EN)

    assert firmas_controller.obtener_mi_firma_controller(7) == {
        "imagen": PNG_DATA_URL,
        "actualizado_en": "2026-11-12T15:30:00+00:00",
    }


def test_guardar_la_institucional_guarda_los_bytes_a_nombre_del_admin(cursor_doblado):
    cursor_doblado["cursor"].fila = (GUARDADA_EN,)

    respuesta = firmas_controller.guardar_firma_institucional_controller(PNG_DATA_URL, ADMIN)

    assert respuesta == {"imagen": PNG_DATA_URL, "actualizado_en": "2026-11-12T15:30:00+00:00"}
    [(_, params)] = cursor_doblado["cursor"].llamadas
    assert params == (PNG, 1)
    assert cursor_doblado["commits"] == [True]


def test_guardar_la_propia_guarda_los_bytes_del_profesor(cursor_doblado):
    cursor_doblado["cursor"].fila = (GUARDADA_EN,)

    firmas_controller.guardar_mi_firma_controller(7, PNG_DATA_URL)

    [(_, params)] = cursor_doblado["cursor"].llamadas
    assert params == (7, PNG)
    assert cursor_doblado["commits"] == [True]


def test_la_del_director_trae_su_nombre_y_su_firma_y_no_confirma(cursor_doblado):
    cursor_doblado["cursor"].fila = ("Ana", "Gómez", memoryview(PNG), GUARDADA_EN)

    assert firmas_controller.obtener_firma_director_grupo_controller(5) == {
        "director_grupo": "Ana Gómez",
        "imagen": PNG_DATA_URL,
        "actualizado_en": "2026-11-12T15:30:00+00:00",
    }
    assert cursor_doblado["commits"] == [False]


def test_la_del_director_sin_firma_guardada_trae_el_nombre_y_la_imagen_en_none(cursor_doblado):
    cursor_doblado["cursor"].fila = ("Ana", "Gómez", None, None)

    assert firmas_controller.obtener_firma_director_grupo_controller(5) == {
        "director_grupo": "Ana Gómez",
        "imagen": None,
        "actualizado_en": None,
    }


def test_sin_director_de_grupo_todo_va_en_none(cursor_doblado):
    cursor_doblado["cursor"].fila = (None, None, None, None)

    assert firmas_controller.obtener_firma_director_grupo_controller(5) == {
        "director_grupo": None,
        "imagen": None,
        "actualizado_en": None,
    }


def test_un_estudiante_que_no_existe_devuelve_none(cursor_doblado):
    cursor_doblado["cursor"].fila = None

    assert firmas_controller.obtener_firma_director_grupo_controller(999) is None


def test_con_otro_anio_lo_valida_y_busca_por_su_matricula(cursor_doblado, monkeypatch):
    pedidos = []

    def anio_falso(cursor, anio_lectivo_id, usuario=None):
        pedidos.append((anio_lectivo_id, usuario))
        return anio_lectivo_id

    monkeypatch.setattr(firmas_controller, "anio_distinto_del_activo", anio_falso)
    cursor_doblado["cursor"].fila = ("Ana", "Gómez", None, None)

    firmas_controller.obtener_firma_director_grupo_controller(5, 3)

    assert pedidos == [(3, None)]
    [(_, params)] = cursor_doblado["cursor"].llamadas
    assert params == (3, 5)


def test_quitar_confirma_y_devuelve_nones(cursor_doblado):
    assert firmas_controller.borrar_firma_institucional_controller() == {
        "imagen": None,
        "actualizado_en": None,
    }
    assert firmas_controller.borrar_mi_firma_controller(7) == {
        "imagen": None,
        "actualizado_en": None,
    }
    assert cursor_doblado["commits"] == [True, True]
