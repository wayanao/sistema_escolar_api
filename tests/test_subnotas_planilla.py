"""Subnotas de la planilla, paso A1: rutas, reglas y conteos.

Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`. Cada prueba pasa por la
aplicacion real (ASGI) con una base simulada que responde segun un fragmento
del SQL y cuenta conexiones, consultas, confirmaciones y reversiones. El
usuario de la sesion se dobla.

Lo que no debe cambiar sin subnotas lo fija `test_subnotas_planilla_caracterizacion.py`;
el calculo, `test_subnotas_planilla_calculo.py`; el año lectivo de las rutas
nuevas, `test_anio_lectivo_guardia.py`.
"""
import asyncio
import json
from decimal import Decimal

import pytest
from psycopg2 import IntegrityError

from app.controllers import subnotas_planilla_controller as controlador
from app.controllers.planilla_controller import NOTA_CALCULADA
from app.db import session


PROFESOR = {"id": 7, "rol": "profesor"}
ADMIN = {"id": 1, "rol": "admin"}

ESCRITURAS = ("INSERT", "UPDATE", "DELETE")


class Base:
    """Pool, conexiones y cursores simulados.

    `respuestas` son `(fragmento, fetchone, fetchall)`: la primera cuyo
    fragmento aparezca en el SQL decide lo que devuelve. Si `fetchone` es una
    excepcion, se lanza al ejecutar. Lo que no coincide devuelve `None` y `[]`.
    """

    def __init__(self, respuestas=(), *, nivel=None, dueno=True, estudiante_del_curso=True):
        self.conexiones = 0
        self.consultas = []
        self.commits = 0
        self.rollbacks = 0
        self.respuestas = list(respuestas) + [
            ("SELECT al.anio, al.estado FROM", (2026, "activo"), []),
            ("FROM asignaciones WHERE id = %s AND profesor_id", (1,) if dueno else None, []),
            ("AS asignacion_academica_id", (77,), []),
            ("SELECT c.nivel", (nivel,), []),
            ("SELECT 1 FROM estudiantes e", (1,) if estudiante_del_curso else None, []),
            ("SELECT e.id FROM estudiantes e", (3,) if estudiante_del_curso else None, []),
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
                if isinstance(uno, Exception):
                    raise uno
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


# ---------------------------------------------------------------------------
# Leer la planilla con subnotas
# ---------------------------------------------------------------------------

FILAS_PLANILLA = [
    (1, "Ana", "Gómez", "Matemáticas", "Cognitivo", Decimal("3.80"), "numerica", None, 10),
    (2, "Luis", "Pérez", "Matemáticas", "Cognitivo", Decimal("4.00"), "numerica", None, 11),
]
FILAS_SUBNOTAS = [
    (7, "Cognitivo", "Taller 1", 1, Decimal("4.00"), None),
    (8, "Cognitivo", "Quiz", None, None, None),
]
PLANILLA = [
    ("LEFT JOIN notas_detalle nd", None, FILAS_PLANILLA),
    ("FROM planilla_subnotas s LEFT JOIN", None, FILAS_SUBNOTAS),
]


@pytest.mark.parametrize("usuario,conexiones,consultas", [(ADMIN, 1, 3), (PROFESOR, 2, 4)])
def test_la_planilla_con_subnotas_suma_una_consulta_y_ninguna_conexion(
    con_base, usuario, conexiones, consultas
):
    base = con_base(Base(PLANILLA))

    status, respuesta = peticion(usuario, "GET", "/planilla-excel/12/2?con_subnotas=true")

    assert status == 200
    assert respuesta["subnotas"] == {
        "Cognitivo": [{"id": 7, "nombre": "Taller 1"}, {"id": 8, "nombre": "Quiz"}]
    }
    assert [e["subnotas"] for e in respuesta["data"]] == [{"7": 4.0}, {}]
    # Lo demas sigue igual que sin el parametro.
    assert respuesta["columnas"] == ["Cognitivo"]
    assert respuesta["data"][0]["notas"] == {"Cognitivo": 3.8}
    assert base.conexiones == conexiones
    assert len(base.consultas) == consultas
    assert base.sentencia("FROM planilla_subnotas s LEFT JOIN")[1] == (77, 2)


def test_la_planilla_sin_el_parametro_no_mira_las_subnotas(con_base):
    base = con_base(Base(PLANILLA))

    status, respuesta = peticion(ADMIN, "GET", "/planilla-excel/12/2")

    assert status == 200
    assert "subnotas" not in respuesta
    assert all("subnotas" not in estudiante for estudiante in respuesta["data"])
    assert len(base.consultas) == 2
    assert not any("planilla_subnotas" in texto for texto, _ in base.consultas)


# ---------------------------------------------------------------------------
# Los dos cambios en las rutas viejas
# ---------------------------------------------------------------------------

NOTA_A_MANO = {
    "estudiante_id": 3, "asignacion_id": 9, "nota": 4.0, "descripcion": "Cognitivo", "periodo": 1,
}


def test_una_celda_con_subnotas_no_se_escribe_a_mano(con_base):
    """P1: el servidor rechaza la nota a mano. Pasa con una pestaña vieja."""
    base = con_base(Base([("FROM planilla_subnotas s", (1,), [])]))

    status, respuesta = peticion(PROFESOR, "POST", "/planilla/nota", NOTA_A_MANO)

    assert status == 409
    assert respuesta == {"detail": NOTA_CALCULADA}
    assert base.escrituras == []
    assert base.commits == 0
    # Se pregunta por la asignacion academica ya resuelta, como el guardado.
    assert base.sentencia("FROM planilla_subnotas s")[1] == (77, 1, "Cognitivo", 3)


def test_una_celda_sin_subnotas_se_escribe_a_mano_como_siempre(con_base):
    base = con_base(Base([
        ("FROM planilla_subnotas s", None, []),
        ("INSERT INTO notas_detalle", (950,), []),
    ]))

    status, respuesta = peticion(PROFESOR, "POST", "/planilla/nota", NOTA_A_MANO)

    assert status == 200
    assert respuesta == {"mensaje": "Nota registrada correctamente", "nota_id": 950}
    # 2026-11-23: primero se intenta cambiar la que existe; como no hay, se inserta.
    assert [t.split()[0] for t, _ in base.escrituras] == ["UPDATE", "INSERT"]
    assert base.commits == 1


def test_borrar_un_tipo_borra_sus_subnotas_en_la_misma_transaccion(con_base):
    base = con_base(Base())

    status, _ = peticion(ADMIN, "DELETE", "/planilla/tipo?asignacion_id=9&descripcion=Cognitivo&periodo=2")

    assert status == 200
    borrado = base.sentencia("DELETE FROM planilla_subnotas")
    assert borrado[1] == (77, 2, "Cognitivo")
    assert base.conexiones == 1
    assert base.commits == 1


# ---------------------------------------------------------------------------
# Crear una subnota
# ---------------------------------------------------------------------------

SUBNOTA = {"asignacion_id": 9, "periodo": 2, "tipo_nota": " Cognitivo ", "nombre": "  Taller 1 "}
TIPO_EXISTE = ("SELECT 1 FROM notas_detalle", (1,), [])


@pytest.mark.parametrize("usuario,consultas", [(ADMIN, 5), (PROFESOR, 6)])
def test_crear_una_subnota(con_base, usuario, consultas):
    base = con_base(Base([
        TIPO_EXISTE,
        ("COUNT(*) FILTER", (3, 0), []),
        ("INSERT INTO planilla_subnotas", (41,), []),
    ]))

    status, respuesta = peticion(usuario, "POST", "/planilla/subnotas", SUBNOTA)

    assert status == 201
    assert respuesta == {"id": 41, "tipo_nota": "Cognitivo", "nombre": "Taller 1"}
    assert base.sentencia("INSERT INTO planilla_subnotas")[1] == (77, 2, "Cognitivo", "Taller 1")
    assert base.conexiones == 1
    assert len(base.consultas) == consultas
    assert base.commits == 1


def test_crear_en_una_columna_interna_responde_422_sin_tocar_la_base(con_base):
    base = con_base(Base())

    status, respuesta = peticion(ADMIN, "POST", "/planilla/subnotas", {**SUBNOTA, "tipo_nota": "mas_alto"})

    assert status == 422
    assert respuesta == {"detail": controlador.TIPO_SIN_SUBNOTAS}
    assert base.conexiones == 0


def test_crear_en_un_tipo_que_no_existe_responde_404(con_base):
    base = con_base(Base([("SELECT 1 FROM notas_detalle", None, [])]))

    status, respuesta = peticion(ADMIN, "POST", "/planilla/subnotas", SUBNOTA)

    assert status == 404
    assert respuesta == {"detail": controlador.TIPO_NO_ENCONTRADO}
    assert base.escrituras == []


@pytest.mark.parametrize(
    "conteo,codigo,mensaje",
    [
        ((3, 1), 409, controlador.SUBNOTA_DUPLICADA),
        ((20, 0), 422, controlador.LIMITE_DE_SUBNOTAS),
    ],
)
def test_crear_respeta_nombre_unico_y_limite(con_base, conteo, codigo, mensaje):
    base = con_base(Base([TIPO_EXISTE, ("COUNT(*) FILTER", conteo, [])]))

    status, respuesta = peticion(ADMIN, "POST", "/planilla/subnotas", SUBNOTA)

    assert status == codigo
    assert respuesta == {"detail": mensaje}
    assert base.escrituras == []


def test_crear_dos_a_la_vez_lo_frena_el_indice_unico_con_409(con_base):
    """La carrera que el conteo no ve: el indice rechaza y sale 409, no 500."""
    base = con_base(Base([
        TIPO_EXISTE,
        ("COUNT(*) FILTER", (3, 0), []),
        ("INSERT INTO planilla_subnotas", IntegrityError("duplicate key"), []),
    ]))

    status, respuesta = peticion(ADMIN, "POST", "/planilla/subnotas", SUBNOTA)

    assert status == 409
    assert respuesta == {"detail": controlador.SUBNOTA_DUPLICADA}
    assert base.commits == 0
    assert base.rollbacks >= 1


def test_un_profesor_ajeno_no_crea_nada(con_base):
    base = con_base(Base([TIPO_EXISTE], dueno=False))

    status, _ = peticion(PROFESOR, "POST", "/planilla/subnotas", SUBNOTA)

    assert status == 403
    # Solo el permiso: ni el año de la clase se consulta.
    assert len(base.consultas) == 1
    assert base.escrituras == []


# ---------------------------------------------------------------------------
# Renombrar una subnota
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("usuario,consultas", [(ADMIN, 3), (PROFESOR, 4)])
def test_renombrar_una_subnota(con_base, usuario, consultas):
    base = con_base(Base([("UPDATE planilla_subnotas", (5,), [])]))

    status, respuesta = peticion(
        usuario, "PUT", "/planilla/subnotas/5", {"asignacion_id": 9, "nombre": " Quiz 2 "}
    )

    assert status == 200
    assert respuesta == {"id": 5, "nombre": "Quiz 2"}
    # El id de la clase va en el WHERE: no se renombra la subnota de otra clase.
    assert base.sentencia("UPDATE planilla_subnotas")[1] == ("Quiz 2", 5, 77)
    assert len(base.consultas) == consultas
    assert base.commits == 1


@pytest.mark.parametrize(
    "resultado,codigo,mensaje",
    [
        (None, 404, controlador.SUBNOTA_NO_ENCONTRADA),
        (IntegrityError("duplicate key"), 409, controlador.SUBNOTA_DUPLICADA),
    ],
)
def test_renombrar_una_que_no_existe_o_a_un_nombre_repetido(con_base, resultado, codigo, mensaje):
    base = con_base(Base([("UPDATE planilla_subnotas", resultado, [])]))

    status, respuesta = peticion(
        ADMIN, "PUT", "/planilla/subnotas/5", {"asignacion_id": 9, "nombre": "Quiz"}
    )

    assert status == codigo
    assert respuesta == {"detail": mensaje}
    assert base.commits == 0


# ---------------------------------------------------------------------------
# Borrar una subnota
# ---------------------------------------------------------------------------

SUBNOTA_BUSCADA = ("SELECT periodo, tipo_nota FROM planilla_subnotas", (1, "Cognitivo"), [])
# (subnota, estudiante, nota, valoracion) del tipo Cognitivo. Se borra la 5.
CALIFICACIONES = [
    (5, 1, Decimal("4.00"), None),
    (6, 1, Decimal("3.00"), None),
    (5, 2, Decimal("5.00"), None),
    (6, 3, Decimal("2.00"), None),
]


@pytest.mark.parametrize("usuario,consultas", [(ADMIN, 9), (PROFESOR, 10)])
def test_borrar_una_subnota_recalcula_solo_a_los_afectados(con_base, usuario, consultas):
    base = con_base(Base([
        SUBNOTA_BUSCADA,
        ("SELECT v.subnota_id, v.estudiante_id", None, CALIFICACIONES),
    ]))

    status, respuesta = peticion(usuario, "DELETE", "/planilla/subnotas/5?asignacion_id=9")

    assert status == 200
    # Ana (1) queda con su 3.00; Luis (2) no tiene nada mas y su celda queda
    # vacia (P4). Eva (3) no tenia la 5 calificada: su celda no se toca (P2).
    assert respuesta == {
        "mensaje": "Subnota eliminada correctamente",
        "calificaciones_borradas": 2,
        "celdas": {
            "1": {"nota": 3.0, "valoracion": None},
            "2": {"nota": None, "valoracion": None},
        },
    }
    assert base.sentencia("DELETE FROM planilla_subnotas WHERE id")[1] == (5,)
    # 2026-11-23: primero se cambian en su lugar las celdas que existen. Aqui
    # ninguna existia (la base no devuelve filas): se insertan las dos, sin
    # borrar nada.
    assert base.sentencia("UPDATE notas_detalle nd")[1] == (
        "Cognitivo", [1, 2], [Decimal("3.00"), None], ["numerica", "numerica"], [None, None],
        77, 1, "Cognitivo",
    )
    assert not any(t.startswith("DELETE FROM notas_detalle") for t, _ in base.consultas)
    assert base.sentencia("INSERT INTO notas_detalle")[1] == (
        77, 1, "Cognitivo", [1, 2], [Decimal("3.00"), None], ["numerica", "numerica"], [None, None],
    )
    # Siempre las mismas consultas, sean 2 o 40 los afectados.
    assert len(base.consultas) == consultas
    assert base.conexiones == 1
    assert base.commits == 1


@pytest.mark.parametrize("usuario,consultas", [(ADMIN, 9), (PROFESOR, 10)])
def test_borrar_una_subnota_cambia_las_celdas_en_su_lugar(con_base, usuario, consultas):
    """2026-11-23: si las celdas ya existen (lo normal), se cambian sin borrarlas
    -conservan su `id` y su tarjeta en Boletin final- y solo se quitan las
    repetidas. Nada se inserta y son las mismas consultas de siempre."""
    base = con_base(Base([
        SUBNOTA_BUSCADA,
        ("SELECT v.subnota_id, v.estudiante_id", None, CALIFICACIONES),
        ("UPDATE notas_detalle nd", None, [(1, 501), (2, 502)]),
    ]))

    status, respuesta = peticion(usuario, "DELETE", "/planilla/subnotas/5?asignacion_id=9")

    assert status == 200
    assert respuesta["celdas"] == {
        "1": {"nota": 3.0, "valoracion": None},
        "2": {"nota": None, "valoracion": None},
    }
    assert base.sentencia("DELETE FROM notas_detalle")[1] == (77, 1, "Cognitivo", [1, 2], [501, 502])
    assert not any("INSERT INTO notas_detalle" in t for t, _ in base.consultas)
    assert len(base.consultas) == consultas
    assert base.commits == 1


def test_borrar_una_subnota_inserta_solo_la_celda_que_faltaba(con_base):
    """Ana (1) tenia celda y se cambia; Luis (2) no tenia y se inserta: una
    consulta mas, sin crecer con el numero de estudiantes."""
    base = con_base(Base([
        SUBNOTA_BUSCADA,
        ("SELECT v.subnota_id, v.estudiante_id", None, CALIFICACIONES),
        ("UPDATE notas_detalle nd", None, [(1, 501)]),
    ]))

    status, _ = peticion(ADMIN, "DELETE", "/planilla/subnotas/5?asignacion_id=9")

    assert status == 200
    assert base.sentencia("DELETE FROM notas_detalle")[1] == (77, 1, "Cognitivo", [1], [501])
    assert base.sentencia("INSERT INTO notas_detalle")[1] == (
        77, 1, "Cognitivo", [2], [None], ["numerica"], [None],
    )
    assert len(base.consultas) == 10


def test_borrar_una_subnota_de_preescolar_deja_la_carita_de_lo_que_queda(con_base):
    base = con_base(Base(
        [
            SUBNOTA_BUSCADA,
            ("SELECT v.subnota_id, v.estudiante_id", None, [
                (5, 1, None, "destacado"),
                (6, 1, None, "apoyo"),
            ]),
        ],
        nivel="preescolar",
    ))

    status, respuesta = peticion(ADMIN, "DELETE", "/planilla/subnotas/6?asignacion_id=9")

    assert status == 200
    assert respuesta["celdas"] == {"1": {"nota": None, "valoracion": "destacado"}}
    assert base.sentencia("INSERT INTO notas_detalle")[1][3:] == (
        [1], [None], ["desarrollo"], ["destacado"],
    )


def test_borrar_una_subnota_sin_calificar_no_toca_ninguna_celda(con_base):
    base = con_base(Base([SUBNOTA_BUSCADA]))

    status, respuesta = peticion(ADMIN, "DELETE", "/planilla/subnotas/5?asignacion_id=9")

    assert status == 200
    assert respuesta["calificaciones_borradas"] == 0
    assert respuesta["celdas"] == {}
    assert not any("notas_detalle" in texto for texto, _ in base.escrituras)
    assert not any("SELECT c.nivel" in texto for texto, _ in base.consultas)
    assert len(base.consultas) == 6


def test_borrar_una_subnota_de_otra_clase_responde_404(con_base):
    base = con_base(Base([("SELECT periodo, tipo_nota FROM planilla_subnotas", None, [])]))

    status, respuesta = peticion(ADMIN, "DELETE", "/planilla/subnotas/5?asignacion_id=9")

    assert status == 404
    assert respuesta == {"detail": controlador.SUBNOTA_NO_ENCONTRADA}
    assert base.escrituras == []


# ---------------------------------------------------------------------------
# Guardar las calificaciones de un estudiante
# ---------------------------------------------------------------------------

def _valores(valores, **extra):
    return {
        "asignacion_id": 9, "periodo": 1, "tipo_nota": "Cognitivo", "estudiante_id": 3,
        "valores": valores, **extra,
    }


# Lo que ya tiene el estudiante en las tres subnotas del tipo.
ACTUALES = [(5, Decimal("4.00"), None), (6, None, None), (7, Decimal("2.00"), None)]
CELDA_INSERTADA = ("INSERT INTO notas_detalle", (950,), [])


def _bloqueo(actuales):
    return ("FOR UPDATE OF s", None, actuales)


@pytest.mark.parametrize("usuario,consultas", [(ADMIN, 9), (PROFESOR, 10)])
def test_guardar_calificaciones_recalcula_la_celda(con_base, usuario, consultas):
    base = con_base(Base([_bloqueo(ACTUALES), CELDA_INSERTADA]))

    status, respuesta = peticion(
        usuario, "POST", "/planilla/subnotas/valores", _valores({"6": 3.5, "7": None})
    )

    assert status == 200
    # (4.00 + 3.50) / 2: la 5 se conserva aunque no venga, la 7 se vacia.
    assert respuesta == {
        "estudiante_id": 3,
        "tipo_nota": "Cognitivo",
        "tipo_evaluacion": "numerica",
        "nota": 3.75,
        "valoracion": None,
        "subnotas": {"5": 4.0, "6": 3.5},
    }
    assert base.sentencia("DELETE FROM planilla_subnotas_valores")[1] == (3, [7])
    assert base.sentencia("INSERT INTO planilla_subnotas_valores")[1] == (
        3, [6], [Decimal("3.50")], [None],
    )
    # La celda se escribe con las dos sentencias del guardado a mano
    # (`planilla_service.guardar_celda`): intentar cambiarla en su lugar y,
    # como aqui no existia, insertarla.
    assert base.sentencia("UPDATE notas_detalle")[1] == (
        Decimal("3.75"), "Cognitivo", "numerica", None, 3, 77, 1, "Cognitivo",
    )
    assert base.sentencia("INSERT INTO notas_detalle")[1] == (
        3, 77, 1, Decimal("3.75"), "Cognitivo", "numerica", None,
    )
    assert base.sentencia("FOR UPDATE OF s")[1] == (3, 77, 1, "Cognitivo")
    assert len(base.consultas) == consultas
    # El permiso del profesor viaja en la misma conexion.
    assert base.conexiones == 1
    assert base.commits == 1


def test_vaciar_todas_las_subnotas_deja_la_celda_vacia(con_base):
    """P4: la celda queda con `nota NULL`, como al borrar una nota a mano."""
    base = con_base(Base([_bloqueo(ACTUALES), CELDA_INSERTADA]))

    status, respuesta = peticion(
        ADMIN, "POST", "/planilla/subnotas/valores", _valores({"5": None, "7": None})
    )

    assert status == 200
    assert respuesta["nota"] is None
    assert respuesta["subnotas"] == {}
    assert base.sentencia("INSERT INTO notas_detalle")[1][3] is None
    assert not any("planilla_subnotas_valores" in t and t.startswith("INSERT") for t, _ in base.consultas)


def test_en_preescolar_se_guardan_caritas_aunque_la_pantalla_pida_numeros(con_base):
    base = con_base(Base([_bloqueo(ACTUALES), CELDA_INSERTADA], nivel="preescolar"))

    status, respuesta = peticion(
        ADMIN, "POST", "/planilla/subnotas/valores",
        _valores({"5": "logrado", "6": "destacado", "7": None}, tipo_evaluacion="numerica"),
    )

    assert status == 200
    # (4 + 5) / 2 = 4.5, empate: la mas alta.
    assert respuesta["tipo_evaluacion"] == "desarrollo"
    assert respuesta["valoracion"] == "destacado"
    assert respuesta["nota"] is None
    assert base.sentencia("INSERT INTO notas_detalle")[1] == (
        3, 77, 1, None, "Cognitivo", "desarrollo", "destacado",
    )


@pytest.mark.parametrize(
    "valores,nivel,mensaje",
    [
        ({"5": 5.5}, None, controlador.NOTA_INVALIDA),
        ({"5": 0.5}, None, controlador.NOTA_INVALIDA),
        ({"5": "4"}, None, controlador.NOTA_INVALIDA),
        ({"5": "logrado"}, "primaria", controlador.NOTA_INVALIDA),
        ({"5": 4.0}, "preescolar", controlador.CARITA_INVALIDA),
        ({"5": "Alto"}, "preescolar", controlador.CARITA_INVALIDA),
        ({"99": 4.0}, None, controlador.SUBNOTAS_AJENAS),
    ],
)
def test_guardar_rechaza_calificaciones_que_no_sirven_sin_escribir_nada(
    con_base, valores, nivel, mensaje
):
    base = con_base(Base([_bloqueo(ACTUALES)], nivel=nivel))

    status, respuesta = peticion(ADMIN, "POST", "/planilla/subnotas/valores", _valores(valores))

    assert status == 422
    assert respuesta == {"detail": mensaje}
    assert base.escrituras == []
    assert base.commits == 0


def test_guardar_en_un_tipo_sin_subnotas_responde_422(con_base):
    base = con_base(Base([_bloqueo([])]))

    status, respuesta = peticion(ADMIN, "POST", "/planilla/subnotas/valores", _valores({"5": 4.0}))

    assert status == 422
    assert respuesta == {"detail": controlador.SUBNOTAS_AJENAS}
    assert base.escrituras == []


def test_guardar_a_un_estudiante_de_otro_curso_responde_403(con_base):
    base = con_base(Base([_bloqueo(ACTUALES)], estudiante_del_curso=False))

    status, respuesta = peticion(ADMIN, "POST", "/planilla/subnotas/valores", _valores({"5": 4.0}))

    assert status == 403
    assert respuesta == {"detail": "El estudiante no pertenece a esta asignación"}
    assert base.escrituras == []


def test_un_profesor_ajeno_no_guarda_calificaciones(con_base):
    base = con_base(Base([_bloqueo(ACTUALES)], dueno=False))

    status, _ = peticion(PROFESOR, "POST", "/planilla/subnotas/valores", _valores({"5": 4.0}))

    assert status == 403
    assert len(base.consultas) == 1
    assert base.escrituras == []


def test_el_cuerpo_sin_valores_responde_422_antes_de_abrir_la_base(con_base):
    base = con_base(Base())

    status, _ = peticion(ADMIN, "POST", "/planilla/subnotas/valores", _valores({}))

    assert status == 422
    assert base.conexiones == 0


# ---------------------------------------------------------------------------
# Mensajes
# ---------------------------------------------------------------------------


def test_los_mensajes_son_constantes_sin_nada_de_la_base():
    mensajes = [
        controlador.TIPO_NO_ENCONTRADO,
        controlador.TIPO_SIN_SUBNOTAS,
        controlador.SUBNOTA_DUPLICADA,
        controlador.LIMITE_DE_SUBNOTAS,
        controlador.SUBNOTA_NO_ENCONTRADA,
        controlador.SUBNOTAS_AJENAS,
        controlador.NOTA_INVALIDA,
        controlador.CARITA_INVALIDA,
        NOTA_CALCULADA,
    ]

    assert all(isinstance(mensaje, str) and mensaje for mensaje in mensajes)
    assert not any("planilla_subnotas" in m or "SELECT" in m for m in mensajes)
