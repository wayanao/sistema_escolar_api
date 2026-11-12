"""Puntualidad de pagos: quién paga sus cuotas mensuales a tiempo.

Para el panel del admin (pedido del usuario del 2026-11-11). Regla acordada
con el usuario ese día:

- Se miran los conceptos que se cobran cada mes (`tipo_cobro` mensual),
  activos, con precio mayor que cero en el curso del estudiante, del año
  activo. Solo las cuotas que ya vencieron: las mismas que cuenta la cartera
  (`listar_cuotas_vencidas`).
- Una cuota está a tiempo si quedó pagada completa a más tardar el día límite
  más los días de gracia (`fecha_efectiva`).
- La fecha de un pago es la que se registró (`COALESCE(fecha, fecha_pago)`):
  un pago registrado tarde con la fecha de ese día cuenta tarde.
- Los adelantos (`pagos_aplicaciones`) pagan el mes al que se aplicaron. Los
  demás pagos del concepto se reparten en orden, de la cuota más vieja a la
  más nueva, como en la cartera (`obtener_cuotas_vencidas_estudiante`). Una
  cuota pagada en partes queda pagada el día del abono que la completa.
- Siempre a tiempo: todas sus cuotas vencidas a tiempo. Quien no tiene cuotas
  vencidas (becados en $0, conceptos sin cuotas todavía) no se cuenta.
- Ranking: primero la mayor parte de cuotas a tiempo; si empatan, quien suele
  pagar más días antes del límite. Nadie que deba hoy entra al ranking, ni
  quien no ha pagado ninguna cuota a tiempo (en el Colegio Demo, el
  2026-11-11, alguien con sus 19 cuotas pagadas tarde salía de primero).
- Cursos: por el porcentaje de sus estudiantes que pagan siempre a tiempo.

Solo cuentas: sin base de datos. Las lecturas están en
`app/repositories/puntualidad_repository.py` y el armado, en
`app/controllers/puntualidad_controller.py`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Optional

# Diferencias de redondeo en abonos (pesos): por debajo, la cuota está pagada.
TOLERANCIA = 0.5
MEJORES_DEL_COLEGIO = 6
MEJORES_POR_CURSO = 5


@dataclass(frozen=True)
class Abono:
    monto: float
    fecha: date


@dataclass(frozen=True)
class CuotaEvaluada:
    periodo: date
    fecha_vencimiento: date
    fecha_efectiva: date
    fecha_pagada: Optional[date]

    @property
    def pagada(self) -> bool:
        return self.fecha_pagada is not None

    @property
    def a_tiempo(self) -> bool:
        return self.fecha_pagada is not None and self.fecha_pagada <= self.fecha_efectiva

    @property
    def dias_antes(self) -> Optional[int]:
        """Días entre el pago y el día límite: negativo si pagó en la gracia."""
        if self.fecha_pagada is None:
            return None
        return (self.fecha_vencimiento - self.fecha_pagada).days


def solo_fecha(valor, respaldo: date) -> date:
    """El día de un pago. Sin fecha (no debería pasar), el respaldo: así un
    pago sin fecha nunca cuenta como puntual."""
    if valor is None:
        return respaldo
    if isinstance(valor, datetime):
        return valor.date()
    return valor


def evaluar_cuotas(cuotas, valor_unitario: float, adelantos: dict, pagos: Iterable[Abono]) -> list[CuotaEvaluada]:
    """Cuándo quedó pagada cada cuota vencida de un concepto.

    `cuotas`: las vencidas, en orden (`listar_cuotas_vencidas`).
    `adelantos`: `{periodo: [Abono, ...]}` de `pagos_aplicaciones`.
    `pagos`: los demás pagos del concepto, en cualquier orden; se usan del más
    viejo al más nuevo, cada uno sobre la cuota más vieja que siga sin pagar.
    """
    restantes = sorted(pagos, key=lambda abono: abono.fecha)
    indice = 0
    disponible = restantes[0].monto if restantes else 0.0
    evaluadas = []

    for cuota in cuotas:
        faltante = float(valor_unitario)
        fecha = None

        for abono in sorted(adelantos.get(cuota.periodo, ()), key=lambda abono: abono.fecha):
            if faltante <= TOLERANCIA:
                break
            faltante -= min(abono.monto, faltante)
            fecha = abono.fecha if fecha is None else max(fecha, abono.fecha)

        while faltante > TOLERANCIA and indice < len(restantes):
            usado = min(disponible, faltante)
            if usado > 0:
                faltante -= usado
                disponible -= usado
                pago = restantes[indice]
                fecha = pago.fecha if fecha is None else max(fecha, pago.fecha)
            if disponible <= TOLERANCIA:
                indice += 1
                disponible = restantes[indice].monto if indice < len(restantes) else 0.0

        evaluadas.append(
            CuotaEvaluada(
                periodo=cuota.periodo,
                fecha_vencimiento=cuota.fecha_vencimiento,
                fecha_efectiva=cuota.fecha_efectiva,
                fecha_pagada=fecha if faltante <= TOLERANCIA else None,
            )
        )

    return evaluadas


def resumir_estudiante(estudiante: dict, evaluadas: list[CuotaEvaluada]) -> Optional[dict]:
    """La puntualidad de un estudiante, o `None` si no tiene cuotas vencidas."""
    if not evaluadas:
        return None
    a_tiempo = [cuota for cuota in evaluadas if cuota.a_tiempo]
    dias = [cuota.dias_antes for cuota in a_tiempo]
    return {
        **estudiante,
        "cuotas_vencidas": len(evaluadas),
        "cuotas_a_tiempo": len(a_tiempo),
        "dias_antes_promedio": round(sum(dias) / len(dias), 1) if dias else None,
        "siempre_a_tiempo": len(a_tiempo) == len(evaluadas),
        "debe": any(not cuota.pagada for cuota in evaluadas),
    }


def _texto(valor) -> str:
    return str(valor or "").strip().lower()


def _orden_ranking(item: dict):
    proporcion = item["cuotas_a_tiempo"] / item["cuotas_vencidas"]
    dias = item["dias_antes_promedio"]
    return (
        -proporcion,
        -(dias if dias is not None else float("-inf")),
        _texto(item.get("apellido")),
        _texto(item.get("nombre")),
    )


def _porcentaje(parte: int, total: int) -> float:
    return round(100 * parte / total, 1) if total else 0.0


def _publico(item: dict) -> dict:
    return {
        "estudiante_id": item["estudiante_id"],
        "nombre": item["nombre"],
        "apellido": item["apellido"],
        "curso_id": item["curso_id"],
        "curso_nombre": item["curso_nombre"],
        "cuotas_vencidas": item["cuotas_vencidas"],
        "cuotas_a_tiempo": item["cuotas_a_tiempo"],
        "dias_antes_promedio": item["dias_antes_promedio"],
        "siempre_a_tiempo": item["siempre_a_tiempo"],
    }


def _ranking(items: Iterable[dict], limite: int) -> list[dict]:
    """Los mejores: sin nadie que deba hoy ni quien nunca ha pagado a tiempo."""
    elegibles = (item for item in items if not item["debe"] and item["cuotas_a_tiempo"] > 0)
    return [_publico(item) for item in sorted(elegibles, key=_orden_ranking)[:limite]]


def armar_puntualidad(estudiantes: list[dict], hoy: date) -> dict:
    """La respuesta de `GET /cartera/puntualidad` a partir de lo evaluado.

    `estudiantes`: los resúmenes de `resumir_estudiante` (sin los `None`).
    """
    siempre = sum(1 for item in estudiantes if item["siempre_a_tiempo"])

    por_curso: dict = {}
    for item in estudiantes:
        por_curso.setdefault(item["curso_id"], []).append(item)

    cursos = []
    for curso_id, lista in por_curso.items():
        a_tiempo = sum(1 for item in lista if item["siempre_a_tiempo"])
        cursos.append(
            {
                "curso_id": curso_id,
                "curso_nombre": lista[0]["curso_nombre"],
                "estudiantes": len(lista),
                "siempre_a_tiempo": a_tiempo,
                "porcentaje": _porcentaje(a_tiempo, len(lista)),
                "mejores": _ranking(lista, MEJORES_POR_CURSO),
            }
        )
    cursos.sort(key=lambda curso: (-curso["porcentaje"], -curso["estudiantes"], _texto(curso["curso_nombre"])))

    return {
        "fecha_corte": hoy.isoformat(),
        "total_estudiantes": len(estudiantes),
        "siempre_a_tiempo": siempre,
        "porcentaje": _porcentaje(siempre, len(estudiantes)),
        "mejores": _ranking(estudiantes, MEJORES_DEL_COLEGIO),
        "cursos": cursos,
    }
