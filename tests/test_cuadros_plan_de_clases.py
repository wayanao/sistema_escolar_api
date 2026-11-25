"""Nombres de los cuadros del plan de clase, paso 1: reglas, lectura y guardado.

Ver `docs/funcionalidades/NOMBRES_CUADROS_PLAN.md`. Las rutas pasan por la
aplicacion real (ASGI) con una base simulada que responde segun un fragmento
del SQL y cuenta conexiones, consultas, confirmaciones y reversiones. El
usuario de la sesion se dobla. La tabla la fija
`test_migracion_plan_de_clases_cuadros.py`.
"""
import asyncio
import json

import pytest

from app.controllers import cuadros_plan_de_clases_controller as controlador
from app.core import cuadros_plan_de_clases as cuadros
from app.db import session
from app.schemas.cuadros_plan_de_clases import CuadrosPlanUpdate
from app.schemas.plan_de_clases import PlanDeClasesCreate, PlanDeClasesResponse


PROFESOR = {"id": 7, "rol": "profesor"}
ADMIN = {"id": 1, "rol": "admin"}

LEER = "SELECT clave, nombre, ayuda FROM plan_de_clases_cuadros"
BLOQUEAR = "LOCK TABLE plan_de_clases_cuadros IN SHARE ROW EXCLUSIVE MODE"
BORRAR = "DELETE FROM plan_de_clases_cuadros"
INSERTAR = "INSERT INTO plan_de_clases_cuadros"


class Base:
    """Pool, conexiones y cursores simulados.

    `respuestas` son `(fragmento, fetchall)`: la primera cuyo fragmento
    aparezca en el SQL decide lo que devuelve. `falla_con` hace fallar la
    sentencia que contenga ese fragmento.
    """

    def __init__(self, respuestas=(), *, falla_con=None):
        self.conexiones = 0
        self.consultas = []
        self.commits = 0
        self.rollbacks = 0
        self.respuestas = list(respuestas)
        self.falla_con = falla_con

    def getconn(self):
        self.conexiones += 1
        return ConexionFalsa(self)

    def putconn(self, conexion, close=False):
        pass

    @property
    def textos(self):
        return [texto for texto, _ in self.consultas]


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
        self._todos = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params=None):
        texto = " ".join(str(sql).split())
        if texto == "PREPARACION":
            return
        self.base.consultas.append((texto, params))
        if self.base.falla_con and self.base.falla_con in texto:
            raise RuntimeError("falla simulada")
        self._todos = []
        for fragmento, todos in self.base.respuestas:
            if fragmento in texto:
                self._todos = list(todos)
                break

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

    app.dependency_overrides[get_current_user] = lambda: usuario
    try:
        asyncio.run(app(scope, receive, send))
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    return salida["status"], json.loads(salida["body"].decode() or "null")


LECTURA = "/plan-de-clases/cuadros"
GUARDADO = "/admin/plan-de-clases/cuadros"


def _cuadro(clave, nombre, ayuda=""):
    return {"clave": clave, "nombre": nombre, "ayuda": ayuda}


# ---------------------------------------------------------------------------
# Las claves
# ---------------------------------------------------------------------------


def test_son_los_siete_cuadros_de_texto_y_los_dos_archivos_del_formulario():
    assert cuadros.CUADROS_DE_TEXTO == (
        "unidad", "estandar", "tema", "proposito", "clase", "dba", "actividad_casa",
    )
    assert cuadros.CUADROS_DE_ARCHIVO == ("imagen1", "imagen2")
    assert cuadros.CLAVES == cuadros.CUADROS_DE_TEXTO + cuadros.CUADROS_DE_ARCHIVO


def test_cada_clave_es_un_campo_del_plan():
    """Las claves son los campos que ya guarda el plan, no nombres nuevos."""
    assert set(cuadros.CUADROS_DE_TEXTO) <= set(PlanDeClasesCreate.model_fields)
    assert set(cuadros.CUADROS_DE_ARCHIVO) <= set(PlanDeClasesResponse.model_fields)


def test_actividad_en_clase_queda_fuera():
    """`competencias` ya no se escribe en el formulario; conserva su nombre fijo."""
    assert "competencias" not in cuadros.CLAVES


# ---------------------------------------------------------------------------
# Las reglas
# ---------------------------------------------------------------------------


def test_una_lista_valida_no_tiene_motivo_para_rechazarla():
    assert cuadros.motivo_para_rechazar([]) is None
    assert cuadros.motivo_para_rechazar([
        ("proposito", "Objetivo", "Lo que se espera"),
        ("imagen1", "Guía de trabajo", ""),
    ]) is None


@pytest.mark.parametrize(
    "lista, motivo",
    [
        ([("competencias", "Actividad", "")], cuadros.CLAVE_DESCONOCIDA),
        ([("Unidad", "Eje", "")], cuadros.CLAVE_DESCONOCIDA),
        ([("tema", "Tema", ""), ("tema", "Asunto", "")], cuadros.CLAVE_REPETIDA),
        ([("tema", "", "")], cuadros.NOMBRE_VACIO),
        ([("tema", "x" * 61, "")], cuadros.NOMBRE_LARGO),
        ([("tema", "Tema", "x" * 151)], cuadros.AYUDA_LARGA),
        ([("imagen2", "Evidencia", "Sube una foto")], cuadros.AYUDA_EN_ARCHIVO),
    ],
)
def test_cada_regla_tiene_su_mensaje(lista, motivo):
    assert cuadros.motivo_para_rechazar(lista) == motivo


def test_los_largos_exactos_se_aceptan():
    assert cuadros.motivo_para_rechazar([("tema", "x" * 60, "y" * 150)]) is None


def test_el_orden_es_el_del_formulario_y_descarta_claves_viejas():
    filas = [
        ("imagen1", "Guía", ""),
        ("vieja", "Algo", ""),
        ("unidad", "Eje", "Ayuda"),
    ]

    assert cuadros.en_orden_del_formulario(filas) == [
        {"clave": "unidad", "nombre": "Eje", "ayuda": "Ayuda"},
        {"clave": "imagen1", "nombre": "Guía", "ayuda": ""},
    ]


def test_el_esquema_recorta_los_textos():
    datos = CuadrosPlanUpdate(cuadros=[_cuadro("  tema ", "  Asunto  ", "  ayuda ")])

    (cuadro,) = datos.cuadros
    assert (cuadro.clave, cuadro.nombre, cuadro.ayuda) == ("tema", "Asunto", "ayuda")


# ---------------------------------------------------------------------------
# Leer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("usuario", [PROFESOR, ADMIN])
def test_leer_devuelve_los_renombrados_en_el_orden_del_formulario(con_base, usuario):
    base = con_base(Base([(LEER, [("imagen1", "Guía", ""), ("proposito", "Objetivo", "Meta")])]))

    codigo, cuerpo = peticion(usuario, "GET", LECTURA)

    assert codigo == 200
    assert cuerpo == {"cuadros": [
        {"clave": "proposito", "nombre": "Objetivo", "ayuda": "Meta"},
        {"clave": "imagen1", "nombre": "Guía", "ayuda": ""},
    ]}
    assert base.conexiones == 1
    assert base.textos == [LEER]
    assert base.commits == 0


def test_sin_renombrados_la_lista_viene_vacia(con_base):
    con_base(Base())

    assert peticion(PROFESOR, "GET", LECTURA) == (200, {"cuadros": []})


def test_la_lectura_no_la_atrapa_la_ruta_del_historial_del_plan(con_base):
    """`GET /plan-de-clases/{asignacion_id}` leeria "cuadros" como numero (422)."""
    con_base(Base())

    assert peticion(PROFESOR, "GET", LECTURA) == (200, {"cuadros": []})
    assert peticion(PROFESOR, "GET", "/plan-de-clases/no-es-numero")[0] == 422


# ---------------------------------------------------------------------------
# Guardar
# ---------------------------------------------------------------------------


def test_el_profesor_no_puede_guardar_y_no_se_abre_la_base(con_base):
    base = con_base(Base())

    codigo, _ = peticion(PROFESOR, "PUT", GUARDADO, {"cuadros": []})

    assert codigo == 403
    assert base.conexiones == 0


def test_guardar_reemplaza_todo_en_una_sola_transaccion(con_base):
    base = con_base(Base())

    codigo, cuerpo = peticion(ADMIN, "PUT", GUARDADO, {"cuadros": [
        _cuadro("imagen1", "  Guía de trabajo "),
        _cuadro("proposito", "Objetivo", " Lo que se espera "),
    ]})

    assert codigo == 200
    assert cuerpo == {"cuadros": [
        {"clave": "proposito", "nombre": "Objetivo", "ayuda": "Lo que se espera"},
        {"clave": "imagen1", "nombre": "Guía de trabajo", "ayuda": ""},
    ]}
    assert base.conexiones == 1
    assert base.textos[:2] == [BLOQUEAR, BORRAR]
    (insertar_texto, parametros) = base.consultas[2]
    assert insertar_texto.startswith(INSERTAR)
    assert insertar_texto.endswith("VALUES (%s, %s, %s, %s), (%s, %s, %s, %s)")
    # Lo que se guarda va recortado, y quien guarda es el admin de la sesion.
    assert parametros == [
        "imagen1", "Guía de trabajo", "", ADMIN["id"],
        "proposito", "Objetivo", "Lo que se espera", ADMIN["id"],
    ]
    assert len(base.consultas) == 3
    # El rollback es la limpieza de siempre al devolver la conexion al pool.
    assert (base.commits, base.rollbacks) == (1, 1)


def test_volver_a_los_originales_borra_sin_insertar(con_base):
    base = con_base(Base())

    assert peticion(ADMIN, "PUT", GUARDADO, {"cuadros": []}) == (200, {"cuadros": []})
    assert base.textos == [BLOQUEAR, BORRAR]
    assert base.commits == 1


@pytest.mark.parametrize(
    "lista, mensaje",
    [
        ([_cuadro("competencias", "Actividad")], cuadros.CLAVE_DESCONOCIDA),
        ([_cuadro("tema", "Tema"), _cuadro("tema", "Asunto")], cuadros.CLAVE_REPETIDA),
        ([_cuadro("tema", "   ")], cuadros.NOMBRE_VACIO),
        ([_cuadro("tema", "x" * 61)], cuadros.NOMBRE_LARGO),
        ([_cuadro("tema", "Tema", "x" * 151)], cuadros.AYUDA_LARGA),
        ([_cuadro("imagen1", "Guía", "Sube una foto")], cuadros.AYUDA_EN_ARCHIVO),
    ],
)
def test_una_lista_invalida_es_422_con_su_mensaje_sin_abrir_la_base(con_base, lista, mensaje):
    base = con_base(Base())

    codigo, cuerpo = peticion(ADMIN, "PUT", GUARDADO, {"cuadros": lista})

    assert codigo == 422
    assert cuerpo == {"detail": mensaje}
    assert base.conexiones == 0


def test_mas_cuadros_que_claves_lo_rechaza_el_esquema(con_base):
    base = con_base(Base())
    lista = [_cuadro(clave, "Nombre") for clave in cuadros.CLAVES] + [_cuadro("tema", "Otra")]

    codigo, _ = peticion(ADMIN, "PUT", GUARDADO, {"cuadros": lista})

    assert codigo == 422
    assert base.conexiones == 0


def test_si_falla_la_escritura_no_queda_nada_a_medias(con_base):
    """Borrar e insertar van juntos: si el INSERT falla, el DELETE se revierte."""
    base = con_base(Base(falla_con=INSERTAR))
    datos = CuadrosPlanUpdate(cuadros=[_cuadro("tema", "Asunto")])

    with pytest.raises(RuntimeError):
        controlador.guardar_cuadros_controller(datos, usuario=ADMIN)

    assert base.textos[:2] == [BLOQUEAR, BORRAR]
    # Uno revierte la escritura y el otro es la limpieza al devolver la conexion.
    assert (base.commits, base.rollbacks) == (0, 2)
