"""Caracterizacion de cobros antes de la funcionalidad "Año lectivo".

Fase 0 de `docs/funcionalidades/ANIO_LECTIVO.md`. Dos grupos:

1. Dentro del año en curso: fija como calcula hoy la deuda cada tipo de
   concepto. La fase 2 debe dejar estas pruebas iguales.
2. Al cambiar de año: documenta el error actual. Los pagos de todos los años
   se suman juntos (`obtener_pagos_por_concepto_estudiantes`) y solo existen
   las cuotas del año calendario de `hoy` (`listar_cuotas_vencidas`). Las
   pruebas con prefijo `test_error_actual_` afirman los valores INCORRECTOS
   de hoy. La fase 2 las invierte paso a paso para exigir el resultado
   correcto; no se "arreglan" antes. Ya invertidas en el paso 2.1 (las
   cuotas se cuentan en el año del concepto): el caso B y los meses vencidos
   de 2026 en enero.

Los montos son los del diagnostico del documento (matricula de $300.000,
mensualidad de $200.000 de febrero a noviembre con dia limite 5).
"""
import datetime

from app.controllers import pagos_controller
from app.services import cobros


MATRICULA = 300_000.0
MENSUALIDAD = 200_000.0
ACTIVIDAD = 50_000.0
SEGURO = 20_000.0

PRECIOS_DEL_CURSO = {1: MATRICULA, 2: MENSUALIDAD, 3: ACTIVIDAD, 4: SEGURO}


class FakeCursor:
    def __init__(self, fetches=None):
        self.fetches = list(fetches or [])
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        return self.fetches.pop(0)


def _concepto(id_, nombre, tipo_cobro, valor, **extra):
    concepto = {
        "id": id_,
        "nombre": nombre,
        "valor": valor,
        "tipo_cobro": tipo_cobro,
        "activo": True,
        "mes_inicial": None,
        "mes_final": 12,
        "frecuencia_meses": 1,
        "dia_limite_mes": None,
        "dias_gracia": 0,
        "mora_tipo": None,
        "mora_valor": 0,
    }
    concepto.update(extra)
    return concepto


def _conceptos_del_colegio(anio=None):
    """Un concepto de cada tipo, configurado como un colegio de calendario A.

    Con `anio`, cada concepto trae su año lectivo, como los devuelve
    `cobros.obtener_tipos_pago` desde la fase 2. Sin el, la forma de antes.
    """
    conceptos = [
        _concepto(1, "Matricula", "anual", MATRICULA),
        _concepto(
            2, "Mensualidad", "mensual", MENSUALIDAD,
            mes_inicial=2, mes_final=11, dia_limite_mes=5,
        ),
        _concepto(3, "Salida pedagogica", "unico", ACTIVIDAD),
        _concepto(4, "Seguro", "opcional", SEGURO),
    ]
    if anio is not None:
        for concepto in conceptos:
            concepto["anio"] = anio
    return conceptos


def _deudas(hoy, pagos=None, tipos=None, precios=None):
    """Deuda por concepto con la misma funcion que usan estado de cuenta y cartera."""
    resultado = cobros.calcular_deudas_desde_contexto(
        tipos_pago=_conceptos_del_colegio() if tipos is None else tipos,
        asignaciones_curso=PRECIOS_DEL_CURSO if precios is None else precios,
        pagos_nombre=pagos or {},
        pagos_descripcion={},
        pagos_aplicados={},
        hoy=hoy,
    )
    por_concepto = {deuda["concepto"]: deuda for deuda in resultado["deudas"]}
    return por_concepto, resultado["total_deuda"]


def _mensualidad_para_meses_vencidos(anio=None):
    """Forma que devuelve `obtener_conceptos_mensuales_estudiante`.

    Con `anio`, el concepto trae su año lectivo, como desde la fase 2.
    """
    concepto = {
        "id": 2,
        "nombre": "Mensualidad",
        "valor_unitario": MENSUALIDAD,
        "valor_origen": "curso",
        "mes_inicial": 2,
        "mes_final": 11,
        "frecuencia_meses": 1,
        "dia_limite_mes": 5,
        "dias_gracia": 0,
    }
    if anio is not None:
        concepto["anio"] = anio
    return concepto


def _meses_vencidos(monkeypatch, hoy, pagado_mensualidad, anio=None):
    """Opciones de "pagar meses vencidos" con pagos legacy (sin aplicaciones)."""
    monkeypatch.setattr(
        cobros,
        "obtener_conceptos_mensuales_estudiante",
        lambda _cursor, _estudiante_id: [_mensualidad_para_meses_vencidos(anio)],
    )
    monkeypatch.setattr(
        cobros,
        "obtener_pagos_por_concepto",
        lambda _cursor, _estudiante_id, hoy=None: (
            {"mensualidad": pagado_mensualidad}, {}, {},
        ),
    )
    return cobros.obtener_cuotas_vencidas_estudiante(FakeCursor(fetches=[[]]), 7, hoy=hoy)


# ---------------------------------------------------------------------------
# 1. Dentro del año en curso: la fase 2 debe dejar esto igual.
# ---------------------------------------------------------------------------


def test_deuda_sin_pagos_por_tipo_de_concepto():
    deudas, total = _deudas(datetime.date(2026, 9, 29))

    assert deudas["Matricula"]["deuda"] == MATRICULA
    assert deudas["Matricula"]["cuotas_vencidas"] == 0
    # Febrero a septiembre: el 5 de septiembre ya paso.
    assert deudas["Mensualidad"]["cuotas_vencidas"] == 8
    assert deudas["Mensualidad"]["deuda"] == 8 * MENSUALIDAD
    assert deudas["Salida pedagogica"]["deuda"] == ACTIVIDAD
    assert "Seguro" not in deudas
    assert total == MATRICULA + 8 * MENSUALIDAD + ACTIVIDAD


def test_pagos_se_restan_por_concepto():
    deudas, total = _deudas(
        datetime.date(2026, 9, 29),
        pagos={"matricula": MATRICULA, "mensualidad": 5 * MENSUALIDAD},
    )

    assert deudas["Matricula"]["deuda"] == 0
    assert deudas["Mensualidad"]["pagado"] == 5 * MENSUALIDAD
    assert deudas["Mensualidad"]["deuda"] == 3 * MENSUALIDAD
    assert total == 3 * MENSUALIDAD + ACTIVIDAD


def test_mensualidad_de_diciembre_cuenta_todo_el_anio_hasta_noviembre():
    deudas, _ = _deudas(datetime.date(2026, 12, 15))

    assert deudas["Mensualidad"]["cuotas_vencidas"] == 10
    assert deudas["Mensualidad"]["deuda"] == 10 * MENSUALIDAD


def test_concepto_sin_precio_en_el_curso_no_genera_deuda():
    precios = {1: MATRICULA, 2: MENSUALIDAD}

    deudas, _ = _deudas(datetime.date(2026, 9, 29), precios=precios)

    assert "Salida pedagogica" not in deudas


def test_concepto_inactivo_no_genera_deuda_aunque_nunca_se_haya_pagado():
    """Hallazgo fuera de alcance del documento: desactivar oculta la deuda.

    Choca con la decision 7 ("si el estudiante debe, la deuda le queda hasta
    que la pague"). Se fija aqui para que un cambio sea siempre deliberado.
    """
    tipos = _conceptos_del_colegio()
    tipos[2]["activo"] = False

    deudas, total = _deudas(datetime.date(2026, 9, 29), tipos=tipos)

    assert "Salida pedagogica" not in deudas
    assert total == MATRICULA + 8 * MENSUALIDAD


# ---------------------------------------------------------------------------
# 2. Al cambiar de año: ERROR ACTUAL. La fase 2 invierte estas pruebas.
# ---------------------------------------------------------------------------


def test_error_actual_caso_a_lo_pagado_en_2026_cubre_2027():
    """Correcto: en marzo de 2027 debe la matricula 2027 + febrero y marzo."""
    pagado_todo_2026 = {
        "matricula": MATRICULA,
        "mensualidad": 10 * MENSUALIDAD,
        "salida pedagogica": ACTIVIDAD,
    }

    deudas, total = _deudas(datetime.date(2027, 3, 15), pagos=pagado_todo_2026)

    assert deudas["Matricula"]["deuda"] == 0
    assert deudas["Mensualidad"]["cuotas_vencidas"] == 2
    assert deudas["Mensualidad"]["deuda"] == 0
    assert total == 0


def test_caso_b_la_deuda_de_2026_sigue_en_enero_mientras_2026_es_el_activo():
    """Invertida en el paso 2.1. Antes, el 15 de enero de 2027 la deuda de
    octubre y noviembre desaparecia: solo existian cuotas de 2027. Ahora cada
    concepto trae su año y sus cuotas se cuentan en el."""
    debe_octubre_y_noviembre = {
        "matricula": MATRICULA,
        "mensualidad": 8 * MENSUALIDAD,
        "salida pedagogica": ACTIVIDAD,
    }
    conceptos_2026 = _conceptos_del_colegio(anio=2026)

    deudas_diciembre, total_diciembre = _deudas(
        datetime.date(2026, 12, 15), pagos=debe_octubre_y_noviembre, tipos=conceptos_2026,
    )
    deudas_enero, total_enero = _deudas(
        datetime.date(2027, 1, 15), pagos=debe_octubre_y_noviembre, tipos=conceptos_2026,
    )

    assert deudas_diciembre["Mensualidad"]["deuda"] == 2 * MENSUALIDAD
    assert total_diciembre == 2 * MENSUALIDAD
    assert deudas_enero["Mensualidad"]["cuotas_vencidas"] == 10
    assert deudas_enero["Mensualidad"]["deuda"] == 2 * MENSUALIDAD
    assert total_enero == 2 * MENSUALIDAD


def test_error_actual_matricula_del_anio_siguiente_se_suma_a_la_del_anio_en_curso():
    """Correcto: la segunda matricula pertenece a 2027 y no toca la de 2026."""
    tipos = [_concepto(1, "Matricula", "anual", MATRICULA)]

    deudas, _ = _deudas(
        datetime.date(2026, 11, 20),
        pagos={"matricula": 2 * MATRICULA},
        tipos=tipos,
        precios={1: MATRICULA},
    )

    assert deudas["Matricula"]["pagado"] == 2 * MATRICULA
    assert deudas["Matricula"]["deuda"] == 0


def test_meses_vencidos_de_2026_siguen_en_enero_mientras_2026_es_el_activo(monkeypatch):
    """Pantalla "pagar meses vencidos". Invertida en el paso 2.1: antes, en
    enero la lista quedaba vacia; ahora siguen octubre y noviembre de 2026."""
    en_diciembre = _meses_vencidos(
        monkeypatch, datetime.date(2026, 12, 15), pagado_mensualidad=8 * MENSUALIDAD,
        anio=2026,
    )
    en_enero = _meses_vencidos(
        monkeypatch, datetime.date(2027, 1, 15), pagado_mensualidad=8 * MENSUALIDAD,
        anio=2026,
    )

    for opciones in (en_diciembre, en_enero):
        assert [cuota["periodo"] for cuota in opciones[0]["cuotas"]] == [
            "2026-10-01",
            "2026-11-01",
        ]


def test_error_actual_meses_vencidos_de_2027_se_cubren_con_pagos_de_2026(monkeypatch):
    """Correcto: en marzo de 2027 debe febrero y marzo de 2027."""
    opciones = _meses_vencidos(
        monkeypatch, datetime.date(2027, 3, 15), pagado_mensualidad=10 * MENSUALIDAD,
    )

    assert opciones == []


def test_error_actual_adelantos_de_diciembre_no_ofrecen_meses_del_anio_siguiente():
    """Correcto: en diciembre se pueden adelantar meses de 2027."""
    concepto = {"frecuencia_meses": 1, "mes_inicial": 2, "mes_final": 11}

    en_octubre = pagos_controller._periodos_programados(concepto, datetime.date(2026, 10, 10))
    en_diciembre = pagos_controller._periodos_programados(concepto, datetime.date(2026, 12, 10))

    assert en_octubre == [datetime.date(2026, 11, 1)]
    assert en_diciembre == []
