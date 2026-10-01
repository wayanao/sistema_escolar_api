"""Fase 2 del año lectivo: los cobros se cuentan en el año de cada concepto.

Ver el plan por pasos de la fase 2 en docs/funcionalidades/ANIO_LECTIVO.md.
Paso 2.1: las cuotas se cuentan en el año lectivo del concepto, no en el año
del calendario. Asi, el 1 de enero las cuotas del año que sigue activo no
desaparecen.

Tres grupos:

1. Hoy no cambia nada. Se compara el codigo nuevo con una copia literal del
   anterior (commit 47c61c2) en miles de combinaciones de fecha y
   configuracion: con el año del calendario, el resultado es identico.
2. Lo nuevo del paso 2.1: un año que ya termino, uno que no ha empezado, los
   dias de gracia que pasan de diciembre, y los conceptos que traen su año.
3. Paso 2.2: cada año cuenta solo sus pagos, y el curso que fija los precios
   sale de la matricula del año. El año va como subconsulta, sin parametros
   ni consultas nuevas.

Los casos A y B del diagnostico estan en
tests/test_anio_lectivo_cobros_caracterizacion.py.
"""
import datetime
from calendar import monthrange
from datetime import date, timedelta
from itertools import product

from app.controllers import estado_cuenta_controller, pagos_controller
from app.repositories import reportes_repository
from app.services import cartera, cobros


# ---------------------------------------------------------------------------
# Copias literales del codigo anterior al paso 2.1, solo para comparar.
# ---------------------------------------------------------------------------


def _listar_cuotas_vencidas_anterior(
    hoy, *, mes_inicial=None, mes_final=12, frecuencia_meses=1,
    dia_limite_mes=None, dias_gracia=0, max_cuotas=10,
):
    frecuencia = max(1, int(frecuencia_meses or 1))
    gracia = max(0, int(dias_gracia or 0))
    mes_inicio = int(mes_inicial) if mes_inicial else hoy.month
    if not (1 <= mes_inicio <= 12):
        mes_inicio = hoy.month
    mes_fin = int(mes_final) if mes_final is not None else 12
    if not (1 <= mes_fin <= 12):
        mes_fin = 12

    cuotas = []
    for i in range(max(1, int(max_cuotas or 1))):
        mes_cuota = mes_inicio + i * frecuencia
        if mes_cuota < 1 or mes_cuota > mes_fin:
            break

        ultimo_dia = monthrange(hoy.year, mes_cuota)[1]
        dia = int(dia_limite_mes) if dia_limite_mes else ultimo_dia
        dia = min(dia, ultimo_dia)
        fecha_vencimiento = date(hoy.year, mes_cuota, dia)
        fecha_efectiva = fecha_vencimiento + timedelta(days=gracia)
        if hoy < fecha_efectiva:
            break

        cuotas.append(cartera.CuotaVencida(
            periodo=date(hoy.year, mes_cuota, 1),
            fecha_vencimiento=fecha_vencimiento,
            fecha_efectiva=fecha_efectiva,
        ))

    return cuotas


def _calcular_cuotas_vencidas_anterior(
    hoy, *, mes_inicial=None, mes_final=12, frecuencia_meses=1,
    dia_limite_mes=None, dias_gracia=0, max_cuotas=10,
):
    cuotas_vencidas = _listar_cuotas_vencidas_anterior(
        hoy,
        mes_inicial=mes_inicial,
        mes_final=mes_final,
        frecuencia_meses=frecuencia_meses,
        dia_limite_mes=dia_limite_mes,
        dias_gracia=dias_gracia,
        max_cuotas=max_cuotas,
    )

    frecuencia = max(1, int(frecuencia_meses or 1))
    mes_inicio = int(mes_inicial) if mes_inicial else hoy.month
    if not (1 <= mes_inicio <= 12):
        mes_inicio = hoy.month
    mes_fin = int(mes_final) if mes_final is not None else 12
    if not (1 <= mes_fin <= 12):
        mes_fin = 12
    siguiente_mes = mes_inicio + len(cuotas_vencidas) * frecuencia
    proxima_fecha = None
    if 1 <= siguiente_mes <= mes_fin:
        ultimo_dia = monthrange(hoy.year, siguiente_mes)[1]
        dia = int(dia_limite_mes) if dia_limite_mes else ultimo_dia
        proxima_fecha = date(hoy.year, siguiente_mes, min(dia, ultimo_dia))

    return cartera.ResultadoCuotas(
        cuotas_vencidas=len(cuotas_vencidas),
        proxima_fecha=proxima_fecha,
        proxima_cuota_pendiente=proxima_fecha is not None,
    )


def _periodos_programados_anterior(concepto, hoy):
    frecuencia = max(1, int(concepto.get("frecuencia_meses") or 1))
    mes_inicial = concepto.get("mes_inicial")
    mes_final = int(concepto.get("mes_final") or 12)
    if not 1 <= mes_final <= 12:
        mes_final = 12
    periodos = []

    for mes in range(hoy.month + 1, mes_final + 1):
        if mes_inicial:
            inicio = int(mes_inicial)
            if mes < inicio or (mes - inicio) % frecuencia != 0:
                continue
        elif (mes - (hoy.month + 1)) % frecuencia != 0:
            continue
        periodos.append(datetime.date(hoy.year, mes, 1))

    return periodos


# Dias de 2026 repartidos en todos los meses: inicio, mitad y final.
DIAS_DE_2026 = [
    date(2026, mes, dia)
    for mes in range(1, 13)
    for dia in (1, 15, monthrange(2026, mes)[1])
]


# ---------------------------------------------------------------------------
# 1. Hoy no cambia nada.
# ---------------------------------------------------------------------------


def test_cuotas_del_anio_del_calendario_identicas_a_las_de_antes():
    combinaciones = 0
    for hoy, mes_inicial, mes_final, frecuencia, dia_limite, gracia in product(
        DIAS_DE_2026,
        (None, 1, 2, 7, 12, 13),
        (6, 11, 12, 13),
        (1, 2),
        (None, 5, 31),
        (0, 10),
    ):
        configuracion = {
            "mes_inicial": mes_inicial,
            "mes_final": mes_final,
            "frecuencia_meses": frecuencia,
            "dia_limite_mes": dia_limite,
            "dias_gracia": gracia,
            "max_cuotas": 12,
        }
        anterior = _listar_cuotas_vencidas_anterior(hoy, **configuracion)
        assert cartera.listar_cuotas_vencidas(hoy, **configuracion) == anterior
        assert cartera.listar_cuotas_vencidas(hoy, anio=hoy.year, **configuracion) == anterior

        anterior_resumen = _calcular_cuotas_vencidas_anterior(hoy, **configuracion)
        assert cartera.calcular_cuotas_vencidas(hoy, **configuracion) == anterior_resumen
        assert (
            cartera.calcular_cuotas_vencidas(hoy, anio=hoy.year, **configuracion)
            == anterior_resumen
        )
        combinaciones += 1

    # Que la comparacion de verdad recorrio el espacio previsto.
    assert combinaciones == len(DIAS_DE_2026) * 6 * 4 * 2 * 3 * 2


def test_adelantos_del_anio_del_calendario_identicos_a_los_de_antes():
    combinaciones = 0
    for hoy, mes_inicial, mes_final, frecuencia in product(
        DIAS_DE_2026,
        (None, 1, 2, 7, 12),
        (0, 6, 11, 12, 13),
        (1, 2, 3),
    ):
        concepto = {
            "mes_inicial": mes_inicial,
            "mes_final": mes_final,
            "frecuencia_meses": frecuencia,
        }
        anterior = _periodos_programados_anterior(concepto, hoy)
        assert pagos_controller._periodos_programados(concepto, hoy) == anterior
        assert (
            pagos_controller._periodos_programados({**concepto, "anio": hoy.year}, hoy)
            == anterior
        )
        combinaciones += 1

    assert combinaciones == len(DIAS_DE_2026) * 5 * 5 * 3


# ---------------------------------------------------------------------------
# 2. Lo nuevo: las cuotas son del año del concepto.
# ---------------------------------------------------------------------------

# La mensualidad de tenant_2005: julio a noviembre, con dia limite 5.
MENSUALIDAD_2026 = {"mes_inicial": 7, "mes_final": 11, "dia_limite_mes": 5, "max_cuotas": 12}


def test_un_anio_que_ya_termino_tiene_todas_sus_cuotas_vencidas():
    cuotas = cartera.listar_cuotas_vencidas(date(2027, 1, 15), anio=2026, **MENSUALIDAD_2026)

    assert [c.periodo for c in cuotas] == [date(2026, mes, 1) for mes in range(7, 12)]
    assert [c.fecha_vencimiento for c in cuotas] == [date(2026, mes, 5) for mes in range(7, 12)]


def test_un_anio_que_no_ha_empezado_no_tiene_cuotas_vencidas():
    """La mensualidad 2027 vista en noviembre de 2026: nada vencido aun."""
    hoy = date(2026, 11, 20)

    assert cartera.listar_cuotas_vencidas(
        hoy, anio=2027, mes_inicial=2, mes_final=11, dia_limite_mes=5,
    ) == []
    resumen = cartera.calcular_cuotas_vencidas(
        hoy, anio=2027, mes_inicial=2, mes_final=11, dia_limite_mes=5,
    )
    assert resumen.cuotas_vencidas == 0
    assert resumen.proxima_fecha == date(2027, 2, 5)


def test_los_dias_de_gracia_que_pasan_de_diciembre_se_respetan():
    """Cuota de diciembre con limite el 20 y 20 dias de gracia: vence el 9 de enero."""
    diciembre = {"mes_inicial": 12, "mes_final": 12, "dia_limite_mes": 20, "dias_gracia": 20}

    assert cartera.listar_cuotas_vencidas(date(2027, 1, 5), anio=2026, **diciembre) == []
    vencidas = cartera.listar_cuotas_vencidas(date(2027, 1, 9), anio=2026, **diciembre)
    assert [c.periodo for c in vencidas] == [date(2026, 12, 1)]


def test_sin_mes_inicial_un_anio_que_termino_cobra_diciembre():
    """Sin `mes_inicial` se cobra solo "el mes actual"; de un año que ya
    termino, ese mes es diciembre."""
    cuotas = cartera.listar_cuotas_vencidas(
        date(2027, 3, 10), anio=2026, mes_inicial=None, mes_final=12, dia_limite_mes=5,
    )

    assert [c.periodo for c in cuotas] == [date(2026, 12, 1)]
    assert cartera.listar_cuotas_vencidas(
        date(2026, 11, 20), anio=2027, mes_inicial=None, mes_final=12, dia_limite_mes=5,
    ) == []


def test_la_deuda_de_un_concepto_se_cuenta_en_su_anio():
    deuda = cartera.calcular_deuda_concepto(
        valor_unitario=200_000,
        tipo_cobro="mensual",
        pagado=600_000,
        hoy=date(2027, 1, 15),
        anio=2026,
        mes_inicial=7,
        mes_final=11,
        dia_limite_mes=5,
        max_cuotas=12,
    )

    assert deuda["cuotas_vencidas"] == 5
    assert deuda["deuda"] == 400_000


class CursorConceptos:
    """Responde la consulta de columnas y la de conceptos; anota cada SQL."""

    def __init__(self, columnas, filas):
        self.columnas = list(columnas)
        self.filas = list(filas)
        self.consultas = []
        self._resultado = []

    def execute(self, query, params=None):
        normalizada = " ".join(str(query).split())
        self.consultas.append(normalizada)
        if "information_schema.columns" in normalizada:
            self._resultado = [(columna,) for columna in self.columnas]
        else:
            self._resultado = list(self.filas)

    def fetchall(self):
        return list(self._resultado)


COLUMNAS_TIPOS_PAGO = [
    "id", "nombre", "valor", "tipo_cobro", "activo", "mes_inicial", "mes_final",
    "frecuencia_meses", "dia_limite_mes", "dias_gracia", "mora_tipo", "mora_valor",
    "anio_lectivo_id",
]


def test_los_conceptos_son_los_del_anio_activo_y_traen_su_anio():
    cursor = CursorConceptos(
        COLUMNAS_TIPOS_PAGO,
        [(2, "MENSUALIDAD", 200_000, "mensual", True, 7, 11, 1, 5, 0, None, 0, 2026)],
    )

    tipos = cobros.obtener_tipos_pago(cursor)

    # Las mismas dos consultas de siempre: el año no cuesta una ida extra.
    assert len(cursor.consultas) == 2
    consulta = cursor.consultas[1]
    assert "FROM tipos_de_pagos tp JOIN anios_lectivos al ON al.id = tp.anio_lectivo_id" in consulta
    assert "WHERE al.estado = 'activo' ORDER BY tp.id" in consulta
    assert "tp.tipo_cobro AS tipo_cobro" in consulta
    assert "al.anio FROM tipos_de_pagos tp" in consulta
    assert tipos == [{
        "id": 2,
        "nombre": "MENSUALIDAD",
        "valor": 200_000.0,
        "tipo_cobro": "mensual",
        "activo": True,
        "mes_inicial": 7,
        "mes_final": 11,
        "frecuencia_meses": 1,
        "dia_limite_mes": 5,
        "dias_gracia": 0,
        "mora_tipo": None,
        "mora_valor": 0.0,
        "anio": 2026,
    }]


def test_los_conceptos_mensuales_del_estudiante_conservan_su_anio(monkeypatch):
    """Los adelantos y los meses vencidos leen el año del concepto de aqui."""
    concepto = {
        "id": 2, "nombre": "MENSUALIDAD", "valor": 0, "tipo_cobro": "mensual",
        "activo": True, "mes_inicial": 7, "mes_final": 11, "frecuencia_meses": 1,
        "dia_limite_mes": 5, "dias_gracia": 0, "mora_tipo": None, "mora_valor": 0,
        "anio": 2026,
    }
    monkeypatch.setattr(cobros, "obtener_curso_estudiante", lambda _c, _e: (3,))
    monkeypatch.setattr(cobros, "obtener_asignaciones_cobro_por_curso", lambda _c, _curso: {2: 200_000})
    monkeypatch.setattr(cobros, "obtener_valores_personalizados_estudiante", lambda _c, _e: {})
    monkeypatch.setattr(cobros, "obtener_tipos_pago", lambda _c: [concepto])

    conceptos = cobros.obtener_conceptos_mensuales_estudiante(object(), 7)

    assert [item["anio"] for item in conceptos] == [2026]


def test_adelantos_de_un_anio_que_no_ha_empezado_ofrecen_todos_sus_meses():
    """Un concepto de 2027 visto en diciembre de 2026: febrero a noviembre."""
    concepto = {"mes_inicial": 2, "mes_final": 11, "frecuencia_meses": 1, "anio": 2027}

    periodos = pagos_controller._periodos_programados(concepto, date(2026, 12, 10))

    assert periodos == [date(2027, mes, 1) for mes in range(2, 12)]


def test_adelantos_sin_mes_inicial_en_un_anio_que_no_ha_empezado_parten_de_enero():
    concepto = {"mes_inicial": None, "mes_final": 6, "frecuencia_meses": 2, "anio": 2027}

    periodos = pagos_controller._periodos_programados(concepto, date(2026, 12, 10))

    assert periodos == [date(2027, 1, 1), date(2027, 3, 1), date(2027, 5, 1)]


def test_adelantos_de_un_anio_que_termino_no_ofrecen_nada():
    concepto = {"mes_inicial": 2, "mes_final": 11, "frecuencia_meses": 1, "anio": 2026}

    assert pagos_controller._periodos_programados(concepto, date(2027, 1, 15)) == []


# ---------------------------------------------------------------------------
# 3. Paso 2.2: cada año cuenta solo sus pagos.
# ---------------------------------------------------------------------------

FILTRO_PAGOS_DEL_ANIO = (
    "AND pagos.anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE estado = 'activo')"
)


class CursorQueAnota:
    """Anota cada SQL, normalizado, con sus parametros; devuelve filas fijas."""

    def __init__(self, fila=None):
        self.consultas = []
        self.fila = fila

    def execute(self, query, params=None):
        self.consultas.append((" ".join(str(query).split()), params))

    def fetchall(self):
        return []

    def fetchone(self):
        return self.fila


def test_lo_pagado_cuenta_solo_pagos_y_aplicaciones_del_anio_activo():
    cursor = CursorQueAnota(fila=(1,))  # existe pagos_aplicaciones

    cobros.obtener_pagos_por_concepto_estudiantes(cursor, (7, 8), hoy=date(2026, 10, 15))

    _tabla, por_nombre, por_descripcion, aplicaciones = cursor.consultas
    assert FILTRO_PAGOS_DEL_ANIO in por_nombre[0]
    assert FILTRO_PAGOS_DEL_ANIO in por_descripcion[0]
    assert (
        "AND tp.anio_lectivo_id = (SELECT id FROM anios_lectivos WHERE estado = 'activo')"
        in aplicaciones[0]
    )
    # Sin parametros nuevos: el año va como subconsulta.
    assert por_nombre[1] == ((7, 8),)
    assert por_descripcion[1] == ((7, 8),)
    assert aplicaciones[1] == ((7, 8), date(2026, 10, 1))


def test_el_curso_del_precio_sale_de_la_matricula_del_anio_activo():
    cursor = CursorQueAnota(fila=(3,))

    assert cobros.obtener_curso_estudiante(cursor, 7) == (3,)
    consulta, params = cursor.consultas[0]
    assert consulta == (
        "SELECT m.curso_id FROM matriculas m "
        "JOIN anios_lectivos al ON al.id = m.anio_lectivo_id "
        "WHERE m.estudiante_id = %s AND al.estado = 'activo'"
    )
    assert params == (7,)


def test_el_estado_de_cuenta_suma_solo_pagos_del_anio_activo():
    cursor = CursorQueAnota(fila=(0, None))

    estado_cuenta_controller._resumen_pagos_estudiante(cursor, 7)

    consulta, params = cursor.consultas[0]
    assert FILTRO_PAGOS_DEL_ANIO in consulta
    assert params == (7,)


def test_los_reportes_de_estado_de_cuenta_cuentan_solo_pagos_del_anio_activo():
    cursor = CursorQueAnota()

    reportes_repository.consultar_pagos_estado_cuenta_por_estudiantes(cursor, (7, 8), True)
    reportes_repository.consultar_otros_pagos_por_estudiantes(cursor, (7, 8), True)

    assert len(cursor.consultas) == 3
    for consulta, params in cursor.consultas:
        assert FILTRO_PAGOS_DEL_ANIO in consulta
        assert params == ((7, 8),)
