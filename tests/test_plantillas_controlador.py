"""Caracterizacion del controlador de plantillas migrado en la subcapa 1.4i.

Las siete funciones del archivo estaban desprotegidas y ninguna tenia cobertura.

El archivo ya era cuidadoso: cerraba explicitamente antes de cada salida
temprana, asi que no fugaba en esos caminos. Lo que se gana con la migracion es
el cierre garantizado cuando un execute lanza.

Se fijan los codigos de estado de cada rechazo, el fallback de plantilla activa,
la atomicidad de la activacion y el nombre por defecto al duplicar.
"""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app.controllers import plantilla_controller

FILA = (
    3, "boletin", "Boletin clasico", "BOL-1", False, True,
    {"margen": 10}, "2026-08-01", "2026-08-02",
)


class CursorFalso:
    """Devuelve un fetchone distinto por cada llamada, en orden."""

    def __init__(self, unos=(), todos=()):
        self.unos = list(unos)
        self.todos = list(todos)
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.unos.pop(0) if self.unos else None

    def fetchall(self):
        return self.todos.pop(0) if self.todos else []


@pytest.fixture
def cursor_de(monkeypatch):
    def instalar(unos=(), todos=()):
        cursor = CursorFalso(unos=unos, todos=todos)
        commits = []

        @contextmanager
        def fake_get_cursor(commit=False, cursor_factory=None):
            commits.append(commit)
            yield cursor

        monkeypatch.setattr(plantilla_controller, "get_cursor", fake_get_cursor)
        return cursor, commits

    return instalar


def test_listar_sin_tipo_ordena_por_tipo_y_predefinida(cursor_de):
    cursor, commits = cursor_de(todos=[[FILA]])

    resultado = plantilla_controller.listar_plantillas_controller()

    query, params = cursor.calls[0]
    assert "ORDER BY tipo ASC, es_predefinida DESC, nombre ASC" in query
    assert params is None
    assert commits == [False]
    assert resultado[0]["id"] == 3
    assert resultado[0]["config_json"] == {"margen": 10}


def test_listar_con_tipo_filtra(cursor_de):
    cursor, _ = cursor_de(todos=[[FILA]])

    plantilla_controller.listar_plantillas_controller(tipo="boletin")

    query, params = cursor.calls[0]
    assert "WHERE tipo = %s" in query
    assert params == ("boletin",)


def test_listar_con_tipo_invalido_responde_400(cursor_de):
    cursor, _ = cursor_de()

    with pytest.raises(Exception) as excinfo:
        plantilla_controller.listar_plantillas_controller(tipo="inexistente")

    assert excinfo.value.status_code == 400
    assert cursor.calls == []


def test_obtener_activa_devuelve_la_activa(cursor_de):
    cursor, commits = cursor_de(unos=[FILA])

    resultado = plantilla_controller.obtener_plantilla_activa_controller("boletin")

    query, params = cursor.calls[0]
    assert "activa = TRUE" in query
    assert params == ("boletin",)
    assert len(cursor.calls) == 1
    assert commits == [False]
    assert resultado["id"] == 3


def test_obtener_activa_cae_en_la_predefinida_si_no_hay_activa(cursor_de):
    cursor, _ = cursor_de(unos=[None, FILA])

    resultado = plantilla_controller.obtener_plantilla_activa_controller("boletin")

    consulta_fallback, params = cursor.calls[1]
    assert "es_predefinida = TRUE" in consulta_fallback
    assert params == ("boletin",)
    assert resultado["id"] == 3


def test_obtener_activa_sin_ninguna_responde_404(cursor_de):
    cursor_de(unos=[None, None])

    with pytest.raises(Exception) as excinfo:
        plantilla_controller.obtener_plantilla_activa_controller("boletin")

    assert excinfo.value.status_code == 404


def test_obtener_activa_con_tipo_invalido_responde_400_sin_consultar(cursor_de):
    cursor, commits = cursor_de()

    with pytest.raises(Exception) as excinfo:
        plantilla_controller.obtener_plantilla_activa_controller("inexistente")

    assert excinfo.value.status_code == 400
    assert cursor.calls == []
    assert commits == []


def test_crear_plantilla_nace_inactiva_y_no_predefinida(cursor_de):
    cursor, commits = cursor_de(unos=[(21,)])
    plantilla = SimpleNamespace(tipo="boletin", nombre="Mi boletin", config_json={"a": 1})

    respuesta = plantilla_controller.crear_plantilla_controller(plantilla)

    query, params = cursor.calls[0]
    assert "VALUES (%s, %s, FALSE, FALSE, %s)" in query
    assert params == ("boletin", "Mi boletin", '{"a": 1}')
    assert commits == [True]
    assert respuesta == {"id": 21, "mensaje": "Plantilla creada"}


def test_crear_plantilla_con_tipo_invalido_responde_400_sin_consultar(cursor_de):
    cursor, commits = cursor_de()
    plantilla = SimpleNamespace(tipo="inexistente", nombre="X", config_json=None)

    with pytest.raises(Exception) as excinfo:
        plantilla_controller.crear_plantilla_controller(plantilla)

    assert excinfo.value.status_code == 400
    assert cursor.calls == []
    assert commits == []


def test_actualizar_plantilla_inexistente_responde_404(cursor_de):
    cursor_de(unos=[None])
    datos = SimpleNamespace(nombre="Nuevo", config_json=None)

    with pytest.raises(Exception) as excinfo:
        plantilla_controller.actualizar_plantilla_controller(3, datos)

    assert excinfo.value.status_code == 404


def test_actualizar_plantilla_predefinida_responde_400(cursor_de):
    cursor, _ = cursor_de(unos=[(True,)])
    datos = SimpleNamespace(nombre="Nuevo", config_json=None)

    with pytest.raises(Exception) as excinfo:
        plantilla_controller.actualizar_plantilla_controller(3, datos)

    assert excinfo.value.status_code == 400
    assert "Duplica para personalizar" in excinfo.value.detail
    assert len(cursor.calls) == 1


def test_actualizar_sin_campos_no_ejecuta_update(cursor_de):
    cursor, _ = cursor_de(unos=[(False,)])
    datos = SimpleNamespace(nombre=None, config_json=None)

    respuesta = plantilla_controller.actualizar_plantilla_controller(3, datos)

    assert respuesta == {"mensaje": "Sin cambios"}
    assert len(cursor.calls) == 1


def test_actualizar_arma_el_set_y_toca_la_fecha(cursor_de):
    cursor, commits = cursor_de(unos=[(False,)])
    datos = SimpleNamespace(nombre="Nuevo", config_json={"a": 1})

    respuesta = plantilla_controller.actualizar_plantilla_controller(3, datos)

    query, params = cursor.calls[1]
    assert query == (
        "UPDATE plantilla_impresion SET nombre = %s, config_json = %s, "
        "actualizado_en = CURRENT_TIMESTAMP WHERE id = %s"
    )
    assert params == ("Nuevo", '{"a": 1}', 3)
    assert commits == [True]
    assert respuesta == {"mensaje": "Plantilla actualizada"}


def test_activar_desactiva_las_demas_del_mismo_tipo(cursor_de):
    cursor, commits = cursor_de(unos=[("boletin",)])

    respuesta = plantilla_controller.activar_plantilla_controller(3)

    desactivar, params_desactivar = cursor.calls[1]
    activar, params_activar = cursor.calls[2]
    assert "SET activa = FALSE WHERE tipo = %s AND id != %s" in desactivar
    assert params_desactivar == ("boletin", 3)
    assert "SET activa = TRUE" in activar
    assert params_activar == (3,)
    assert commits == [True]
    assert respuesta == {"mensaje": "Plantilla activada para tipo 'boletin'"}


def test_activar_plantilla_inexistente_responde_404(cursor_de):
    cursor, _ = cursor_de(unos=[None])

    with pytest.raises(Exception) as excinfo:
        plantilla_controller.activar_plantilla_controller(3)

    assert excinfo.value.status_code == 404
    assert len(cursor.calls) == 1


def test_duplicar_agrega_el_sufijo_copia_por_defecto(cursor_de):
    cursor, commits = cursor_de(unos=[("boletin", "Boletin clasico", {"a": 1}), (42,)])

    respuesta = plantilla_controller.duplicar_plantilla_controller(3)

    _, params = cursor.calls[1]
    assert params == ("boletin", "Boletin clasico (copia)", '{"a": 1}')
    assert commits == [True]
    assert respuesta == {"id": 42, "mensaje": "Plantilla duplicada"}


def test_duplicar_respeta_el_nombre_indicado(cursor_de):
    cursor, _ = cursor_de(unos=[("boletin", "Boletin clasico", None), (42,)])

    plantilla_controller.duplicar_plantilla_controller(3, nuevo_nombre="Mi copia")

    _, params = cursor.calls[1]
    assert params == ("boletin", "Mi copia", "{}")


def test_eliminar_plantilla_predefinida_responde_400(cursor_de):
    cursor, _ = cursor_de(unos=[(True,)])

    with pytest.raises(Exception) as excinfo:
        plantilla_controller.eliminar_plantilla_controller(3)

    assert excinfo.value.status_code == 400
    assert len(cursor.calls) == 1


def test_eliminar_plantilla_propia_borra_confirmando(cursor_de):
    cursor, commits = cursor_de(unos=[(False,)])

    respuesta = plantilla_controller.eliminar_plantilla_controller(3)

    query, params = cursor.calls[1]
    assert query == "DELETE FROM plantilla_impresion WHERE id = %s"
    assert params == (3,)
    assert commits == [True]
    assert respuesta == {"mensaje": "Plantilla eliminada"}
