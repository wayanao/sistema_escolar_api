"""Valores de pago de un estudiante en un año (pedido del usuario, 2026-10-12).

Lo que se le cobra al estudiante, concepto por concepto, con el precio de su
curso y su valor personalizado, para el recuadro "Valores de pago" de la
sección de matricular. Solo lee. Todo usa dobles: sin base de datos.

La ruta de deudas no sirve para esto: solo trae los conceptos con deuda, y en
noviembre de 2026 la mensualidad de 2027 todavía no debe nada.
"""
import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute

from app.controllers import tipos_pagos_controller
from app.dependencies import get_current_active_admin
from app.routes import tipos_pagos as rutas_tipos_pagos
from app.services import cobros
from app.services.anio_lectivo import AnioLectivoInexistenteError

ID_2027 = 3
CURSO_2027 = 20


def _concepto(id_, nombre, tipo_cobro, valor_base, activo=True):
    return {
        "id": id_,
        "nombre": nombre,
        "valor": valor_base,
        "tipo_cobro": tipo_cobro,
        "activo": activo,
        "mes_inicial": 2,
        "mes_final": 11,
        "frecuencia_meses": 1,
        "dia_limite_mes": 5,
        "dias_gracia": 0,
        "mora_tipo": None,
        "mora_valor": 0,
        "anio": 2027,
    }


CONCEPTOS_2027 = [
    _concepto(12, "MENSUALIDAD", "mensual", 150_000),
    # Precio 0 en el curso: se cobra el valor base del concepto.
    _concepto(13, "MATRICULA", "anual", 300_000),
    # No se cobran: opcional, inactivo y sin precio en el curso.
    _concepto(14, "SALIDA PEDAGOGICA", "opcional", 50_000),
    _concepto(15, "UNIFORME", "unico", 90_000, activo=False),
    _concepto(16, "GRADO", "unico", 120_000),
    # Beca completa: valor personalizado 0.
    _concepto(17, "BIBLIOTECA", "unico", 40_000),
]
PRECIOS_CURSO = {12: 200_000, 13: 0, 14: 50_000, 15: 90_000, 17: 40_000}
VALORES_ESTUDIANTE = {12: 180_000, 17: 0}
MOTIVOS = {12: "Beca parcial", 17: "Hijo de docente"}


@pytest.fixture
def datos_2027(monkeypatch):
    llamadas = {"curso": [], "tipos": [], "motivos": []}

    def curso(_cursor, estudiante_id, **kwargs):
        llamadas["curso"].append((estudiante_id, kwargs))
        return (CURSO_2027,)

    def tipos(_cursor, **kwargs):
        llamadas["tipos"].append(kwargs)
        return [dict(concepto) for concepto in CONCEPTOS_2027]

    def motivos(_cursor, estudiante_id):
        llamadas["motivos"].append(estudiante_id)
        return dict(MOTIVOS)

    monkeypatch.setattr(cobros, "obtener_curso_estudiante", curso)
    monkeypatch.setattr(cobros, "obtener_tipos_pago", tipos)
    monkeypatch.setattr(
        cobros, "obtener_asignaciones_cobro_por_curso",
        lambda _c, curso_id: dict(PRECIOS_CURSO) if curso_id == CURSO_2027 else {},
    )
    monkeypatch.setattr(
        cobros, "obtener_valores_personalizados_estudiante",
        lambda _c, _e: dict(VALORES_ESTUDIANTE),
    )
    monkeypatch.setattr(cobros, "obtener_motivos_personalizados_estudiante", motivos)
    return llamadas


# ---------------------------------------------------------------------------
# 1. El servicio: qué conceptos y con qué valores.
# ---------------------------------------------------------------------------

def test_trae_lo_que_se_cobra_con_precio_del_curso_y_lo_que_paga(datos_2027):
    curso_id, conceptos = cobros.obtener_valores_pago_estudiante(
        object(), 7, anio_lectivo_id=ID_2027,
    )

    assert curso_id == CURSO_2027
    assert conceptos == [
        {
            "tipo_pago_id": 12,
            "nombre": "MENSUALIDAD",
            "tipo_cobro": "mensual",
            "precio_curso": 200_000.0,
            "valor_personalizado": 180_000.0,
            "motivo": "Beca parcial",
            "valor_a_pagar": 180_000.0,
        },
        {
            "tipo_pago_id": 13,
            "nombre": "MATRICULA",
            "tipo_cobro": "anual",
            "precio_curso": 300_000.0,
            "valor_personalizado": None,
            "motivo": None,
            "valor_a_pagar": 300_000.0,
        },
        {
            "tipo_pago_id": 17,
            "nombre": "BIBLIOTECA",
            "tipo_cobro": "unico",
            "precio_curso": 40_000.0,
            "valor_personalizado": 0.0,
            "motivo": "Hijo de docente",
            "valor_a_pagar": 0.0,
        },
    ]
    # Conceptos y curso son los del año pedido.
    assert datos_2027["curso"] == [(7, {"anio_lectivo_id": ID_2027})]
    assert datos_2027["tipos"] == [{"anio_lectivo_id": ID_2027}]


def test_sin_anio_usa_el_activo_como_el_resto_de_cobros(datos_2027):
    cobros.obtener_valores_pago_estudiante(object(), 7)

    assert datos_2027["curso"] == [(7, {})]
    assert datos_2027["tipos"] == [{}]


def test_coincide_con_lo_que_cobra_el_calculo_de_deudas(datos_2027):
    """Mismos conceptos y mismo valor que usa `_calcular_deudas`: lo que se
    ve en el recuadro es lo que se cobra."""
    _curso_id, conceptos = cobros.obtener_valores_pago_estudiante(
        object(), 7, anio_lectivo_id=ID_2027,
    )
    deudas = cobros._calcular_deudas(
        tipos_pago=CONCEPTOS_2027,
        asignaciones_curso=PRECIOS_CURSO,
        pagos_nombre={},
        pagos_descripcion={},
        valores_estudiante=VALORES_ESTUDIANTE,
    )["deudas"]

    assert [(c["tipo_pago_id"], c["valor_a_pagar"]) for c in conceptos] == [
        (d["concepto_id"], d["valor_unitario"]) for d in deudas
    ]


def test_sin_valores_personalizados_no_pide_motivos(datos_2027, monkeypatch):
    monkeypatch.setattr(
        cobros, "obtener_valores_personalizados_estudiante", lambda _c, _e: {},
    )

    _curso_id, conceptos = cobros.obtener_valores_pago_estudiante(
        object(), 7, anio_lectivo_id=ID_2027,
    )

    assert datos_2027["motivos"] == []
    assert all(c["valor_personalizado"] is None for c in conceptos)
    assert [c["valor_a_pagar"] for c in conceptos] == [200_000.0, 300_000.0, 40_000.0]


def test_sin_matricula_en_el_anio_avisa(datos_2027, monkeypatch):
    monkeypatch.setattr(cobros, "obtener_curso_estudiante", lambda _c, _e, **_k: None)

    with pytest.raises(ValueError, match="no tiene matrícula en el año lectivo seleccionado"):
        cobros.obtener_valores_pago_estudiante(object(), 7, anio_lectivo_id=ID_2027)


class CursorFalso:
    def __init__(self, una=(), todas=()):
        self.una = list(una)
        self.todas = list(todas)
        self.consultas = []

    def execute(self, sql, params=None):
        self.consultas.append((" ".join(str(sql).split()), params))

    def fetchone(self):
        return self.una.pop(0) if self.una else None

    def fetchall(self):
        return self.todas.pop(0) if self.todas else []

    def close(self):
        self.cerrado = True


def test_los_motivos_salen_de_los_valores_vigentes_del_estudiante():
    cursor = CursorFalso(una=[(1,)], todas=[[(12, "Beca parcial"), (17, None)]])

    motivos = cobros.obtener_motivos_personalizados_estudiante(cursor, 7)

    assert motivos == {12: "Beca parcial", 17: None}
    sql, params = cursor.consultas[-1]
    assert sql == (
        "SELECT tipo_pago_id, motivo FROM tipos_pagos_estudiantes "
        "WHERE estudiante_id = %s AND activo = TRUE"
    )
    assert params == (7,)


def test_sin_la_tabla_de_valores_no_hay_motivos():
    cursor = CursorFalso(una=[None])

    assert cobros.obtener_motivos_personalizados_estudiante(cursor, 7) == {}
    assert len(cursor.consultas) == 1


# ---------------------------------------------------------------------------
# 2. El controlador: valida el año y siempre cierra la conexión.
# ---------------------------------------------------------------------------

class ConexionFalsa:
    def __init__(self):
        self.cursor_falso = CursorFalso()
        self.cerrada = False

    def cursor(self):
        return self.cursor_falso

    def close(self):
        self.cerrada = True


def test_el_controlador_valida_el_anio_y_responde_los_conceptos(monkeypatch):
    conexion = ConexionFalsa()
    recibidos = {"anio": [], "valores": []}
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: conexion)
    monkeypatch.setattr(
        tipos_pagos_controller, "exigir_anio_lectivo",
        lambda _c, anio_id: recibidos["anio"].append(anio_id) or (anio_id, 2027, "preparacion"),
    )

    def valores(_cursor, estudiante_id, **kwargs):
        recibidos["valores"].append((estudiante_id, kwargs))
        return CURSO_2027, [{"tipo_pago_id": 12}]

    monkeypatch.setattr(tipos_pagos_controller, "obtener_valores_pago_estudiante", valores)

    respuesta = tipos_pagos_controller.listar_valores_pago_estudiante(7, anio_lectivo_id=ID_2027)

    assert respuesta == {
        "estudiante_id": 7,
        "anio_lectivo_id": ID_2027,
        "curso_id": CURSO_2027,
        "conceptos": [{"tipo_pago_id": 12}],
    }
    assert recibidos == {"anio": [ID_2027], "valores": [(7, {"anio_lectivo_id": ID_2027})]}
    assert conexion.cerrada is True
    assert conexion.cursor_falso.cerrado is True


def test_el_controlador_sin_anio_no_lo_valida_y_usa_el_activo(monkeypatch):
    conexion = ConexionFalsa()
    recibidos = []
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: conexion)
    monkeypatch.setattr(
        tipos_pagos_controller, "exigir_anio_lectivo",
        lambda *_a: pytest.fail("Sin año no se valida ninguno"),
    )
    monkeypatch.setattr(
        tipos_pagos_controller, "obtener_valores_pago_estudiante",
        lambda _c, estudiante_id, **kwargs: recibidos.append(kwargs) or (10, []),
    )

    respuesta = tipos_pagos_controller.listar_valores_pago_estudiante(7)

    assert recibidos == [{}]
    assert respuesta["anio_lectivo_id"] is None
    assert conexion.cerrada is True


def test_el_controlador_cierra_la_conexion_si_el_anio_no_existe(monkeypatch):
    conexion = ConexionFalsa()
    monkeypatch.setattr(tipos_pagos_controller, "get_connection", lambda: conexion)

    def no_existe(_cursor, _anio_id):
        raise AnioLectivoInexistenteError("El año lectivo seleccionado no existe.")

    monkeypatch.setattr(tipos_pagos_controller, "exigir_anio_lectivo", no_existe)

    with pytest.raises(AnioLectivoInexistenteError):
        tipos_pagos_controller.listar_valores_pago_estudiante(7, anio_lectivo_id=99)
    assert conexion.cerrada is True


# ---------------------------------------------------------------------------
# 3. La ruta: solo admin, año opcional y 404 con el mensaje del servicio.
# ---------------------------------------------------------------------------

def _ruta_valores_pago():
    return next(
        ruta
        for ruta in rutas_tipos_pagos.router.routes
        if isinstance(ruta, APIRoute)
        and ruta.path == "/estudiantes/{estudiante_id}/valores-pago"
    )


def test_la_ruta_es_un_get_solo_para_admin_con_el_anio_opcional():
    ruta = _ruta_valores_pago()

    assert ruta.methods == {"GET"}
    dependencias = [dep.dependency for dep in rutas_tipos_pagos.router.dependencies]
    assert get_current_active_admin in dependencias
    parametros = {parametro.name: parametro for parametro in ruta.dependant.query_params}
    assert set(parametros) == {"anio_lectivo_id"}
    assert parametros["anio_lectivo_id"].field_info.default is None


def test_la_ruta_pasa_el_anio_al_controlador(monkeypatch):
    recibidos = []
    monkeypatch.setattr(
        rutas_tipos_pagos, "listar_valores_pago_estudiante",
        lambda estudiante_id, **kwargs: recibidos.append((estudiante_id, kwargs)) or {},
    )

    rutas_tipos_pagos.get_valores_pago_estudiante(7, anio_lectivo_id=ID_2027)
    rutas_tipos_pagos.get_valores_pago_estudiante(7)

    assert recibidos == [(7, {"anio_lectivo_id": ID_2027}), (7, {"anio_lectivo_id": None})]


@pytest.mark.parametrize(
    "error",
    [
        AnioLectivoInexistenteError("El año lectivo seleccionado no existe."),
        ValueError("El estudiante no tiene matrícula en el año lectivo seleccionado."),
    ],
)
def test_la_ruta_responde_404_con_el_mensaje(monkeypatch, error):
    def falla(_estudiante_id, **_kwargs):
        raise error

    monkeypatch.setattr(rutas_tipos_pagos, "listar_valores_pago_estudiante", falla)

    with pytest.raises(HTTPException) as exc:
        rutas_tipos_pagos.get_valores_pago_estudiante(7, anio_lectivo_id=ID_2027)

    assert exc.value.status_code == 404
    assert exc.value.detail == str(error)
