"""Caracterizacion del controlador de branding migrado en la subcapa 1.4c.

Cubre las cuatro funciones que pasaron de get_connection a get_cursor.

Dos propiedades merecen atencion:
- obtener_branding_controller crea la fila de branding si no existe, asi que
  tiene dos caminos distintos que deben conservarse;
- subir_logo_controller y eliminar_logo_controller borran el archivo anterior
  DESPUES de cerrar el bloque de base de datos. Ese orden importa: si se borrara
  dentro, un fallo posterior dejaria el archivo perdido sin haber confirmado.
"""

import asyncio
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app.controllers import branding_controller

FILA_COMPLETA = (
    1, "Colegio", "Lema", "url/principal.png", "url/secundario.png",
    "Calle 1", "555", "info@colegio.edu", "900", "12345", "colegio.edu",
    "#111111", "#222222", {"clave": "valor"},
)


class CursorFalso:
    def __init__(self, filas, eventos):
        self._filas = list(filas)
        self.calls = []
        self.eventos = eventos

    def execute(self, query, params=None):
        self.calls.append((query, params))
        self.eventos.append("sql")

    def fetchone(self):
        return self._filas.pop(0) if self._filas else None


@pytest.fixture
def entorno(monkeypatch):
    def instalar(filas=()):
        eventos = []
        cursor = CursorFalso(filas, eventos)
        commits = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor
            eventos.append("cierre_bloque")

        borrados = []

        monkeypatch.setattr(branding_controller, "get_cursor", fake_get_cursor)
        monkeypatch.setattr(
            branding_controller,
            "delete_file",
            lambda url: (borrados.append(url), eventos.append("delete_file")),
        )
        return SimpleNamespace(
            cursor=cursor, commits=commits, borrados=borrados, eventos=eventos
        )

    return instalar


def test_obtener_branding_devuelve_la_fila_existente(entorno):
    caso = entorno(filas=[FILA_COMPLETA])

    resultado = branding_controller.obtener_branding_controller()

    assert len(caso.cursor.calls) == 1
    consulta, _ = caso.cursor.calls[0]
    assert "FROM institucion_branding" in consulta
    assert resultado["id"] == 1
    assert resultado["nombre_institucion"] == "Colegio"
    assert resultado["configuracion_extra"] == {"clave": "valor"}


def test_obtener_branding_crea_la_fila_si_no_existe(entorno):
    fila_nueva = (2, "", None, None, None, None, None, None, None, None, None, None, None, None)
    caso = entorno(filas=[None, fila_nueva])

    resultado = branding_controller.obtener_branding_controller()

    assert len(caso.cursor.calls) == 2
    insercion, _ = caso.cursor.calls[1]
    assert "INSERT INTO institucion_branding" in insercion
    assert caso.commits == [True]
    assert resultado["id"] == 2


def test_obtener_branding_aplica_los_colores_por_defecto(entorno):
    fila = (3, "", "", None, None, "", "", "", "", "", "", None, None, None)
    entorno(filas=[fila])

    resultado = branding_controller.obtener_branding_controller()

    assert resultado["color_primario"] == "#0f314f"
    assert resultado["color_secundario"] == "#526775"
    assert resultado["configuracion_extra"] == {}


def test_actualizar_branding_confirma_y_relee(entorno):
    caso = entorno(filas=[FILA_COMPLETA])
    data = SimpleNamespace(
        nombre_institucion="Colegio", eslogan="Lema", direccion="Calle 1",
        telefono="555", email="info@colegio.edu", nit="900", codigo_dane="12345",
        sitio_web="colegio.edu", color_primario="#111111",
        color_secundario="#222222", configuracion_extra={"clave": "valor"},
    )

    resultado = branding_controller.actualizar_branding_controller(data)

    actualizacion, params = caso.cursor.calls[0]
    assert "UPDATE institucion_branding" in actualizacion
    assert params[0] == "Colegio"
    assert params[-1] == '{"clave": "valor"}'
    # Un bloque para la escritura y otro para la relectura posterior.
    assert caso.commits == [True, True]
    assert resultado["nombre_institucion"] == "Colegio"


def test_subir_logo_borra_el_anterior_despues_de_confirmar(entorno, monkeypatch):
    caso = entorno(filas=[("url/logo_viejo.png",)])
    monkeypatch.setattr(branding_controller, "save_bytes", lambda *a, **k: None)
    monkeypatch.setattr(
        branding_controller, "storage_url_for_key", lambda key: "url/logo_nuevo.png"
    )
    archivo = SimpleNamespace(
        content_type="image/png",
        filename="logo.png",
        read=_lector(b"contenido"),
    )

    resultado = asyncio.run(branding_controller.subir_logo_controller(archivo, "principal"))

    actualizacion, params = caso.cursor.calls[1]
    assert "logo_principal_url" in actualizacion
    assert params == ("url/logo_nuevo.png",)
    assert caso.commits == [True]
    assert caso.borrados == ["url/logo_viejo.png"]
    assert caso.eventos == ["sql", "sql", "cierre_bloque", "delete_file"]
    assert resultado == {"url": "url/logo_nuevo.png", "slot": "principal"}


def test_subir_logo_rechaza_slot_invalido(entorno):
    entorno()
    archivo = SimpleNamespace(content_type="image/png", filename="l.png", read=_lector(b""))

    with pytest.raises(Exception) as excinfo:
        asyncio.run(branding_controller.subir_logo_controller(archivo, "lateral"))

    assert excinfo.value.status_code == 400


def test_eliminar_logo_limpia_la_columna_y_borra_el_archivo(entorno):
    caso = entorno(filas=[("url/logo_viejo.png",)])

    resultado = branding_controller.eliminar_logo_controller("secundario")

    actualizacion, _ = caso.cursor.calls[1]
    assert "logo_secundario_url = NULL" in actualizacion
    assert caso.commits == [True]
    assert caso.borrados == ["url/logo_viejo.png"]
    assert caso.eventos == ["sql", "sql", "cierre_bloque", "delete_file"]
    assert resultado == {"mensaje": "Logo eliminado", "slot": "secundario"}


def test_eliminar_logo_rechaza_slot_invalido(entorno):
    entorno()

    with pytest.raises(Exception) as excinfo:
        branding_controller.eliminar_logo_controller("lateral")

    assert excinfo.value.status_code == 400


def _lector(contenido):
    async def leer():
        return contenido

    return leer
