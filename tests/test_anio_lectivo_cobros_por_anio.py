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
4. Paso 2.3: se puede pedir un año que no es el activo, para registrar un
   pago en el año de la deuda que salda (cerrado o en preparacion) y para
   adelantar en diciembre meses del año siguiente. Sin año, todo sigue como
   antes: las pruebas que ya existian no se tocaron.

Los casos A y B del diagnostico estan en
tests/test_anio_lectivo_cobros_caracterizacion.py.
"""
import datetime
from calendar import monthrange
from contextlib import contextmanager
from datetime import date, timedelta
from itertools import product
from types import SimpleNamespace

import pytest
from fastapi.routing import APIRoute
from pydantic import ValidationError

from app.controllers import estado_cuenta_controller, estudiante_controller, pagos_controller
from app.repositories import pagos_repository, reportes_repository
from app.routes import estudiantes as rutas_estudiantes
from app.routes import pagos as rutas_pagos
from app.schemas.pago import PagoAdelantadoCreate, PagoCreate
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
        self.parametros = []
        self._resultado = []

    def execute(self, query, params=None):
        normalizada = " ".join(str(query).split())
        self.consultas.append(normalizada)
        self.parametros.append(params)
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


# ---------------------------------------------------------------------------
# 4. Paso 2.3: pedir un año que no es el activo.
# ---------------------------------------------------------------------------

ID_2027 = 3  # id de 2027 en anios_lectivos, en preparacion
ANIOS_DE_PRUEBA = {1: (1, 2026, "cerrado"), ID_2027: (ID_2027, 2027, "preparacion")}


def test_sin_anio_los_conceptos_se_piden_como_siempre():
    cursor = CursorConceptos(COLUMNAS_TIPOS_PAGO, [])

    cobros.obtener_tipos_pago(cursor)

    assert "WHERE al.estado = 'activo'" in cursor.consultas[1]
    assert cursor.parametros[1] is None


def test_con_anio_los_conceptos_son_los_de_ese_anio():
    cursor = CursorConceptos(COLUMNAS_TIPOS_PAGO, [])

    cobros.obtener_tipos_pago(cursor, anio_lectivo_id=ID_2027)

    assert "WHERE al.id = %s ORDER BY tp.id" in cursor.consultas[1]
    assert cursor.parametros[1] == (ID_2027,)


def test_con_anio_el_curso_sale_de_la_matricula_de_ese_anio():
    cursor = CursorQueAnota(fila=(30,))

    assert cobros.obtener_curso_estudiante(cursor, 7, anio_lectivo_id=ID_2027) == (30,)
    consulta, params = cursor.consultas[0]
    assert consulta.endswith("WHERE m.estudiante_id = %s AND al.id = %s")
    assert params == (7, ID_2027)


def test_con_anio_lo_pagado_cuenta_los_pagos_de_ese_anio():
    cursor = CursorQueAnota(fila=(1,))  # existe pagos_aplicaciones

    cobros.obtener_pagos_por_concepto_estudiantes(
        cursor, (7, 8), hoy=date(2026, 12, 10), anio_lectivo_id=ID_2027,
    )

    _tabla, por_nombre, por_descripcion, aplicaciones = cursor.consultas
    assert "AND pagos.anio_lectivo_id = %s" in por_nombre[0]
    assert "AND pagos.anio_lectivo_id = %s" in por_descripcion[0]
    assert "AND tp.anio_lectivo_id = %s" in aplicaciones[0]
    assert por_nombre[1] == ((7, 8), ID_2027)
    assert por_descripcion[1] == ((7, 8), ID_2027)
    assert aplicaciones[1] == ((7, 8), date(2026, 12, 1), ID_2027)


class BaseDeCobros:
    """Base simulada con 2026 activo y 2027 en preparacion.

    El estudiante 7 esta en el curso 3 en 2026 y en el curso 30 en 2027. Cada
    año tiene su propia matricula: 300.000 en el curso de 2026 y 350.000 en el
    de 2027. No hay pagos.
    """

    def __init__(self):
        self.consultas = []
        self._filas = []

    def execute(self, query, params=None):
        consulta = " ".join(str(query).lower().split())
        self.consultas.append((consulta, params))
        pide_2027 = "al.id = %s" in consulta and params[-1] == ID_2027
        if "information_schema.columns" in consulta:
            self._filas = [(columna,) for columna in COLUMNAS_TIPOS_PAGO]
        elif "information_schema.tables" in consulta:
            self._filas = [(1,)]
        elif "from matriculas m" in consulta:
            self._filas = [(30,)] if pide_2027 else [(3,)]
        elif "from tipos_pagos_cursos" in consulta:
            self._filas = {3: [(1, 300_000)], 30: [(12, 350_000)]}[params[0]]
        elif "from tipos_pagos_estudiantes" in consulta:
            self._filas = []
        elif "from tipos_de_pagos tp" in consulta:
            id_concepto, anio = (12, 2027) if pide_2027 else (1, 2026)
            self._filas = [
                (id_concepto, "MATRICULA", 300_000, "anual", True, 2, 12, 1, None, 0, None, 0, anio),
            ]
        elif "lower(coalesce(" in consulta or "from pagos_aplicaciones pa" in consulta:
            self._filas = []
        else:
            raise AssertionError(f"Consulta no caracterizada: {consulta}")

    def fetchall(self):
        return list(self._filas)

    def fetchone(self):
        return self._filas[0] if self._filas else None


def test_el_precio_de_2027_sale_del_curso_de_2027():
    hoy = date(2026, 11, 20)

    del_2026 = cobros.calcular_deudas_estudiante(BaseDeCobros(), 7, hoy=hoy)
    del_2027 = cobros.calcular_deudas_estudiante(
        BaseDeCobros(), 7, hoy=hoy, anio_lectivo_id=ID_2027,
    )

    assert del_2026["curso_id"] == 3
    assert [d["valor_unitario"] for d in del_2026["deudas"]] == [300_000]
    assert del_2027["curso_id"] == 30
    assert [d["concepto_id"] for d in del_2027["deudas"]] == [12]
    # La matricula de 2027 se debe completa aunque el año no haya empezado.
    assert [d["deuda"] for d in del_2027["deudas"]] == [350_000]


def test_sin_matricula_en_el_anio_pedido_el_mensaje_lo_dice():
    class SinMatricula(BaseDeCobros):
        def execute(self, query, params=None):
            super().execute(query, params)
            if "from matriculas m" in " ".join(str(query).lower().split()):
                self._filas = []

    with pytest.raises(ValueError, match="no tiene matrícula en el año lectivo seleccionado"):
        cobros.calcular_deudas_estudiante(SinMatricula(), 7, anio_lectivo_id=ID_2027)
    # Sin año, el mensaje de siempre.
    with pytest.raises(ValueError, match="El estudiante seleccionado no existe."):
        cobros.calcular_deudas_estudiante(SinMatricula(), 7)


def test_el_pago_se_guarda_con_el_anio_pedido():
    cursor = CursorQueAnota(fila=(501,))

    pagos_repository.insertar_pago(
        cursor, 7, None, 300_000, "MATRICULA", "2026-11-20", "Efectivo", anio_lectivo_id=ID_2027,
    )
    pagos_repository.insertar_pago_adelantado(
        cursor, 7, 400_000, "MENSUALIDAD", "2026-12-10", "Efectivo", anio_lectivo_id=ID_2027,
    )

    (pago, params_pago), (adelanto, params_adelanto) = cursor.consultas
    assert "VALUES (%s, %s, %s, %s, %s, %s, %s)" in pago
    assert params_pago == (7, None, 300_000, "MATRICULA", "2026-11-20", "Efectivo", ID_2027)
    assert "VALUES (%s, %s, %s, %s, %s, %s)" in adelanto
    assert params_adelanto == (7, 400_000, "MENSUALIDAD", "2026-12-10", "Efectivo", ID_2027)


class CursorDePagos:
    """Lo que el registro de pagos lee de la base, con los años de prueba."""

    def __init__(self, anios=None):
        self.anios = dict(ANIOS_DE_PRUEBA if anios is None else anios)
        self.consultas = []
        self._fila = None

    def execute(self, query, params=None):
        consulta = " ".join(str(query).lower().split())
        self.consultas.append((consulta, params))
        if "from anios_lectivos where id = %s" in consulta:
            self._fila = self.anios.get(params[0])
        elif "information_schema.tables" in consulta or "from pg_indexes" in consulta:
            self._fila = (1,)
        else:
            self._fila = None

    def fetchone(self):
        return self._fila

    def fetchall(self):
        return []

    def close(self):
        pass

    def leyo_anios(self):
        return any("from anios_lectivos" in consulta for consulta, _ in self.consultas)


class ConexionDePagos:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        pass


def _pago(**cambios):
    datos = {
        "estudiante_id": 7, "monto": 300_000, "descripcion": "MATRICULA", "fecha": None,
        "venta_id": None, "metodos": None, "aplicaciones": None, "tipo_pago": "Efectivo",
    }
    datos.update(cambios)
    return SimpleNamespace(**datos)


@pytest.fixture
def registro(monkeypatch):
    """Registro de pagos con la deuda y el INSERT espiados."""
    cursor = CursorDePagos()
    conexion = ConexionDePagos(cursor)
    llamadas = {"saldo": [], "insert": []}

    def saldo(_cursor, _estudiante_id, _concepto, **kwargs):
        llamadas["saldo"].append(kwargs)
        return 1_000_000.0

    def insertar(_cursor, *_args, **kwargs):
        llamadas["insert"].append(kwargs)
        return 501

    monkeypatch.setattr(pagos_controller, "get_connection", lambda: conexion)
    monkeypatch.setattr(pagos_controller, "obtener_saldo_concepto", saldo)
    monkeypatch.setattr(pagos_controller, "insertar_pago", insertar)
    return SimpleNamespace(cursor=cursor, conexion=conexion, llamadas=llamadas)


@pytest.mark.parametrize(
    "anio_lectivo_id", [1, ID_2027], ids=["anio_cerrado", "anio_en_preparacion"],
)
def test_un_pago_se_registra_en_el_anio_de_la_deuda_que_salda(registro, anio_lectivo_id):
    """Decision 6: aunque el año este cerrado."""
    pago_id = pagos_controller.registrar_pago_controller(_pago(anio_lectivo_id=anio_lectivo_id))

    assert pago_id == 501
    assert registro.llamadas["saldo"] == [{"anio_lectivo_id": anio_lectivo_id}]
    assert registro.llamadas["insert"] == [{"anio_lectivo_id": anio_lectivo_id}]
    assert registro.conexion.commits == 1


def test_un_pago_a_un_anio_que_no_existe_no_se_registra(registro):
    with pytest.raises(ValueError, match="El año lectivo seleccionado no existe."):
        pagos_controller.registrar_pago_controller(_pago(anio_lectivo_id=99))

    assert registro.llamadas == {"saldo": [], "insert": []}
    assert registro.conexion.rollbacks == 1


def test_sin_anio_el_pago_va_al_anio_activo_como_siempre(registro):
    pagos_controller.registrar_pago_controller(_pago())

    assert registro.llamadas["saldo"] == [{}]
    assert registro.llamadas["insert"] == [{"anio_lectivo_id": None}]
    assert not registro.cursor.leyo_anios()


def test_las_cuotas_que_se_pagan_son_las_del_anio_del_pago(monkeypatch):
    """Una aplicacion solo puede ser de un concepto del año del pago."""
    conexion = ConexionDePagos(CursorDePagos())
    recibido = {}

    def cuotas(_cursor, _estudiante_id, hoy=None, **kwargs):
        recibido.update(kwargs)
        return []

    monkeypatch.setattr(pagos_controller, "get_connection", lambda: conexion)
    monkeypatch.setattr(pagos_controller, "obtener_cuotas_vencidas_estudiante", cuotas)
    aplicacion = SimpleNamespace(tipo_pago_id=2, periodo=date(2026, 10, 1), monto=200_000)

    with pytest.raises(ValueError, match="no tiene cuotas vencidas disponibles"):
        pagos_controller.registrar_pago_controller(
            _pago(anio_lectivo_id=ID_2027, aplicaciones=[aplicacion], monto=200_000),
        )

    assert recibido == {"anio_lectivo_id": ID_2027}
    assert conexion.rollbacks == 1


def _mensualidad_2027():
    """Como la devuelve obtener_conceptos_mensuales_estudiante para 2027."""
    return {
        "id": 12, "nombre": "MENSUALIDAD", "valor_unitario": 200_000, "valor_origen": "curso",
        "mes_inicial": 2, "mes_final": 11, "frecuencia_meses": 1, "anio": 2027,
    }


MESES_FEBRERO_A_NOVIEMBRE = [
    "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre",
]


def test_en_diciembre_se_ofrecen_los_meses_de_2027_para_adelantar(monkeypatch):
    conexion = ConexionDePagos(CursorDePagos())

    def conceptos(_cursor, _estudiante_id, **kwargs):
        return [_mensualidad_2027()] if kwargs == {"anio_lectivo_id": ID_2027} else []

    monkeypatch.setattr(pagos_controller, "get_connection", lambda: conexion)
    monkeypatch.setattr(pagos_controller, "obtener_conceptos_mensuales_estudiante", conceptos)
    monkeypatch.setattr(pagos_controller, "leer_aplicaciones_vigentes", lambda _c, _e, _t: [])

    opciones = pagos_controller.obtener_opciones_adelanto_controller(
        7, hoy=date(2026, 12, 10), anio_lectivo_id=ID_2027,
    )

    periodos = opciones["opciones"][0]["periodos_disponibles"]
    assert [p["etiqueta"] for p in periodos] == [f"{mes} 2027" for mes in MESES_FEBRERO_A_NOVIEMBRE]
    assert opciones["opciones"][0]["total_disponible"] == 10 * 200_000


def test_en_diciembre_se_registra_un_adelanto_de_meses_de_2027(monkeypatch):
    conexion = ConexionDePagos(CursorDePagos())
    recibidos = {"conceptos": [], "insert": [], "aplicaciones": []}

    def conceptos(_cursor, _estudiante_id, **kwargs):
        recibidos["conceptos"].append(kwargs)
        return [_mensualidad_2027()]

    def insertar(_cursor, *_args, **kwargs):
        recibidos["insert"].append(kwargs)
        return 601

    def aplicar(_cursor, _pago_id, _estudiante_id, tipo_pago_id, periodo, monto):
        recibidos["aplicaciones"].append((tipo_pago_id, periodo, monto))

    monkeypatch.setattr(pagos_controller, "get_connection", lambda: conexion)
    monkeypatch.setattr(pagos_controller, "obtener_conceptos_mensuales_estudiante", conceptos)
    monkeypatch.setattr(pagos_controller, "leer_aplicaciones_vigentes", lambda _c, _e, _t: [])
    monkeypatch.setattr(pagos_controller, "insertar_pago_adelantado", insertar)
    monkeypatch.setattr(pagos_controller, "insertar_aplicacion", aplicar)
    adelanto = SimpleNamespace(
        estudiante_id=7, tipo_pago_id=12, cantidad_meses=2, monto_distribuir=None, fecha=None,
        metodos=[SimpleNamespace(tipo="Efectivo", monto=400_000, nota=None)],
        anio_lectivo_id=ID_2027,
    )

    resultado = pagos_controller.registrar_pago_adelantado_controller(
        adelanto, hoy=date(2026, 12, 10),
    )

    assert recibidos["conceptos"] == [{"anio_lectivo_id": ID_2027}]
    assert recibidos["insert"] == [{"anio_lectivo_id": ID_2027}]
    assert recibidos["aplicaciones"] == [
        (12, date(2027, 2, 1), 200_000),
        (12, date(2027, 3, 1), 200_000),
    ]
    assert [p["etiqueta"] for p in resultado["periodos"]] == ["Febrero 2027", "Marzo 2027"]
    assert conexion.commits == 1


def test_las_deudas_del_estudiante_en_otro_anio(monkeypatch):
    cursor = CursorDePagos()
    recibido = []

    @contextmanager
    def cursor_de_prueba(*_args, **_kwargs):
        yield cursor

    def deudas(_cursor, _estudiante_id, **kwargs):
        recibido.append(kwargs)
        return {"curso_id": 30, "deudas": [{"concepto": "MATRICULA", "deuda": 350_000.0}]}

    monkeypatch.setattr(estudiante_controller, "get_cursor", cursor_de_prueba)
    monkeypatch.setattr(estudiante_controller, "calcular_deudas_estudiante", deudas)

    respuesta = estudiante_controller.obtener_deudas_estudiante_controller(
        7, anio_lectivo_id=ID_2027,
    )

    assert recibido == [{"anio_lectivo_id": ID_2027}]
    assert respuesta == {
        "estudiante_id": 7,
        "curso_id": 30,
        "deudas": [{"concepto": "MATRICULA", "deuda": 350_000.0}],
        "total_deuda": 350_000.0,
    }
    with pytest.raises(ValueError, match="El año lectivo seleccionado no existe."):
        estudiante_controller.obtener_deudas_estudiante_controller(7, anio_lectivo_id=99)


RUTAS_CON_ANIO = {
    "/pagos/vencidos/opciones/{estudiante_id}": (rutas_pagos, "obtener_opciones_vencidas_controller"),
    "/pagos/adelanto/opciones/{estudiante_id}": (rutas_pagos, "obtener_opciones_adelanto_controller"),
    "/estudiantes/{estudiante_id}/deudas": (rutas_estudiantes, "obtener_deudas_estudiante_controller"),
}


def _ruta(path):
    modulo, _controlador = RUTAS_CON_ANIO[path]
    return next(
        ruta for ruta in modulo.router.routes
        if isinstance(ruta, APIRoute) and ruta.path == path
    )


@pytest.mark.parametrize("path", sorted(RUTAS_CON_ANIO))
def test_las_consultas_aceptan_el_anio_opcional(path):
    parametros = {p.name: p for p in _ruta(path).dependant.query_params}

    assert set(parametros) == {"anio_lectivo_id"}
    anio = parametros["anio_lectivo_id"]
    assert not anio.field_info.is_required()
    assert anio.field_info.default is None
    limites = {type(m).__name__.lower(): m for m in anio.field_info.metadata}
    assert limites["gt"].gt == 0


@pytest.mark.parametrize("path", sorted(RUTAS_CON_ANIO))
def test_las_consultas_le_pasan_el_anio_al_controlador(monkeypatch, path):
    modulo, controlador = RUTAS_CON_ANIO[path]
    recibido = []
    monkeypatch.setattr(
        modulo, controlador,
        lambda estudiante_id, **kwargs: recibido.append((estudiante_id, kwargs)),
    )
    endpoint = _ruta(path).endpoint

    endpoint(7, anio_lectivo_id=ID_2027)
    endpoint(7, anio_lectivo_id=None)

    assert recibido == [(7, {"anio_lectivo_id": ID_2027}), (7, {"anio_lectivo_id": None})]


def test_el_cuerpo_del_pago_y_del_adelanto_acepta_el_anio_opcional():
    assert PagoCreate(estudiante_id=7, monto=1).anio_lectivo_id is None
    assert PagoCreate(estudiante_id=7, monto=1, anio_lectivo_id=ID_2027).anio_lectivo_id == ID_2027
    with pytest.raises(ValidationError):
        PagoCreate(estudiante_id=7, monto=1, anio_lectivo_id=0)

    adelanto = {
        "estudiante_id": 7, "tipo_pago_id": 12, "cantidad_meses": 1,
        "metodos": [{"tipo": "Efectivo", "monto": 1}],
    }
    assert PagoAdelantadoCreate(**adelanto).anio_lectivo_id is None
    assert PagoAdelantadoCreate(**adelanto, anio_lectivo_id=ID_2027).anio_lectivo_id == ID_2027
    with pytest.raises(ValidationError):
        PagoAdelantadoCreate(**adelanto, anio_lectivo_id=-1)
