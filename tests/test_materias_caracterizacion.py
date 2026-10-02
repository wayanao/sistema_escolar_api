"""Caracterizacion de editar una materia (`PUT /materias/{id}`).

Escrita el 2026-10-02, antes del paso 3.6 del año lectivo (aviso al renombrar
una materia que se usa en otro año; ver
`docs/funcionalidades/ANIO_LECTIVO.md`). Hasta entonces editar una materia no
tenia ninguna prueba. Fija lo que el paso 3.6 no debe cambiar: el nombre que se
guarda, los errores y sus codigos HTTP, y las dos consultas de hoy (nombre
repetido y `UPDATE`) con su texto y sus parametros.

Sin base de datos: un doble de conexion que reconoce cada consulta por su
texto y falla ante una que no conoce.

Ajustado a proposito en el paso 3.6: el doble conoce la consulta nueva (en que
años se dicta la materia) y responde como hoy, un solo año activo; editar
cuesta 3 consultas en vez de 2 (aceptado por el usuario el 2026-10-02). Las
dos de antes conservan su texto, sus parametros y su orden, y las respuestas
no cambiaron. Las pruebas del aviso estan en
`test_anio_lectivo_renombrar_materia.py`.
"""
import asyncio
import json

import pytest
from psycopg2 import IntegrityError

from app.controllers import materia_controller
from app.controllers.materia_controller import MateriaDuplicadaError
from app.routes import materias as rutas


def _normalizar(sql):
    return " ".join(sql.split())


SQL_NOMBRE_REPETIDO = _normalizar(
    """
    SELECT id
    FROM materias
    WHERE UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g')) = %s
      AND (%s IS NULL OR id <> %s)
    LIMIT 1
    """
)
SQL_ACTUALIZAR = _normalizar(
    """
    UPDATE materias
    SET nombre = %s, estado = %s
    WHERE id = %s
    RETURNING id
    """
)
# Paso 3.6: en que años se dicta la materia, para el aviso al renombrar.
SQL_NOMBRE_Y_ANIOS = _normalizar(
    """
    SELECT m.nombre, al.anio, al.estado
    FROM materias m
    LEFT JOIN asignaciones a ON a.materia_id = m.id
    LEFT JOIN cursos c ON c.id = a.curso_id
    LEFT JOIN anios_lectivos al ON al.id = c.anio_lectivo_id
    WHERE m.id = %s
    GROUP BY m.nombre, al.anio, al.estado
    ORDER BY al.anio
    """
)
HOY = [(2026, "activo")]


class BaseDeMaterias:
    """Una base minima: la materia 5 se llama GEOMETRIA y existe tambien ALGEBRA (8).

    `usos` son los años en que se dicta cada materia; por defecto, como hoy,
    solo 2026 activo.
    """

    def __init__(self, existe=True, falla_update=False, usos=HOY):
        self.materias = {5: "GEOMETRIA", 8: "ALGEBRA"} if existe else {8: "ALGEBRA"}
        self.usos = list(usos)
        self.falla_update = falla_update
        self.consultas = []
        self.commits = 0
        self.rollbacks = 0
        self.cerrada = False
        self._filas = []

    # --- cursor ---
    def execute(self, sql, params=None):
        sql = _normalizar(sql)
        self.consultas.append((sql, params))
        if sql == SQL_NOMBRE_REPETIDO:
            nombre, _, excluir = params
            self._filas = [
                (materia_id,)
                for materia_id, actual in self.materias.items()
                if actual == nombre and materia_id != excluir
            ]
        elif sql == SQL_ACTUALIZAR:
            if self.falla_update:
                raise IntegrityError("duplicate key value violates unique constraint")
            nombre, _, materia_id = params
            if materia_id in self.materias:
                self.materias[materia_id] = nombre
                self._filas = [(materia_id,)]
            else:
                self._filas = []
        elif sql == SQL_NOMBRE_Y_ANIOS:
            # Como el LEFT JOIN: una fila por año, o una con año NULL si la
            # materia no tiene clases; ninguna si la materia no existe.
            (materia_id,) = params
            if materia_id not in self.materias:
                self._filas = []
            else:
                nombre = self.materias[materia_id]
                usos = self.usos or [(None, None)]
                self._filas = [(nombre, anio, estado) for anio, estado in usos]
        else:
            raise AssertionError(f"consulta inesperada: {sql}")

    def fetchone(self):
        return self._filas[0] if self._filas else None

    def fetchall(self):
        return list(self._filas)

    # --- conexion ---
    def cursor(self, *args, **kwargs):
        return self

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.cerrada = True


@pytest.fixture
def base(monkeypatch):
    base = BaseDeMaterias()
    monkeypatch.setattr(materia_controller, "get_connection", lambda: base)
    return base


def _usar(monkeypatch, base):
    monkeypatch.setattr(materia_controller, "get_connection", lambda: base)
    return base


# ---------------------------------------------------------------------------
# El controlador.
# ---------------------------------------------------------------------------


def test_renombrar_guarda_el_nombre_normalizado_y_confirma(base):
    respuesta = materia_controller.actualizar_materia_controller(
        5, {"nombre": "  geometría   plana ", "estado": "inactivo"}
    )

    assert respuesta == {"mensaje": "Materia actualizada correctamente"}
    assert base.materias[5] == "GEOMETRÍA PLANA"
    assert base.commits == 1
    assert base.rollbacks == 0
    assert base.cerrada


def test_editar_cuesta_tres_consultas_con_estos_parametros(base):
    """Antes del paso 3.6 eran las dos de los extremos; la del medio es nueva."""
    materia_controller.actualizar_materia_controller(
        5, {"nombre": "Geometría plana", "estado": "inactivo"}
    )

    assert base.consultas == [
        (SQL_NOMBRE_REPETIDO, ("GEOMETRÍA PLANA", 5, 5)),
        (SQL_NOMBRE_Y_ANIOS, (5,)),
        (SQL_ACTUALIZAR, ("GEOMETRÍA PLANA", "inactivo", 5)),
    ]


def test_un_estado_desconocido_se_guarda_como_activo(base):
    materia_controller.actualizar_materia_controller(
        5, {"nombre": "GEOMETRIA", "estado": "borrada"}
    )

    assert base.consultas[-1] == (SQL_ACTUALIZAR, ("GEOMETRIA", "activo", 5))


def test_un_nombre_repetido_no_se_guarda(base):
    with pytest.raises(MateriaDuplicadaError, match="Ya existe una materia llamada 'ALGEBRA'."):
        materia_controller.actualizar_materia_controller(5, {"nombre": " algebra "})

    assert [sql for sql, _ in base.consultas] == [SQL_NOMBRE_REPETIDO]
    assert base.materias[5] == "GEOMETRIA"
    assert base.rollbacks == 1
    assert base.commits == 0


def test_un_nombre_vacio_no_consulta_nada(base):
    with pytest.raises(ValueError, match="El nombre de la materia es obligatorio."):
        materia_controller.actualizar_materia_controller(5, {"nombre": "   "})

    assert base.consultas == []
    assert base.rollbacks == 1


def test_una_materia_que_no_existe_responde_error(monkeypatch):
    base = _usar(monkeypatch, BaseDeMaterias(existe=False))

    respuesta = materia_controller.actualizar_materia_controller(5, {"nombre": "GEOMETRIA"})

    assert respuesta == {"error": "Materia no encontrada"}
    assert base.rollbacks == 1
    assert base.commits == 0


def test_si_la_base_rechaza_el_nombre_sale_como_repetido(monkeypatch):
    base = _usar(monkeypatch, BaseDeMaterias(falla_update=True))

    with pytest.raises(MateriaDuplicadaError, match="Ya existe una materia con ese nombre."):
        materia_controller.actualizar_materia_controller(5, {"nombre": "TRIGONOMETRIA"})

    assert base.rollbacks == 1


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
def app_con_usuario():
    from app.dependencies import get_current_user
    from app.main import app

    def entrar_como(usuario):
        app.dependency_overrides[get_current_user] = lambda: usuario
        return app

    try:
        yield entrar_como
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _doblar_controlador(monkeypatch, resultado=None, error=None):
    recibido = []

    def falso(materia_id, data):
        recibido.append((materia_id, data))
        if error is not None:
            raise error
        return resultado

    monkeypatch.setattr(rutas, "actualizar_materia_controller", falso)
    return recibido


def test_la_ruta_pasa_el_cuerpo_entero_y_devuelve_el_resultado(monkeypatch, app_con_usuario):
    app = app_con_usuario({"id": 1, "rol": "admin"})
    recibido = _doblar_controlador(
        monkeypatch, resultado={"mensaje": "Materia actualizada correctamente"}
    )

    status, cuerpo = peticion_put(app, "/materias/5", {"nombre": "GEOMETRIA", "estado": "activo"})

    assert status == 200
    assert cuerpo == {"mensaje": "Materia actualizada correctamente"}
    assert recibido == [(5, {"nombre": "GEOMETRIA", "estado": "activo"})]


@pytest.mark.parametrize(
    ("error", "resultado", "status_esperado", "cuerpo_esperado"),
    [
        (
            MateriaDuplicadaError("Ya existe una materia llamada 'ALGEBRA'."),
            None,
            409,
            {"detail": "Ya existe una materia llamada 'ALGEBRA'."},
        ),
        (
            ValueError("El nombre de la materia es obligatorio."),
            None,
            422,
            {"detail": "El nombre de la materia es obligatorio."},
        ),
        (None, {"error": "Materia no encontrada"}, 404, {"detail": "Materia no encontrada"}),
    ],
)
def test_la_ruta_traduce_cada_error_a_su_codigo(
    monkeypatch, app_con_usuario, error, resultado, status_esperado, cuerpo_esperado
):
    app = app_con_usuario({"id": 1, "rol": "admin"})
    _doblar_controlador(monkeypatch, resultado=resultado, error=error)

    assert peticion_put(app, "/materias/5", {"nombre": "X"}) == (status_esperado, cuerpo_esperado)


def test_un_profesor_no_puede_editar_materias(monkeypatch, app_con_usuario):
    app = app_con_usuario({"id": 7, "rol": "profesor"})
    recibido = _doblar_controlador(monkeypatch, resultado={"mensaje": "no deberia llegar"})

    status, _ = peticion_put(app, "/materias/5", {"nombre": "GEOMETRIA"})

    assert status == 403
    assert recibido == []
