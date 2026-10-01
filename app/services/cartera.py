"""Servicio de cartera escolar.

Centraliza la lógica de cálculo de deuda por tipo de pago para que sea
consistente entre el resumen del estudiante, el reporte por curso y
cualquier otro punto del sistema que necesite saber cuánto debe alguien.

Reglas implementadas:
- Cuotas vencidas se calculan respetando mes_inicial, mes_final, frecuencia_meses,
  dia_limite_mes y dias_gracia.
- La mora se aplica POR CADA cuota vencida no pagada.
- El día de vencimiento se ajusta automáticamente si el mes tiene menos días
  (por ejemplo dia_limite_mes=31 en febrero → último día válido).
- Si NO hay configuración de recurrencia (mes_inicial vacío), el sistema NO
  asume meses retroactivos; solo cobra la cuota del mes actual si ya venció.
"""
from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from app.core.fechas import hoy_en_colombia


@dataclass
class ResultadoCuotas:
    cuotas_vencidas: int
    proxima_fecha: Optional[date]
    proxima_cuota_pendiente: bool  # True si la siguiente cuota ya tiene fecha asignada


@dataclass(frozen=True)
class CuotaVencida:
    periodo: date
    fecha_vencimiento: date
    fecha_efectiva: date


def _ultimo_dia_del_mes(anio: int, mes: int) -> int:
    return monthrange(anio, mes)[1]


def _mes_de_referencia(hoy: date, anio: int) -> int:
    """El "mes actual" de `anio`, visto desde `hoy`.

    Es el mes que se cobra cuando el concepto no tiene `mes_inicial`. En el
    año de `hoy`, el mes de hoy, como siempre. En un año que ya terminó,
    diciembre. En uno que no ha empezado, enero, que todavía no vence.
    """
    if anio == hoy.year:
        return hoy.month
    return 12 if anio < hoy.year else 1


def listar_cuotas_vencidas(
    hoy: Optional[date] = None,
    *,
    anio: Optional[int] = None,
    mes_inicial: Optional[int] = None,
    mes_final: int = 12,
    frecuencia_meses: int = 1,
    dia_limite_mes: Optional[int] = None,
    dias_gracia: int = 0,
    max_cuotas: int = 10,
) -> list[CuotaVencida]:
    """Devuelve las cuotas vencidas con su periodo y fecha limite real.

    `anio` es el año lectivo cuyas cuotas se listan; sin el, el de `hoy`. El
    corte siempre es `hoy`: un año que ya termino tiene todas sus cuotas
    vencidas, y uno que no ha empezado, ninguna. Asi, el 1 de enero las
    cuotas del año que sigue activo no desaparecen.
    """
    if hoy is None:
        hoy = hoy_en_colombia()
    anio_cuotas = int(anio) if anio else hoy.year
    mes_referencia = _mes_de_referencia(hoy, anio_cuotas)

    frecuencia = max(1, int(frecuencia_meses or 1))
    gracia = max(0, int(dias_gracia or 0))
    mes_inicio = int(mes_inicial) if mes_inicial else mes_referencia
    if not (1 <= mes_inicio <= 12):
        mes_inicio = mes_referencia
    mes_fin = int(mes_final) if mes_final is not None else 12
    if not (1 <= mes_fin <= 12):
        mes_fin = 12

    cuotas = []
    for i in range(max(1, int(max_cuotas or 1))):
        mes_cuota = mes_inicio + i * frecuencia
        if mes_cuota < 1 or mes_cuota > mes_fin:
            break

        ultimo_dia = _ultimo_dia_del_mes(anio_cuotas, mes_cuota)
        dia = int(dia_limite_mes) if dia_limite_mes else ultimo_dia
        dia = min(dia, ultimo_dia)
        fecha_vencimiento = date(anio_cuotas, mes_cuota, dia)
        fecha_efectiva = fecha_vencimiento + timedelta(days=gracia)
        if hoy < fecha_efectiva:
            break

        cuotas.append(CuotaVencida(
            periodo=date(anio_cuotas, mes_cuota, 1),
            fecha_vencimiento=fecha_vencimiento,
            fecha_efectiva=fecha_efectiva,
        ))

    return cuotas


def calcular_cuotas_vencidas(
    hoy: Optional[date] = None,
    *,
    anio: Optional[int] = None,
    mes_inicial: Optional[int] = None,
    mes_final: int = 12,
    frecuencia_meses: int = 1,
    dia_limite_mes: Optional[int] = None,
    dias_gracia: int = 0,
    max_cuotas: int = 10,
) -> ResultadoCuotas:
    """Calcula cuántas cuotas mensuales están vencidas hasta `hoy`.

    Una cuota se considera vencida cuando `hoy >= fecha_vencimiento + dias_gracia`.
    `anio` es el año de las cuotas, como en `listar_cuotas_vencidas`.
    """
    if hoy is None:
        hoy = hoy_en_colombia()
    anio_cuotas = int(anio) if anio else hoy.year
    mes_referencia = _mes_de_referencia(hoy, anio_cuotas)

    cuotas_vencidas = listar_cuotas_vencidas(
        hoy=hoy,
        anio=anio_cuotas,
        mes_inicial=mes_inicial,
        mes_final=mes_final,
        frecuencia_meses=frecuencia_meses,
        dia_limite_mes=dia_limite_mes,
        dias_gracia=dias_gracia,
        max_cuotas=max_cuotas,
    )

    frecuencia = max(1, int(frecuencia_meses or 1))
    mes_inicio = int(mes_inicial) if mes_inicial else mes_referencia
    if not (1 <= mes_inicio <= 12):
        mes_inicio = mes_referencia
    mes_fin = int(mes_final) if mes_final is not None else 12
    if not (1 <= mes_fin <= 12):
        mes_fin = 12
    siguiente_mes = mes_inicio + len(cuotas_vencidas) * frecuencia
    proxima_fecha: Optional[date] = None
    if 1 <= siguiente_mes <= mes_fin:
        ultimo_dia = _ultimo_dia_del_mes(anio_cuotas, siguiente_mes)
        dia = int(dia_limite_mes) if dia_limite_mes else ultimo_dia
        proxima_fecha = date(anio_cuotas, siguiente_mes, min(dia, ultimo_dia))

    return ResultadoCuotas(
        cuotas_vencidas=len(cuotas_vencidas),
        proxima_fecha=proxima_fecha,
        proxima_cuota_pendiente=proxima_fecha is not None,
    )


def calcular_mora(
    *,
    saldo_unitario: float,
    cuotas_vencidas_sin_pagar: int,
    mora_tipo: Optional[str],
    mora_valor: float,
) -> float:
    """Calcula el monto total de mora.

    - 'porcentaje': mora_valor% del saldo unitario por cada cuota vencida no pagada.
    - 'fijo': mora_valor por cada cuota vencida no pagada.
    - cualquier otro valor: 0.
    """
    if not mora_tipo or cuotas_vencidas_sin_pagar <= 0:
        return 0.0

    valor = float(mora_valor or 0)
    if valor <= 0:
        return 0.0

    if mora_tipo == "porcentaje":
        return saldo_unitario * (valor / 100.0) * cuotas_vencidas_sin_pagar
    if mora_tipo == "fijo":
        return valor * cuotas_vencidas_sin_pagar
    return 0.0


def calcular_deuda_concepto(
    *,
    valor_unitario: float,
    tipo_cobro: str,
    pagado: float,
    hoy: Optional[date] = None,
    anio: Optional[int] = None,
    mes_inicial: Optional[int] = None,
    mes_final: int = 12,
    frecuencia_meses: int = 1,
    dia_limite_mes: Optional[int] = None,
    dias_gracia: int = 0,
    max_cuotas: int = 10,
    mora_tipo: Optional[str] = None,
    mora_valor: float = 0.0,
    es_legacy_mensualidad: bool = False,
) -> dict:
    """Calcula la deuda de un concepto para un estudiante.

    `anio` es el año lectivo del concepto: sus cuotas se cuentan en ese año
    (ver `listar_cuotas_vencidas`). Sin el, el de `hoy`.

    Devuelve un dict con:
        valor_total: lo que debería haber pagado a la fecha (sin contar mora)
        cuotas_vencidas: 0 si no es mensual/recurrente
        mora: monto de mora calculado sobre lo no pagado
        pagado: lo recibido
        deuda: max(0, valor_total + mora - pagado)
    """
    tipo = (tipo_cobro or "unico").lower()
    es_recurrente = tipo == "mensual" or es_legacy_mensualidad

    if es_recurrente:
        res = calcular_cuotas_vencidas(
            hoy=hoy,
            anio=anio,
            mes_inicial=mes_inicial,
            mes_final=mes_final,
            frecuencia_meses=frecuencia_meses,
            dia_limite_mes=dia_limite_mes,
            dias_gracia=dias_gracia,
            max_cuotas=max_cuotas,
        )
        cuotas_vencidas = res.cuotas_vencidas
        valor_total = float(valor_unitario) * cuotas_vencidas
    else:
        cuotas_vencidas = 0
        valor_total = float(valor_unitario)

    pagado_f = float(pagado or 0)
    saldo_sin_mora = max(0.0, valor_total - pagado_f)

    # Mora: una unidad de mora por cada cuota vencida que NO esté pagada.
    cuotas_sin_pagar = 0
    if es_recurrente and cuotas_vencidas > 0 and valor_unitario > 0:
        cuotas_pagadas = min(cuotas_vencidas, int(pagado_f // float(valor_unitario)))
        cuotas_sin_pagar = max(0, cuotas_vencidas - cuotas_pagadas)
    elif not es_recurrente and saldo_sin_mora > 0:
        cuotas_sin_pagar = 1  # único o anual: 1 unidad de mora cuando hay saldo

    mora = calcular_mora(
        saldo_unitario=float(valor_unitario),
        cuotas_vencidas_sin_pagar=cuotas_sin_pagar,
        mora_tipo=mora_tipo,
        mora_valor=mora_valor,
    )

    deuda = max(0.0, valor_total + mora - pagado_f)

    return {
        "valor_total": valor_total,
        "cuotas_vencidas": cuotas_vencidas,
        "mora": mora,
        "pagado": pagado_f,
        "deuda": deuda,
    }
