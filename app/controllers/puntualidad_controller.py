"""Puntualidad de pagos del año activo (panel del admin, 2026-11-11).

Junta las lecturas de `app/repositories/puntualidad_repository.py` con las
reglas de cobro de siempre (`app/services/cobros.py`: qué conceptos se cobran
a cada estudiante y a qué precio; `app/services/cartera.py`: qué cuotas ya
vencieron) y con las cuentas de `app/services/puntualidad.py`. Solo lee.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Optional

from app.core.fechas import hoy_en_colombia
from app.database import get_cursor
from app.repositories.puntualidad_repository import (
    leer_adelantos,
    leer_estudiantes_del_anio_activo,
    leer_pagos_de_cuotas,
    leer_precios_por_curso,
)
from app.services.cartera import listar_cuotas_vencidas
from app.services.cobros import (
    MAX_CUOTAS_ANUALES,
    _valor_unitario_concepto,
    normalizar_concepto,
    obtener_tipos_pago,
    obtener_valores_personalizados_por_estudiantes,
    tabla_pagos_aplicaciones_existe,
)
from app.services.puntualidad import (
    Abono,
    armar_puntualidad,
    evaluar_cuotas,
    resumir_estudiante,
    solo_fecha,
)


def _conceptos_mensuales(cursor) -> list[dict]:
    return [
        tipo
        for tipo in obtener_tipos_pago(cursor)
        if tipo["activo"] and normalizar_concepto(tipo["tipo_cobro"]) == "mensual"
    ]


def _pagos_del_concepto(filas: list[tuple], nombre: str, hoy: date) -> list[Abono]:
    """Los pagos de un concepto, buscados como en la cartera: por `tipo_pago`
    y, si por ahí no hay nada, por `descripcion`."""
    por_tipo = [Abono(float(monto or 0), solo_fecha(fecha, hoy)) for tipo, _desc, monto, fecha in filas if tipo == nombre]
    if sum(abono.monto for abono in por_tipo) > 0:
        return por_tipo
    return [Abono(float(monto or 0), solo_fecha(fecha, hoy)) for _tipo, desc, monto, fecha in filas if desc == nombre]


def reporte_puntualidad(hoy: Optional[date] = None) -> dict:
    """Quién paga a tiempo sus cuotas mensuales del año activo: el total, el
    ranking de cursos y los mejores de cada curso y del colegio."""
    hoy = hoy or hoy_en_colombia()

    with get_cursor() as cursor:
        conceptos = _conceptos_mensuales(cursor)
        if not conceptos:
            return armar_puntualidad([], hoy)
        precios_por_curso = leer_precios_por_curso(cursor)
        estudiantes = leer_estudiantes_del_anio_activo(cursor)
        if not estudiantes:
            return armar_puntualidad([], hoy)

        ids = tuple(fila[0] for fila in estudiantes)
        valores_por_estudiante = obtener_valores_personalizados_por_estudiantes(cursor, ids)
        hay_adelantos = tabla_pagos_aplicaciones_existe(cursor)
        filas_pagos = leer_pagos_de_cuotas(cursor, ids, sin_adelantos=hay_adelantos)
        filas_adelantos = leer_adelantos(cursor, ids) if hay_adelantos else []

    pagos_por_estudiante = defaultdict(list)
    for estudiante_id, tipo, descripcion, monto, fecha in filas_pagos:
        pagos_por_estudiante[estudiante_id].append((tipo, descripcion, monto, fecha))

    adelantos = defaultdict(lambda: defaultdict(list))
    for estudiante_id, tipo_pago_id, periodo, monto, fecha in filas_adelantos:
        adelantos[(estudiante_id, tipo_pago_id)][periodo].append(Abono(float(monto or 0), solo_fecha(fecha, hoy)))

    resumenes = []
    for estudiante_id, nombre, apellido, curso_id, curso_nombre in estudiantes:
        evaluadas = []
        for concepto in conceptos:
            valor_unitario, _origen = _valor_unitario_concepto(
                tipo_pago=concepto,
                asignaciones_curso=precios_por_curso.get(curso_id, {}),
                valores_estudiante=valores_por_estudiante.get(estudiante_id, {}),
            )
            if not valor_unitario or valor_unitario <= 0:
                continue
            cuotas = listar_cuotas_vencidas(
                hoy=hoy,
                anio=concepto.get("anio"),
                mes_inicial=concepto.get("mes_inicial"),
                mes_final=concepto.get("mes_final", 12),
                frecuencia_meses=concepto.get("frecuencia_meses", 1),
                dia_limite_mes=concepto.get("dia_limite_mes"),
                dias_gracia=concepto.get("dias_gracia", 0),
                max_cuotas=MAX_CUOTAS_ANUALES,
            )
            if not cuotas:
                continue
            evaluadas.extend(
                evaluar_cuotas(
                    cuotas,
                    float(valor_unitario),
                    adelantos.get((estudiante_id, concepto["id"]), {}),
                    _pagos_del_concepto(
                        pagos_por_estudiante.get(estudiante_id, []),
                        normalizar_concepto(concepto["nombre"]),
                        hoy,
                    ),
                )
            )

        resumen = resumir_estudiante(
            {
                "estudiante_id": estudiante_id,
                "nombre": nombre,
                "apellido": apellido,
                "curso_id": curso_id,
                "curso_nombre": curso_nombre,
            },
            evaluadas,
        )
        if resumen:
            resumenes.append(resumen)

    return armar_puntualidad(resumenes, hoy)
