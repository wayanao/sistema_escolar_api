"""Controller de Cartera Vencida.

Genera el reporte de TODOS los estudiantes con mora, separando:
 - Deuda academica (conceptos asignados por curso)
 - Deuda por ventas de inventario (saldo pendiente de cargos)

Usa el mismo servicio `app.services.cartera` para mantener consistencia
con el resumen del estudiante y los reportes por curso.
"""
from __future__ import annotations

from app.database import get_connection
from app.services.cobros import (
    calcular_deudas_desde_contexto,
    obtener_tipos_pago,
)


def reporte_cartera_vencida(curso_id: int | None = None):
    """Devuelve la lista de estudiantes con deuda > 0.

    Estructura del item:
    {
        "estudiante_id": int,
        "nombre": str,
        "apellido": str,
        "curso_id": int,
        "curso_nombre": str,
        "deuda_academica": float,
        "deuda_inventario": float,
        "mora": float,
        "total": float,
        "cuotas_vencidas": int,        # suma de cuotas vencidas en conceptos recurrentes
        "conceptos": [                  # detalle de la deuda académica
            {
                "concepto": str,
                "tipo_cobro": str,
                "valor_total": float,
                "pagado": float,
                "mora": float,
                "cuotas_vencidas": int,
                "deuda": float,
            }, ...
        ],
        "ventas_pendientes": [
            {"venta_id": int, "fecha": str, "saldo": float}, ...
        ],
    }
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        tipos = obtener_tipos_pago(cursor)

        # 2. ¿Existe la tabla puente?
        cursor.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = ANY (current_schemas(false))
              AND table_name = 'tipos_pagos_cursos'
            """
        )
        tabla_puente = cursor.fetchone() is not None

        # 3. Cargar asignaciones por curso (índice global)
        asignaciones_por_curso = {}  # curso_id -> {tipo_pago_id: valor}
        if tabla_puente:
            cursor.execute(
                """
                SELECT curso_id, tipo_pago_id, valor
                FROM tipos_pagos_cursos
                WHERE activo = TRUE
                """
            )
            for r in cursor.fetchall():
                asignaciones_por_curso.setdefault(r[0], {})[r[1]] = float(r[2] or 0)

        # 4. Estudiantes (filtrar por curso si se pidió)
        where_curso = "AND e.curso_id = %s" if curso_id else ""
        params = (curso_id,) if curso_id else ()
        cursor.execute(
            f"""
            SELECT e.id, e.nombre, e.apellido, e.estado,
                   c.id AS curso_id, c.nombre AS curso_nombre
            FROM estudiantes e
            JOIN cursos c ON c.id = e.curso_id
            WHERE COALESCE(e.estado, 'Activo') ILIKE 'activo'
            {where_curso}
            ORDER BY c.nombre, e.apellido, e.nombre
            """,
            params,
        )
        estudiantes = cursor.fetchall()

        if not estudiantes:
            return []

        # 5. Pagos por estudiante: agrupados por tipo_pago (nombre, descripcion)
        est_ids = tuple(e[0] for e in estudiantes)
        cursor.execute(
            """
            SELECT estudiante_id, LOWER(COALESCE(tipo_pago, '')), COALESCE(SUM(monto), 0)
            FROM pagos
            WHERE estudiante_id IN %s
            GROUP BY estudiante_id, LOWER(COALESCE(tipo_pago, ''))
            """,
            (est_ids,),
        )
        pagos_por_est_tipo = {}
        for r in cursor.fetchall():
            pagos_por_est_tipo.setdefault(r[0], {})[r[1]] = float(r[2] or 0)

        cursor.execute(
            """
            SELECT estudiante_id, LOWER(COALESCE(descripcion, '')), COALESCE(SUM(monto), 0)
            FROM pagos
            WHERE estudiante_id IN %s AND descripcion IS NOT NULL
            GROUP BY estudiante_id, LOWER(COALESCE(descripcion, ''))
            """,
            (est_ids,),
        )
        pagos_por_est_desc = {}
        for r in cursor.fetchall():
            pagos_por_est_desc.setdefault(r[0], {})[r[1]] = float(r[2] or 0)

        # 6. Ventas pendientes (cargos de inventario con saldo)
        cursor.execute(
            """
            SELECT estudiante_id, id, fecha, total, COALESCE(pagado, 0)
            FROM ventas
            WHERE estudiante_id IN %s AND estado = 'Pendiente'
            ORDER BY fecha ASC
            """,
            (est_ids,),
        )
        ventas_por_est = {}
        for r in cursor.fetchall():
            est_id, v_id, fecha, total, pagado_v = r
            saldo = max(0.0, float(total or 0) - float(pagado_v or 0))
            if saldo <= 0:
                continue
            ventas_por_est.setdefault(est_id, []).append(
                {
                    "venta_id": v_id,
                    "fecha": fecha.isoformat() if fecha else None,
                    "saldo": saldo,
                }
            )

        # 7. Calcular deuda academica por estudiante
        resultado = []

        for est in estudiantes:
            (
                est_id, nombre, apellido, _estado,
                c_id, c_nombre,
            ) = est

            pagos_nombre = pagos_por_est_tipo.get(est_id, {})
            pagos_desc = pagos_por_est_desc.get(est_id, {})
            asign_curso = asignaciones_por_curso.get(c_id, {})
            resumen = calcular_deudas_desde_contexto(
                tipos_pago=tipos,
                asignaciones_curso=asign_curso,
                pagos_nombre=pagos_nombre,
                pagos_descripcion=pagos_desc,
            )
            conceptos = [
                deuda for deuda in resumen["deudas"] if deuda["deuda"] > 0
            ]
            deuda_academica = sum(deuda["deuda"] for deuda in conceptos)
            mora_total = sum(deuda["mora"] for deuda in conceptos)
            cuotas_vencidas_total = sum(
                deuda["cuotas_vencidas"] for deuda in conceptos
            )

            ventas_pendientes = ventas_por_est.get(est_id, [])
            deuda_inventario = sum(v["saldo"] for v in ventas_pendientes)
            total = deuda_academica + deuda_inventario

            if total <= 0:
                continue

            resultado.append(
                {
                    "estudiante_id": est_id,
                    "nombre": nombre,
                    "apellido": apellido,
                    "curso_id": c_id,
                    "curso_nombre": c_nombre,
                    "deuda_academica": round(deuda_academica, 2),
                    "deuda_inventario": round(deuda_inventario, 2),
                    "mora": round(mora_total, 2),
                    "total": round(total, 2),
                    "cuotas_vencidas": cuotas_vencidas_total,
                    "conceptos": conceptos,
                    "ventas_pendientes": ventas_pendientes,
                }
            )

        # Ordenar por mayor deuda
        resultado.sort(key=lambda x: x["total"], reverse=True)
        return resultado

    finally:
        cursor.close()
        conn.close()


def resumen_cartera_vencida():
    """Resumen para KPIs del dashboard: total deuda, # estudiantes en mora, etc."""
    items = reporte_cartera_vencida()
    total_estudiantes = len(items)
    total_deuda = sum(i["total"] for i in items)
    total_academico = sum(i["deuda_academica"] for i in items)
    total_inventario = sum(i["deuda_inventario"] for i in items)
    total_mora = sum(i["mora"] for i in items)
    top_5 = items[:5]

    # Distribución por curso
    por_curso = {}
    for i in items:
        por_curso.setdefault(
            i["curso_id"],
            {"curso_id": i["curso_id"], "curso_nombre": i["curso_nombre"], "total": 0.0, "estudiantes": 0},
        )
        por_curso[i["curso_id"]]["total"] += i["total"]
        por_curso[i["curso_id"]]["estudiantes"] += 1

    distribucion_cursos = sorted(por_curso.values(), key=lambda x: x["total"], reverse=True)

    return {
        "total_estudiantes": total_estudiantes,
        "total_deuda": round(total_deuda, 2),
        "total_academico": round(total_academico, 2),
        "total_inventario": round(total_inventario, 2),
        "total_mora": round(total_mora, 2),
        "top_5": top_5,
        "distribucion_cursos": distribucion_cursos,
    }
