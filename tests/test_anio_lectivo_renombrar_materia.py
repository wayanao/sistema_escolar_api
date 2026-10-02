"""Fase 3 del año lectivo, paso 3.6: aviso al renombrar una materia.

Ver `docs/funcionalidades/ANIO_LECTIVO.md`, decision 12. El boletin y los
certificados leen el nombre de la materia al imprimir, asi que renombrarla
cambia tambien los documentos de otros años. Si la materia se usa en mas de un
año, o en uno cerrado o reabierto, `PUT /materias/{id}` responde 409 con el
codigo `materia_usada_en_otro_anio` y el aviso, y no guarda; con
`confirmar_cambio_nombre: true` guarda como siempre.

Con un solo año, como hoy, nunca avisa: lo fija
`test_materias_caracterizacion.py`, escrita antes del cambio.

Sin base de datos: dobles de conexion, como el resto de pruebas del año
lectivo. La ruta se conduce por la aplicacion real (ASGI) para ver el codigo
HTTP y el cuerpo exactos.
"""
import asyncio
import json

import pytest

from app.controllers import materia_controller
from app.controllers.materia_controller import (
    MateriaDuplicadaError,
    MateriaUsadaEnOtroAnioError,
)
from app.repositories.anios_lectivos_repository import leer_nombre_y_anios_de_materia
from app.routes import materias as rutas
from app.services.anio_lectivo import (
    anios_a_avisar_al_renombrar,
    mensaje_materia_usada_en_otro_anio,
)


def _normalizar(sql):
    return " ".join(sql.split())


# ---------------------------------------------------------------------------
# La regla: cuando avisar y que años nombrar.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("usos", "anios"),
    [
        # Un solo año que no es pasado: nunca avisa (hoy, y en la fase 5).
        ([], []),
        ([(2026, "activo")], []),
        ([(2027, "preparacion")], []),
        # Un solo año, pero cerrado o reabierto: sus boletines cambiarian.
        ([(2026, "cerrado")], [2026]),
        ([(2026, "reabierto")], [2026]),
        # Mas de un año: se nombran los que no son el activo.
        ([(2026, "activo"), (2027, "preparacion")], [2027]),
        ([(2026, "cerrado"), (2027, "activo")], [2026]),
        ([(2025, "cerrado"), (2026, "reabierto"), (2027, "activo")], [2025, 2026]),
    ],
)
def test_cuando_avisar_y_que_anios_nombrar(usos, anios):
    assert anios_a_avisar_al_renombrar(usos) == anios


def test_el_aviso_de_un_anio_es_el_del_documento():
    assert mensaje_materia_usada_en_otro_anio([2026]) == (
        "Esta materia se usa en 2026. Si cambias el nombre, también cambiará "
        "en los boletines y certificados de 2026."
    )


@pytest.mark.parametrize(
    ("anios", "texto"),
    [([2025, 2026], "2025 y 2026"), ([2024, 2025, 2026], "2024, 2025 y 2026")],
)
def test_el_aviso_de_varios_anios_los_nombra_todos(anios, texto):
    assert mensaje_materia_usada_en_otro_anio(anios) == (
        f"Esta materia se usa en {texto}. Si cambias el nombre, también cambiará "
        f"en los boletines y certificados de {texto}."
    )


# ---------------------------------------------------------------------------
# La consulta.
# ---------------------------------------------------------------------------


class CursorConFilas:
    def __init__(self, filas):
        self.filas = filas
        self.consultas = []

    def execute(self, sql, params=None):
        self.consultas.append((_normalizar(sql), params))

    def fetchall(self):
        return list(self.filas)


def test_la_consulta_trae_el_nombre_y_los_anios_de_la_materia():
    cursor = CursorConFilas([("GEOMETRIA", 2026, "cerrado"), ("GEOMETRIA", 2027, "activo")])

    assert leer_nombre_y_anios_de_materia(cursor, 5) == (
        "GEOMETRIA",
        [(2026, "cerrado"), (2027, "activo")],
    )
    [(sql, params)] = cursor.consultas
    assert params == (5,)
    # Una fila por año, con el año de cada clase sacado de su curso, y sin
    # filtrar las clases inactivas (ante la duda, avisar de mas).
    assert "LEFT JOIN asignaciones a ON a.materia_id = m.id" in sql
    assert "LEFT JOIN anios_lectivos al ON al.id = c.anio_lectivo_id" in sql
    assert "GROUP BY m.nombre, al.anio, al.estado" in sql
    assert "a.activo" not in sql


def test_una_materia_sin_clases_trae_la_lista_vacia():
    cursor = CursorConFilas([("GEOMETRIA", None, None)])

    assert leer_nombre_y_anios_de_materia(cursor, 5) == ("GEOMETRIA", [])


def test_una_materia_que_no_existe_trae_none():
    assert leer_nombre_y_anios_de_materia(CursorConFilas([]), 5) is None


# ---------------------------------------------------------------------------
# El controlador, con una base de dos años.
# ---------------------------------------------------------------------------

DOS_ANIOS = [(2026, "cerrado"), (2027, "activo")]


class BaseDeMaterias:
    """La materia 5 (GEOMETRIA) y ALGEBRA (8); `usos` son los años de la 5.

    Reconoce cada consulta por su forma y falla ante una desconocida. El texto
    exacto de cada una lo fija `test_materias_caracterizacion.py`.
    """

    def __init__(self, usos=DOS_ANIOS, nombre_guardado="GEOMETRIA"):
        self.materias = {5: nombre_guardado, 8: "ALGEBRA"}
        self.usos = list(usos)
        self.consultas = []
        self.commits = 0
        self.rollbacks = 0
        self._filas = []

    def execute(self, sql, params=None):
        sql = _normalizar(sql)
        if sql.startswith("SELECT id FROM materias"):
            self.consultas.append("nombre repetido")
            nombre, _, excluir = params
            self._filas = [
                (i,) for i, actual in self.materias.items() if actual == nombre and i != excluir
            ]
        elif sql.startswith("SELECT m.nombre, al.anio, al.estado"):
            self.consultas.append("años de la materia")
            nombre = self.materias[params[0]]
            self._filas = [(nombre, anio, estado) for anio, estado in self.usos or [(None, None)]]
        elif sql.startswith("UPDATE materias"):
            self.consultas.append("guardar")
            nombre, _, materia_id = params
            self.materias[materia_id] = nombre
            self._filas = [(materia_id,)]
        else:
            raise AssertionError(f"consulta inesperada: {sql}")

    def fetchone(self):
        return self._filas[0] if self._filas else None

    def fetchall(self):
        return list(self._filas)

    def cursor(self, *args, **kwargs):
        return self

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        pass


@pytest.fixture
def con_base(monkeypatch):
    def usar(**kwargs):
        base = BaseDeMaterias(**kwargs)
        monkeypatch.setattr(materia_controller, "get_connection", lambda: base)
        return base

    return usar


def test_renombrar_una_materia_de_2026_cerrado_avisa_y_no_guarda(con_base):
    base = con_base()

    with pytest.raises(MateriaUsadaEnOtroAnioError) as error:
        materia_controller.actualizar_materia_controller(5, {"nombre": "GEOMETRÍA PLANA"})

    assert str(error.value) == mensaje_materia_usada_en_otro_anio([2026])
    assert error.value.codigo == "materia_usada_en_otro_anio"
    assert base.consultas == ["nombre repetido", "años de la materia"]
    assert base.materias[5] == "GEOMETRIA"
    assert base.rollbacks == 1
    assert base.commits == 0


def test_con_la_confirmacion_guarda_como_siempre_sin_la_consulta_del_aviso(con_base):
    base = con_base()

    respuesta = materia_controller.actualizar_materia_controller(
        5, {"nombre": "GEOMETRÍA PLANA", "estado": "activo", "confirmar_cambio_nombre": True}
    )

    assert respuesta == {"mensaje": "Materia actualizada correctamente"}
    assert base.consultas == ["nombre repetido", "guardar"]
    assert base.materias[5] == "GEOMETRÍA PLANA"
    assert base.commits == 1


@pytest.mark.parametrize("confirmacion", ["true", 1, "si", False, None])
def test_solo_el_booleano_true_confirma(con_base, confirmacion):
    base = con_base()

    with pytest.raises(MateriaUsadaEnOtroAnioError):
        materia_controller.actualizar_materia_controller(
            5, {"nombre": "GEOMETRÍA PLANA", "confirmar_cambio_nombre": confirmacion}
        )

    assert base.materias[5] == "GEOMETRIA"


def test_sin_cambiar_el_nombre_no_avisa(con_base):
    """Cambiar solo el estado no toca lo que imprime el boletin."""
    base = con_base()

    materia_controller.actualizar_materia_controller(5, {"nombre": "geometria", "estado": "inactivo"})

    assert base.consultas == ["nombre repetido", "años de la materia", "guardar"]
    assert base.commits == 1


def test_cambiar_mayusculas_o_espacios_guardados_tambien_avisa(con_base):
    """Se compara el texto guardado tal cual: es lo que sale impreso."""
    base = con_base(nombre_guardado="Geometria")

    with pytest.raises(MateriaUsadaEnOtroAnioError):
        materia_controller.actualizar_materia_controller(5, {"nombre": "GEOMETRIA"})

    assert base.materias[5] == "Geometria"


@pytest.mark.parametrize(
    "usos",
    [[], [(2027, "activo")], [(2027, "preparacion")]],
    ids=["sin clases", "solo el activo", "solo en preparacion"],
)
def test_con_un_solo_anio_que_no_es_pasado_guarda_sin_avisar(con_base, usos):
    base = con_base(usos=usos)

    respuesta = materia_controller.actualizar_materia_controller(5, {"nombre": "GEOMETRÍA PLANA"})

    assert respuesta == {"mensaje": "Materia actualizada correctamente"}
    assert base.materias[5] == "GEOMETRÍA PLANA"


def test_un_nombre_repetido_se_informa_antes_que_el_aviso(con_base):
    """Confirmar no arregla un nombre repetido: ese error va primero."""
    base = con_base()

    with pytest.raises(MateriaDuplicadaError):
        materia_controller.actualizar_materia_controller(5, {"nombre": "ALGEBRA"})

    assert base.consultas == ["nombre repetido"]


# ---------------------------------------------------------------------------
# La ruta, por HTTP.
# ---------------------------------------------------------------------------


def peticion_put(aplicacion, ruta, cuerpo):
    """Una peticion PUT real contra la app. Devuelve (status, cuerpo)."""
    crudo = json.dumps(cuerpo).encode()
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1",
        "method": "PUT",
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
def app_admin():
    from app.dependencies import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "rol": "admin"}
    try:
        yield app
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_la_ruta_responde_409_con_el_codigo_y_el_aviso(monkeypatch, app_admin):
    def falso(materia_id, data):
        raise MateriaUsadaEnOtroAnioError(mensaje_materia_usada_en_otro_anio([2026]))

    monkeypatch.setattr(rutas, "actualizar_materia_controller", falso)

    status, cuerpo = peticion_put(app_admin, "/materias/5", {"nombre": "GEOMETRÍA PLANA"})

    assert status == 409
    assert cuerpo == {
        "detail": {
            "codigo": "materia_usada_en_otro_anio",
            "mensaje": mensaje_materia_usada_en_otro_anio([2026]),
        }
    }


def test_la_ruta_pasa_la_confirmacion_al_controlador(monkeypatch, app_admin):
    recibido = []

    def falso(materia_id, data):
        recibido.append(data)
        return {"mensaje": "Materia actualizada correctamente"}

    monkeypatch.setattr(rutas, "actualizar_materia_controller", falso)

    status, _ = peticion_put(
        app_admin, "/materias/5", {"nombre": "GEOMETRÍA PLANA", "confirmar_cambio_nombre": True}
    )

    assert status == 200
    assert recibido == [{"nombre": "GEOMETRÍA PLANA", "confirmar_cambio_nombre": True}]


def test_de_punta_a_punta_avisa_y_con_la_confirmacion_guarda(monkeypatch, app_admin):
    """El flujo que hara el frontend: intentar, recibir el aviso, confirmar."""
    base = BaseDeMaterias()
    monkeypatch.setattr(materia_controller, "get_connection", lambda: base)

    primero = peticion_put(app_admin, "/materias/5", {"nombre": "GEOMETRÍA PLANA"})
    segundo = peticion_put(
        app_admin, "/materias/5", {"nombre": "GEOMETRÍA PLANA", "confirmar_cambio_nombre": True}
    )

    assert primero[0] == 409
    assert primero[1]["detail"]["codigo"] == "materia_usada_en_otro_anio"
    assert segundo == (200, {"mensaje": "Materia actualizada correctamente"})
    assert base.materias[5] == "GEOMETRÍA PLANA"
