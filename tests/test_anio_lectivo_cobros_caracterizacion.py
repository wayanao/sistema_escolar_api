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
   de 2026 en enero. En el paso 2.2 (cada año cuenta solo sus pagos): la
   matricula del año siguiente, el caso A y los meses vencidos de 2027. Esas
   tres pasan por una base de pagos simulada (`BaseDePagos`), porque el
   filtro por año vive en el SQL. En el paso 2.3 (pagar en otro año): los
   adelantos de diciembre. Ya no queda ninguna `test_error_actual_`.

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


ANIO_2026, ANIO_2027 = 1, 2  # ids de anios_lectivos


class BaseDePagos:
    """Pagos de varios años, como los devolveria PostgreSQL.

    Responde las consultas de `cobros.obtener_pagos_por_concepto_estudiantes`:
    suma por estudiante y concepto, y se queda solo con los pagos del año
    activo si la consulta trae ese filtro, igual que la base real. Cada pago
    es `(estudiante_id, tipo_pago, descripcion, monto, anio_lectivo_id)`;
    no hay adelantos (aplicaciones).
    """

    FILTRO_ANIO_ACTIVO = (
        "pagos.anio_lectivo_id = (select id from anios_lectivos where estado = 'activo')"
    )

    def __init__(self, pagos, anio_activo_id):
        self.pagos = list(pagos)
        self.anio_activo_id = anio_activo_id
        self.filas = []

    def execute(self, query, params=None):
        consulta = " ".join(str(query).lower().split())
        if "from information_schema.tables" in consulta:
            self.filas = [(1,)]
        elif "lower(coalesce(tipo_pago, ''))" in consulta:
            self.filas = self._sumar(consulta, params, campo=1)
        elif "lower(coalesce(descripcion, ''))" in consulta:
            self.filas = self._sumar(consulta, params, campo=2)
        elif "from pagos_aplicaciones pa" in consulta:
            self.filas = []
        else:
            raise AssertionError(f"Consulta no caracterizada: {consulta}")

    def _sumar(self, consulta, params, campo):
        estudiantes = set(params[0])
        solo_anio_activo = self.FILTRO_ANIO_ACTIVO in consulta
        sumas = {}
        for pago in self.pagos:
            estudiante_id, monto, anio_lectivo_id = pago[0], pago[3], pago[4]
            concepto = pago[campo]
            if estudiante_id not in estudiantes or concepto is None:
                continue
            if solo_anio_activo and anio_lectivo_id != self.anio_activo_id:
                continue
            clave = (estudiante_id, concepto.lower())
            sumas[clave] = sumas.get(clave, 0.0) + monto
        return [(est, concepto, total) for (est, concepto), total in sumas.items()]

    def fetchall(self):
        return list(self.filas)

    def fetchone(self):
        return self.filas[0] if self.filas else None


def _deudas_desde_la_base(hoy, base, tipos):
    """Deuda por concepto con lo pagado que devuelve la base simulada."""
    pagos_nombre, pagos_descripcion, pagos_aplicados = (
        cobros.obtener_pagos_por_concepto_estudiantes(base, (7,), hoy=hoy)
    )
    resultado = cobros.calcular_deudas_desde_contexto(
        tipos_pago=tipos,
        asignaciones_curso=PRECIOS_DEL_CURSO,
        pagos_nombre=pagos_nombre.get(7, {}),
        pagos_descripcion=pagos_descripcion.get(7, {}),
        pagos_aplicados=pagos_aplicados.get(7, {}),
        hoy=hoy,
    )
    por_concepto = {deuda["concepto"]: deuda for deuda in resultado["deudas"]}
    return por_concepto, resultado["total_deuda"]


def _todo_2026_pagado():
    """Pagos de 2026 como los guarda hoy el sistema: el concepto en la
    descripcion y el metodo en `tipo_pago`."""
    return [
        (7, "Efectivo", "Matricula", MATRICULA, ANIO_2026),
        (7, "Efectivo", "Mensualidad", 10 * MENSUALIDAD, ANIO_2026),
        (7, "Efectivo", "Salida pedagogica", ACTIVIDAD, ANIO_2026),
    ]


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


def test_caso_a_lo_pagado_en_2026_no_cubre_2027():
    """Invertida en el paso 2.2. Antes, en marzo de 2027 lo pagado en 2026
    cubria 2027 y no debia nada. Ahora, con 2027 activo, solo cuentan los
    pagos de 2027: debe la matricula 2027, febrero y marzo, y la salida
    pedagogica de 2027 (los conceptos se copian cada año, decision 17). Lo
    que quede de 2026 se muestra aparte en el paso 2.4."""
    con_2026_activo = BaseDePagos(_todo_2026_pagado(), anio_activo_id=ANIO_2026)
    con_2027_activo = BaseDePagos(_todo_2026_pagado(), anio_activo_id=ANIO_2027)

    _, total_2026 = _deudas_desde_la_base(
        datetime.date(2026, 12, 15), con_2026_activo, _conceptos_del_colegio(anio=2026),
    )
    deudas, total = _deudas_desde_la_base(
        datetime.date(2027, 3, 15), con_2027_activo, _conceptos_del_colegio(anio=2027),
    )

    # En diciembre de 2026, con 2026 activo, todo estaba pagado.
    assert total_2026 == 0
    assert deudas["Matricula"]["pagado"] == 0
    assert deudas["Matricula"]["deuda"] == MATRICULA
    assert deudas["Mensualidad"]["cuotas_vencidas"] == 2
    assert deudas["Mensualidad"]["deuda"] == 2 * MENSUALIDAD
    assert deudas["Salida pedagogica"]["deuda"] == ACTIVIDAD
    assert total == MATRICULA + 2 * MENSUALIDAD + ACTIVIDAD


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


def test_la_matricula_del_anio_siguiente_no_se_suma_a_la_del_anio_en_curso():
    """Invertida en el paso 2.2. Antes, la matricula 2027 pagada en noviembre
    de 2026 se sumaba a la de 2026. Ahora cada pago cuenta en su año."""
    pagos = [
        (7, "Efectivo", "Matricula", MATRICULA, ANIO_2026),
        (7, "Transferencia", "Matricula", MATRICULA, ANIO_2027),
    ]

    deudas_2026, _ = _deudas_desde_la_base(
        datetime.date(2026, 11, 20),
        BaseDePagos(pagos, anio_activo_id=ANIO_2026),
        [_concepto(1, "Matricula", "anual", MATRICULA, anio=2026)],
    )
    deudas_2027, _ = _deudas_desde_la_base(
        datetime.date(2027, 2, 10),
        BaseDePagos(pagos, anio_activo_id=ANIO_2027),
        [_concepto(1, "Matricula", "anual", MATRICULA, anio=2027)],
    )

    assert deudas_2026["Matricula"]["pagado"] == MATRICULA
    assert deudas_2026["Matricula"]["deuda"] == 0
    assert deudas_2027["Matricula"]["pagado"] == MATRICULA
    assert deudas_2027["Matricula"]["deuda"] == 0


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


def test_meses_vencidos_de_2027_no_se_cubren_con_pagos_de_2026(monkeypatch):
    """Pantalla "pagar meses vencidos". Invertida en el paso 2.2: antes, en
    marzo de 2027 los pagos de 2026 cubrian 2027 y la lista quedaba vacia.
    Ahora debe febrero y marzo de 2027."""
    monkeypatch.setattr(
        cobros,
        "obtener_conceptos_mensuales_estudiante",
        lambda _cursor, _estudiante_id: [_mensualidad_para_meses_vencidos(2027)],
    )
    base = BaseDePagos(_todo_2026_pagado(), anio_activo_id=ANIO_2027)

    opciones = cobros.obtener_cuotas_vencidas_estudiante(
        base, 7, hoy=datetime.date(2027, 3, 15),
    )

    assert [cuota["periodo"] for cuota in opciones[0]["cuotas"]] == [
        "2027-02-01",
        "2027-03-01",
    ]
    assert [cuota["saldo"] for cuota in opciones[0]["cuotas"]] == [MENSUALIDAD, MENSUALIDAD]


def test_en_diciembre_se_pueden_adelantar_meses_del_anio_siguiente():
    """Invertida en el paso 2.3. Antes, en diciembre no se podia adelantar
    nada: solo existian meses del año del calendario. Ahora el pago puede ir
    al año siguiente (en preparacion), y sus conceptos traen ese año. Los de
    2026 siguen sin ofrecer nada en diciembre: ya no les quedan meses. El
    camino completo, del controlador al registro, esta en
    tests/test_anio_lectivo_cobros_por_anio.py."""
    concepto_2026 = {"frecuencia_meses": 1, "mes_inicial": 2, "mes_final": 11, "anio": 2026}
    concepto_2027 = {**concepto_2026, "anio": 2027}

    en_octubre = pagos_controller._periodos_programados(concepto_2026, datetime.date(2026, 10, 10))
    en_diciembre_2026 = pagos_controller._periodos_programados(
        concepto_2026, datetime.date(2026, 12, 10),
    )
    en_diciembre_2027 = pagos_controller._periodos_programados(
        concepto_2027, datetime.date(2026, 12, 10),
    )

    assert en_octubre == [datetime.date(2026, 11, 1)]
    assert en_diciembre_2026 == []
    assert en_diciembre_2027 == [datetime.date(2027, mes, 1) for mes in range(2, 12)]
