"""Caracterizacion del controlador de usuarios migrado en la subcapa 1.4.

Fijan el comportamiento observable de las cuatro funciones migradas: sentencia,
parametros, semantica de commit y respuesta devuelta.

Dos aserciones merecen atencion:
- que la contrasena que llega al SQL sea la hasheada y nunca la original;
- que la actualizacion sin campos no pida conexion, porque antes la abria y la
  perdia al salir por el return temprano.
"""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app.controllers import usuario_controller


class CursorFalso:
    def __init__(self, fila=None, filas=None):
        self.fila = fila
        self.filas = filas or []
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.fila

    def fetchall(self):
        return self.filas


@pytest.fixture
def cursor_de(monkeypatch):
    def instalar(fila=None, filas=None):
        cursor = CursorFalso(fila=fila, filas=filas)
        commits = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        monkeypatch.setattr(usuario_controller, "get_cursor", fake_get_cursor)
        monkeypatch.setattr(
            usuario_controller,
            "get_password_hash",
            lambda password: f"hash::{password}",
        )
        return cursor, commits

    return instalar


def test_crear_usuario_inserta_confirmando_y_devuelve_id(cursor_de):
    cursor, commits = cursor_de(fila=(31,))
    usuario = SimpleNamespace(
        nombre="Ana",
        email="ana@colegio.edu",
        password="secreta",
        rol="admin",
    )

    respuesta = usuario_controller.crear_usuario_controller(usuario)

    query, params = cursor.calls[0]
    assert "INSERT INTO usuarios" in query
    assert "RETURNING id" in query
    assert params == ("Ana", "ana@colegio.edu", "hash::secreta", "admin")
    assert commits == [True]
    assert respuesta == {"id": 31, "mensaje": "Usuario creado exitosamente"}


def test_crear_usuario_nunca_envia_la_contrasena_en_claro(cursor_de):
    cursor, _ = cursor_de(fila=(31,))
    usuario = SimpleNamespace(
        nombre="Ana",
        email="ana@colegio.edu",
        password="secreta",
        rol="admin",
    )

    usuario_controller.crear_usuario_controller(usuario)

    _, params = cursor.calls[0]
    assert "secreta" not in params


def test_obtener_usuarios_consulta_sin_confirmar(cursor_de):
    cursor, commits = cursor_de(filas=[(1, "Ana", "ana@colegio.edu", "admin")])

    respuesta = usuario_controller.obtener_usuarios_controller()

    query, _ = cursor.calls[0]
    assert "SELECT id, nombre, email, rol FROM usuarios" in query
    assert commits == [False]
    assert respuesta == [
        {"id": 1, "nombre": "Ana", "email": "ana@colegio.edu", "rol": "admin"}
    ]


def test_actualizar_usuario_arma_el_set_solo_con_los_campos_presentes(cursor_de):
    cursor, commits = cursor_de()
    usuario = SimpleNamespace(nombre="Ana María", email=None, rol=None, password=None)

    respuesta = usuario_controller.actualizar_usuario_controller(7, usuario)

    query, params = cursor.calls[0]
    assert query == "UPDATE usuarios SET nombre = %s WHERE id = %s"
    assert params == ["Ana María", 7]
    assert commits == [True]
    assert respuesta == {"mensaje": "Usuario actualizado exitosamente"}


def test_actualizar_usuario_hashea_la_contrasena(cursor_de):
    cursor, _ = cursor_de()
    usuario = SimpleNamespace(nombre=None, email=None, rol=None, password="nueva")

    usuario_controller.actualizar_usuario_controller(7, usuario)

    query, params = cursor.calls[0]
    assert query == "UPDATE usuarios SET password = %s WHERE id = %s"
    assert params == ["hash::nueva", 7]


def test_actualizar_usuario_sin_campos_no_pide_conexion(cursor_de):
    cursor, commits = cursor_de()
    usuario = SimpleNamespace(nombre=None, email=None, rol=None, password=None)

    respuesta = usuario_controller.actualizar_usuario_controller(7, usuario)

    assert respuesta == {"error": "No hay campos para actualizar"}
    assert commits == []
    assert cursor.calls == []


def test_eliminar_usuario_borra_confirmando(cursor_de):
    cursor, commits = cursor_de()

    respuesta = usuario_controller.eliminar_usuario_controller(7)

    query, params = cursor.calls[0]
    assert query == "DELETE FROM usuarios WHERE id = %s"
    assert params == (7,)
    assert commits == [True]
    assert respuesta == {"mensaje": "Usuario eliminado exitosamente"}
