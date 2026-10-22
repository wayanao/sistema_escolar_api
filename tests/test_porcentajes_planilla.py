"""Porcentajes por tipo de nota, paso B2b: guardarlos, verlos y borrarlos.

Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md` (PB1 a PB3, PB8 y PB10). Cada
prueba pasa por la aplicacion real (ASGI) con una base simulada que responde
segun un fragmento del SQL y cuenta conexiones, consultas, confirmaciones y
reversiones. El usuario de la sesion se dobla.

El calculo lo fija `test_nota_periodo.py`; la tabla, su migracion
`test_migracion_planilla_tipos_porcentaje.py`; el año lectivo de la ruta
nueva, `test_anio_lectivo_guardia.py`.
"""
import asyncio
import json
from decimal import Decimal

import pytest

from app.controllers import porcentajes_planilla_controller as controlador
from app.db import session


PROFESOR = {"id": 7, "rol": "profesor"}
ADMIN = {"id": 1, "rol": "admin"}

ESCRITURAS = ("INSERT", "UPDATE", "DELETE")


class Base:
    """Pool, conexiones y cursores simulados.

    `respuestas` son `(fragmento, fetchone, fetchall)`: la primera cuyo
    fragmento aparezca en el SQL decide lo que devuelve. Lo que no coincide
    devuelve `None` y `[]`.
    """

    def __init__(self, respuestas=(), *, dueno=True):
        self.conexiones = 0
        self.consultas = []
        self.commits = 0
        self.rollbacks = 0
        self.respuestas = list(respuestas) + [
            ("SELECT al.anio, al.estado FROM", (2026, "activo"), []),
            ("FROM asignaciones WHERE id = %s AND profesor_id", (1,) if dueno else None, []),
            ("AS asignacion_academica_id", (77,), []),
        ]

    def getconn(self):
        self.conexiones += 1
        return ConexionFalsa(self)

    def putconn(self, conexion, close=False):
        pass

    @property
    def escrituras(self):
        return [(t, p) for t, p in self.consultas if t.split()[0] in ESCRITURAS]

    def sentencia(self, fragmento):
        (encontrada,) = [(t, p) for t, p in self.consultas if fragmento in t]
        return encontrada

    def menciona(self, tabla):
        return any(tabla in texto for texto, _ in self.consultas)


class ConexionFalsa:
    def __init__(self, base):
        self.base = base
        self.autocommit = False

    def cursor(self, *args, **kwargs):
        return CursorFalso(self.base)

    def commit(self):
        self.base.commits += 1

    def rollback(self):
        self.base.rollbacks += 1

    def close(self):
        pass


class CursorFalso:
    def __init__(self, base):
        self.base = base
        self._uno = None
        self._todos = []
        self.rowcount = 1
        self.description = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params=None):
        texto = " ".join(str(sql).split())
        if texto == "PREPARACION":
            return
        self.base.consultas.append((texto, params))
        self._uno, self._todos = None, []
        for fragmento, uno, todos in self.base.respuestas:
            if fragmento in texto:
                self._uno, self._todos = uno, list(todos)
                break

    def fetchone(self):
        return self._uno

    def fetchall(self):
        return list(self._todos)

    def close(self):
        pass


@pytest.fixture
def con_base(monkeypatch):
    monkeypatch.setattr(
        session, "apply_session_setup", lambda cursor: cursor.execute("PREPARACION")
    )

    def usar(base):
        monkeypatch.setattr(session, "get_pool", lambda: base)
        return base

    return usar


def peticion(usuario, metodo, ruta, cuerpo=None):
    """Una peticion real contra la app con `usuario` en sesion."""
    from app.dependencies import get_current_user
    from app.main import app

    ruta, _, consulta = ruta.partition("?")
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

    app.dependency_overrides[get_current_user] = lambda: usuario
    try:
        asyncio.run(app(scope, receive, send))
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    return salida["status"], json.loads(salida["body"].decode() or "null")


RUTA = "/planilla/tipos/porcentaje"
TABLA = "planilla_tipos_porcentaje"

BLOQUEO = ("FOR NO KEY UPDATE", (77,), [])
LEER_TIPOS = "SELECT DISTINCT descripcion FROM notas_detalle"
LEER_PORCENTAJES = "SELECT tipo_nota, porcentaje FROM planilla_tipos_porcentaje"
TIPOS = [("Cognitivo",), ("Procedimental",), ("Actitudinal",), ("mas_alto",)]


def _clase(porcentajes, tipos=TIPOS):
    """La clase con sus tipos de nota y los porcentajes ya guardados."""
    return [
        BLOQUEO,
        (LEER_TIPOS, None, tipos),
        (LEER_PORCENTAJES, None, porcentajes),
    ]


def _cuerpo(tipo_nota, porcentaje):
    return {"asignacion_id": 9, "periodo": 2, "tipo_nota": tipo_nota, "porcentaje": porcentaje}


# ---------------------------------------------------------------------------
# Guardar y quitar un porcentaje
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("usuario,consultas", [(ADMIN, 6), (PROFESOR, 7)])
def test_guardar_el_porcentaje_que_completa_los_100(con_base, usuario, consultas):
    base = con_base(Base(_clase([("Cognitivo", 50), ("Procedimental", 30)])))

    status, respuesta = peticion(usuario, "PUT", RUTA, _cuerpo(" actitudinal ", 20))

    assert status == 200
    # Con el nombre exacto de la columna, como lo ve la planilla.
    assert respuesta == {"tipo_nota": "Actitudinal", "porcentaje": 20, "suma": 100, "activos": True}
    assert base.sentencia(f"INSERT INTO {TABLA}")[1] == (77, 2, "Actitudinal", 20)
    # La clase se bloquea antes de leer: dos guardados a la vez no pasan de 100.
    textos = [texto for texto, _ in base.consultas]
    bloqueo = next(i for i, t in enumerate(textos) if "FOR NO KEY UPDATE" in t)
    lectura = next(i for i, t in enumerate(textos) if LEER_PORCENTAJES in t)
    assert bloqueo < lectura
    assert base.sentencia("FOR NO KEY UPDATE")[1] == (77,)
    assert base.sentencia(LEER_TIPOS)[1] == (77, 2)
    assert base.conexiones == 1
    assert len(base.consultas) == consultas
    assert base.commits == 1


def test_cambiar_un_porcentaje_no_cuenta_el_que_tenia(con_base):
    base = con_base(Base(_clase([("Cognitivo", 50), ("Procedimental", 30), ("Actitudinal", 20)])))

    status, respuesta = peticion(ADMIN, "PUT", RUTA, _cuerpo("Cognitivo", 40))

    assert status == 200
    assert respuesta == {"tipo_nota": "Cognitivo", "porcentaje": 40, "suma": 90, "activos": False}
    assert base.sentencia(f"INSERT INTO {TABLA}")[1] == (77, 2, "Cognitivo", 40)


def test_quitar_un_porcentaje_con_null(con_base):
    base = con_base(Base(_clase([("Cognitivo", 50), ("Procedimental", 30)])))

    status, respuesta = peticion(ADMIN, "PUT", RUTA, _cuerpo("Procedimental", None))

    assert status == 200
    assert respuesta == {"tipo_nota": "Procedimental", "porcentaje": None, "suma": 50, "activos": False}
    assert [texto.split()[0] for texto, _ in base.escrituras] == ["DELETE"]
    assert base.sentencia(f"DELETE FROM {TABLA}")[1] == (77, 2, "Procedimental")
    assert base.commits == 1


def test_si_la_suma_pasa_de_100_responde_422_sin_escribir(con_base):
    base = con_base(Base(_clase([("Cognitivo", 50), ("Procedimental", 30)])))

    status, respuesta = peticion(ADMIN, "PUT", RUTA, _cuerpo("Actitudinal", 21))

    assert status == 422
    assert respuesta == {"detail": controlador.SUMA_EXCEDIDA}
    assert base.escrituras == []
    assert base.commits == 0


def test_el_porcentaje_de_un_tipo_que_ya_no_existe_no_cuenta_en_la_suma(con_base):
    base = con_base(Base(_clase([("Cognitivo", 50), ("Borrado", 90)])))

    status, respuesta = peticion(ADMIN, "PUT", RUTA, _cuerpo("Procedimental", 50))

    assert status == 200
    assert respuesta["suma"] == 100
    assert base.sentencia(f"INSERT INTO {TABLA}")[1] == (77, 2, "Procedimental", 50)


def test_en_un_tipo_que_no_existe_responde_404(con_base):
    base = con_base(Base(_clase([], tipos=[("Cognitivo",)])))

    status, respuesta = peticion(ADMIN, "PUT", RUTA, _cuerpo("Actitudinal", 20))

    assert status == 404
    assert respuesta == {"detail": controlador.TIPO_NO_ENCONTRADO}
    assert base.escrituras == []


@pytest.mark.parametrize("tipo", ["mas_alto", "Desde React"])
def test_en_una_columna_interna_responde_422_sin_tocar_la_base(con_base, tipo):
    base = con_base(Base())

    status, respuesta = peticion(ADMIN, "PUT", RUTA, _cuerpo(tipo, 20))

    assert status == 422
    assert respuesta == {"detail": controlador.TIPO_SIN_PORCENTAJE}
    assert base.conexiones == 0


@pytest.mark.parametrize("porcentaje", [0, 101, -5, 33.5])
def test_un_porcentaje_que_no_es_entero_de_1_a_100_responde_422_sin_tocar_la_base(
    con_base, porcentaje
):
    base = con_base(Base())

    status, respuesta = peticion(ADMIN, "PUT", RUTA, _cuerpo("Cognitivo", porcentaje))

    assert status == 422
    assert respuesta == {"detail": controlador.PORCENTAJE_INVALIDO}
    assert base.conexiones == 0


@pytest.mark.parametrize("porcentaje", ["40", True])
def test_texto_o_booleano_no_son_porcentaje(con_base, porcentaje):
    base = con_base(Base())

    status, _ = peticion(ADMIN, "PUT", RUTA, _cuerpo("Cognitivo", porcentaje))

    assert status == 422
    assert base.conexiones == 0


def test_el_porcentaje_es_obligatorio_aunque_sea_null(con_base):
    """Quitar un porcentaje se pide con `null` a proposito, no por olvido."""
    base = con_base(Base())
    cuerpo = _cuerpo("Cognitivo", 20)
    del cuerpo["porcentaje"]

    status, _ = peticion(ADMIN, "PUT", RUTA, cuerpo)

    assert status == 422
    assert base.conexiones == 0


def test_un_profesor_ajeno_no_guarda_nada(con_base):
    base = con_base(Base(_clase([]), dueno=False))

    status, _ = peticion(PROFESOR, "PUT", RUTA, _cuerpo("Cognitivo", 20))

    assert status == 403
    # Solo el permiso: ni el año de la clase se consulta.
    assert len(base.consultas) == 1
    assert base.escrituras == []


def test_los_mensajes_son_constantes_sin_nada_de_la_base():
    mensajes = [
        controlador.TIPO_NO_ENCONTRADO,
        controlador.TIPO_SIN_PORCENTAJE,
        controlador.PORCENTAJE_INVALIDO,
        controlador.SUMA_EXCEDIDA,
    ]
    assert all(isinstance(m, str) and m and "{" not in m for m in mensajes)


# ---------------------------------------------------------------------------
# Leer los porcentajes con la planilla
# ---------------------------------------------------------------------------

FILAS_PLANILLA = [
    (1, "Ana", "Gómez", "Matemáticas", "Cognitivo", Decimal("3.80"), "numerica", None, 10),
    (1, "Ana", "Gómez", "Matemáticas", "Procedimental", Decimal("4.00"), "numerica", None, 11),
]
PLANILLA = [
    ("LEFT JOIN notas_detalle nd", None, FILAS_PLANILLA),
    (LEER_PORCENTAJES, None, [("cognitivo", 60), ("Procedimental", 40)]),
]


@pytest.mark.parametrize("usuario,conexiones,consultas", [(ADMIN, 1, 3), (PROFESOR, 2, 4)])
def test_la_planilla_con_porcentajes_suma_una_consulta_y_ninguna_conexion(
    con_base, usuario, conexiones, consultas
):
    base = con_base(Base(PLANILLA))

    status, respuesta = peticion(usuario, "GET", "/planilla-excel/12/2?con_porcentajes=true")

    assert status == 200
    assert respuesta["porcentajes"] == {"Cognitivo": 60, "Procedimental": 40}
    assert respuesta["porcentajes_activos"] is True
    # Lo demas sigue igual que sin el parametro.
    assert respuesta["columnas"] == ["Cognitivo", "Procedimental"]
    assert "subnotas" not in respuesta
    assert base.sentencia(LEER_PORCENTAJES)[1] == (77, 2)
    assert base.conexiones == conexiones
    assert len(base.consultas) == consultas


@pytest.mark.parametrize("consulta", ["", "?con_subnotas=true"])
def test_la_planilla_sin_el_parametro_no_mira_los_porcentajes(con_base, consulta):
    """Asistencia y la planilla de hoy no pagan una consulta de mas."""
    base = con_base(Base(PLANILLA))

    status, respuesta = peticion(ADMIN, "GET", f"/planilla-excel/12/2{consulta}")

    assert status == 200
    assert "porcentajes" not in respuesta
    assert "porcentajes_activos" not in respuesta
    assert not base.menciona(TABLA)


def test_la_planilla_con_subnotas_y_porcentajes_trae_las_dos_cosas(con_base):
    base = con_base(Base(PLANILLA))

    status, respuesta = peticion(
        ADMIN, "GET", "/planilla-excel/12/2?con_subnotas=true&con_porcentajes=true"
    )

    assert status == 200
    assert respuesta["subnotas"] == {}
    assert respuesta["porcentajes"] == {"Cognitivo": 60, "Procedimental": 40}
    assert len(base.consultas) == 4
    assert base.conexiones == 1


# ---------------------------------------------------------------------------
# PB10: borrar un tipo borra su porcentaje
# ---------------------------------------------------------------------------

def test_borrar_un_tipo_borra_su_porcentaje_en_la_misma_transaccion(con_base):
    base = con_base(Base())

    status, _ = peticion(
        ADMIN, "DELETE", "/planilla/tipo?asignacion_id=9&descripcion=Cognitivo&periodo=2"
    )

    assert status == 200
    assert base.sentencia(f"DELETE FROM {TABLA}")[1] == (77, 2, "Cognitivo")
    assert base.conexiones == 1
    assert base.commits == 1
