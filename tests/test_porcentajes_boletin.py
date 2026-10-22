"""Porcentajes por tipo de nota, paso B2c: la definitiva del boletin (PB5).

Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`, "Avance del paso B2". Con los
porcentajes de la clase y el periodo activos, guardar el boletin calcula la
definitiva en el servidor y guarda esa, no la que manda la pantalla; la
lectura del boletin del profesor la agrega para que la pantalla muestre la que
se va a guardar. Sin porcentajes activos todo queda como hoy: lo fija
`test_porcentajes_planilla_caracterizacion.py` (paso B1).

El cursor responde segun un fragmento del SQL y, a cualquier otra consulta,
"nada", igual que en B1.
"""
from decimal import Decimal

import pytest

from app.controllers import boletin_controller
from app.repositories import porcentajes_planilla_repository as repositorio


ADMIN = {"id": 1, "rol": "admin"}


class CursorGuionado:
    """Responde segun un fragmento del SQL y guarda todo lo que se ejecuta."""

    def __init__(self, guion=()):
        self.guion = guion
        self.consultas = []
        self._uno = None
        self._todos = []

    def execute(self, sql, params=None):
        texto = " ".join(str(sql).split())
        self.consultas.append((texto, params))
        self._uno, self._todos = None, []
        for fragmento, uno, todos in self.guion:
            if fragmento in texto:
                self._uno, self._todos = uno, list(todos)
                break

    def fetchone(self):
        return self._uno

    def fetchall(self):
        return list(self._todos)

    def close(self):
        pass

    def leyo(self, fragmento):
        return [params for texto, params in self.consultas if fragmento in texto]


class ConexionFalsa:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.commits = 0

    def cursor(self, **_kwargs):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass

    def close(self):
        pass


@pytest.fixture
def boletin(monkeypatch):
    def instalar(guion):
        cursor = CursorGuionado(guion)
        conexion = ConexionFalsa(cursor)
        monkeypatch.setattr(boletin_controller, "get_connection", lambda: conexion)
        return cursor

    return instalar


GUARDIA = ("SELECT al.anio, al.estado", (2026, "activo"), [])
RESUELVE = ("AS asignacion_academica_id", (55,), [])
CABECERA = ("INSERT INTO boletin_cabecera", (901,), [])
LEER_PORCENTAJES = "SELECT tipo_nota, porcentaje FROM planilla_tipos_porcentaje"
LEER_TIPOS = "SELECT DISTINCT descripcion FROM notas_detalle"
LEER_CELDAS = "AS tipo_evaluacion FROM notas_detalle WHERE asignacion_id = %s"

TIPOS = [("Cognitivo",), ("Procedimental",), ("Actitudinal",)]
COMPLETOS = [("Cognitivo", 50), ("Procedimental", 30), ("Actitudinal", 20)]
INCOMPLETOS = [("Cognitivo", 50), ("Procedimental", 30)]


def _nivel(nivel):
    return ("SELECT c.nivel", (nivel,), [])


def _guion_guardar(porcentajes, celdas=(), *, nivel=None, tipos=TIPOS):
    return [
        GUARDIA, RESUELVE, _nivel(nivel), CABECERA,
        (LEER_PORCENTAJES, None, porcentajes),
        (LEER_TIPOS, None, tipos),
        (LEER_CELDAS, None, celdas),
    ]


class _Boletin:
    def __init__(self, definitiva, tipo_evaluacion="numerica"):
        self.estudiante_id = 8
        self.asignacion_id = 44
        self.periodo = 2
        self.definitiva = definitiva
        self.tipo_evaluacion = tipo_evaluacion
        self.detalles = []


def _definitiva_guardada(cursor):
    ((params),) = cursor.leyo("INSERT INTO boletin_cabecera")
    return params[3]


def _numericas(**notas):
    return [(tipo, nota, None, "numerica") for tipo, nota in notas.items()]


def _caritas(**codigos):
    return [(tipo, None, codigo, "desarrollo") for tipo, codigo in codigos.items()]


# --------------------------------------------------------------------------
# Guardar el boletin
# --------------------------------------------------------------------------

def test_sin_porcentajes_guarda_la_que_llega_y_solo_mira_si_hay(boletin):
    cursor = boletin(_guion_guardar([]))

    boletin_controller.guardar_boletin_controller(_Boletin(4.5), usuario=ADMIN)

    assert _definitiva_guardada(cursor) == 4.5
    assert cursor.leyo(LEER_PORCENTAJES) == [(55, 2)]
    assert cursor.leyo(LEER_TIPOS) == []
    assert cursor.leyo(LEER_CELDAS) == []


def test_con_porcentajes_incompletos_guarda_la_que_llega(boletin):
    cursor = boletin(_guion_guardar(INCOMPLETOS))

    boletin_controller.guardar_boletin_controller(_Boletin(4.5), usuario=ADMIN)

    assert _definitiva_guardada(cursor) == 4.5
    assert cursor.leyo(LEER_TIPOS) == [(55, 2)]
    assert cursor.leyo(LEER_CELDAS) == []


def test_con_porcentajes_activos_guarda_la_que_calcula_el_servidor(boletin):
    """Ejemplo de B0: 4.0 x 50 % + 3.0 x 30 % + 5.0 x 20 % = 3.90. La
    pantalla manda otra cifra (el promedio simple, 4.00) y no se usa."""
    celdas = _numericas(Cognitivo=Decimal("4.00"), Procedimental=Decimal("3.00"),
                        Actitudinal=Decimal("5.00"))
    cursor = boletin(_guion_guardar(COMPLETOS, celdas))

    boletin_controller.guardar_boletin_controller(_Boletin(4.0), usuario=ADMIN)

    assert _definitiva_guardada(cursor) == Decimal("3.90")
    assert cursor.leyo(LEER_CELDAS) == [(55, 2, 8)]


def test_la_celda_vacia_reparte_su_peso_y_la_columna_interna_no_cuenta(boletin):
    celdas = _numericas(Cognitivo=Decimal("4.00"), Procedimental=Decimal("3.00"),
                        Actitudinal=None)
    celdas.append(("mas_alto", Decimal("1.00"), None, "numerica"))
    cursor = boletin(_guion_guardar(COMPLETOS, celdas, tipos=TIPOS + [("mas_alto",)]))

    boletin_controller.guardar_boletin_controller(_Boletin(3.5), usuario=ADMIN)

    assert _definitiva_guardada(cursor) == Decimal("3.63")


@pytest.mark.parametrize("enviada", [0, None])
def test_sin_ninguna_nota_del_estudiante_guarda_la_que_llega(boletin, enviada):
    """Sin nada que ponderar el servidor no opina: queda lo de hoy (0 en
    numerica, vacia en caritas), y el puesto de ese estudiante no cambia."""
    cursor = boletin(_guion_guardar(COMPLETOS, []))

    boletin_controller.guardar_boletin_controller(_Boletin(enviada), usuario=ADMIN)

    assert _definitiva_guardada(cursor) == enviada


@pytest.mark.parametrize(
    "nivel,pedido",
    [("preescolar", "numerica"), (None, "numerica")],
    ids=["el-nivel-manda", "sin-nivel-mandan-las-celdas"],
)
def test_en_caritas_guarda_el_valor_del_promedio_ponderado(boletin, nivel, pedido):
    """50 % destacado (5) y 50 % logrado (4): 4.50. La pantalla no manda el
    tipo de evaluacion de la materia; si el curso no tiene nivel, decide lo
    mismo que el frontend: es de caritas si alguna celda lo es."""
    mitad = [("Cognitivo", 50), ("Procedimental", 50)]
    celdas = _caritas(Cognitivo="destacado", Procedimental="logrado")
    tipos = [("Cognitivo",), ("Procedimental",)]
    cursor = boletin(_guion_guardar(mitad, celdas, nivel=nivel, tipos=tipos))

    boletin_controller.guardar_boletin_controller(_Boletin(4.5, pedido), usuario=ADMIN)

    assert _definitiva_guardada(cursor) == Decimal("4.50")


def test_en_primaria_el_nivel_manda_aunque_haya_una_carita_vieja(boletin):
    celdas = _numericas(Cognitivo=Decimal("4.00"), Procedimental=Decimal("3.00"),
                        Actitudinal=Decimal("5.00"))
    celdas.append(("Otro", None, "logrado", "desarrollo"))
    cursor = boletin(_guion_guardar(COMPLETOS, celdas, nivel="primaria"))

    boletin_controller.guardar_boletin_controller(_Boletin(4.0), usuario=ADMIN)

    assert _definitiva_guardada(cursor) == Decimal("3.90")


# --------------------------------------------------------------------------
# La lectura del boletin del profesor
# --------------------------------------------------------------------------

def _celda(estudiante_id, nombre, tipo_nota, nota, tipo="numerica", valoracion=None):
    return {"estudiante_id": estudiante_id, "nombre": nombre, "apellido": "Ruiz",
            "tipo_nota": tipo_nota, "nota": nota, "tipo_evaluacion": tipo,
            "valoracion": valoracion}


CELDAS_DE_LA_CLASE = [
    _celda(3, "Ana", "Cognitivo", Decimal("4.00")),
    _celda(3, "Ana", "Procedimental", Decimal("3.00")),
    _celda(3, "Ana", "Actitudinal", Decimal("5.00")),
    _celda(4, "Leo", None, None),
]


def _guion_leer(porcentajes, celdas=CELDAS_DE_LA_CLASE, *, nivel=None, tipos=TIPOS):
    # Con un cursor de diccionarios, como el de esta lectura.
    return [
        RESUELVE,
        ("nd.descripcion as tipo_nota", None, celdas),
        ("bc.estudiante_id = ANY(%s)", None, []),
        (LEER_PORCENTAJES, None,
         [{"tipo_nota": t, "porcentaje": p} for t, p in porcentajes]),
        (LEER_TIPOS, None, [{"descripcion": t} for (t,) in tipos]),
        ("SELECT c.nivel", {"nivel": nivel}, []),
    ]


def test_la_lectura_sin_porcentajes_no_trae_definitiva_y_solo_mira_si_hay(boletin):
    cursor = boletin(_guion_leer([]))

    respuesta = boletin_controller.obtener_boletin_para_profesor_controller(44, 2)

    assert all("definitiva" not in estudiante for estudiante in respuesta)
    assert cursor.leyo(LEER_PORCENTAJES) == [(55, 2)]
    assert cursor.leyo(LEER_TIPOS) == []
    # Va despues de las dos lecturas de siempre.
    assert LEER_PORCENTAJES in cursor.consultas[-1][0]


def test_la_lectura_con_porcentajes_incompletos_no_trae_definitiva(boletin):
    cursor = boletin(_guion_leer(INCOMPLETOS))

    respuesta = boletin_controller.obtener_boletin_para_profesor_controller(44, 2)

    assert all("definitiva" not in estudiante for estudiante in respuesta)
    assert cursor.leyo("SELECT c.nivel") == []


def test_la_lectura_con_porcentajes_activos_trae_la_definitiva_del_servidor(boletin):
    cursor = boletin(_guion_leer(COMPLETOS))

    respuesta = boletin_controller.obtener_boletin_para_profesor_controller(44, 2)

    ana, leo = respuesta
    assert ana["definitiva"] == 3.9
    # Sin notas no hay nada que ponderar: la pantalla usa la suya, como hoy.
    assert "definitiva" not in leo
    # Las celdas son las que ya leyo; no se piden otra vez.
    assert cursor.leyo(LEER_CELDAS) == []
    assert cursor.leyo("SELECT c.nivel") == [(55,)]


def test_la_lectura_en_caritas_trae_el_valor_del_promedio_ponderado(boletin):
    mitad = [("Cognitivo", 50), ("Procedimental", 50)]
    celdas = [
        _celda(3, "Eva", "Cognitivo", None, "desarrollo", "destacado"),
        _celda(3, "Eva", "Procedimental", None, "desarrollo", "logrado"),
    ]
    boletin(_guion_leer(mitad, celdas, nivel="preescolar",
                        tipos=[("Cognitivo",), ("Procedimental",)]))

    (eva,) = boletin_controller.obtener_boletin_para_profesor_controller(44, 2)

    assert eva["definitiva"] == 4.5


# --------------------------------------------------------------------------
# El repositorio devuelve tuplas con cualquier cursor
# --------------------------------------------------------------------------

def test_el_repositorio_devuelve_tuplas_tambien_con_un_cursor_de_diccionarios():
    cursor = CursorGuionado([
        (LEER_PORCENTAJES, None, [{"tipo_nota": "Cognitivo", "porcentaje": 60}]),
        (LEER_TIPOS, None, [{"descripcion": "Cognitivo"}]),
        (LEER_CELDAS, None, [{"descripcion": "Cognitivo", "nota": Decimal("4.00"),
                              "valoracion": None, "tipo_evaluacion": "numerica"}]),
    ])

    assert repositorio.leer_porcentajes_de_planilla(cursor, 55, 2) == [("Cognitivo", 60)]
    assert repositorio.leer_tipos_de_planilla(cursor, 55, 2) == ["Cognitivo"]
    assert repositorio.leer_celdas_del_estudiante(cursor, 55, 2, 8) == [
        ("Cognitivo", Decimal("4.00"), None, "numerica"),
    ]
