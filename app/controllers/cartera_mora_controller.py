"""Controller de Cartera Vencida.

Genera el reporte de TODOS los estudiantes con mora, separando:
 - Deuda académica (matrícula / mensualidad / conceptos asignados por curso)
 - Deuda por ventas de inventario (saldo pendiente de cargos)

Usa el mismo servicio `app.services.cartera` para mantener consistencia
con el resumen del estudiante y los reportes por curso.
"""
from __future__ import annotations

from datetime import date

from app.database import get_connection
from app.services.cartera import calcular_deuda_concepto


def _col_or_default(cols, name, default_sql):
    return name if name in cols else default_sql


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
        # 1. Columnas disponibles en tipos_de_pagos
        cursor.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = ANY (current_schemas(false))
              AND table_name = 'tipos_de_pagos'
            """
        )
        cols_tp = {row[0] for row in cursor.fetchall()}

        c = _col_or_default

        cursor.execute(
            f"""
            SELECT id, nombre, valor,
                {c(cols_tp, 'tipo_cobro', "'unico'")} AS tipo_cobro,
                {c(cols_tp, 'activo', 'TRUE')} AS activo,
                {c(cols_tp, 'mes_inicial', 'NULL')} AS mes_inicial,
                {c(cols_tp, 'frecuencia_meses', '1')} AS frecuencia_meses,
                {c(cols_tp, 'dia_limite_mes', 'NULL')} AS dia_limite_mes,
                {c(cols_tp, 'dias_gracia', '0')} AS dias_gracia,
                {c(cols_tp, 'mora_tipo', 'NULL')} AS mora_tipo,
                {c(cols_tp, 'mora_valor', '0')} AS mora_valor
            FROM tipos_de_pagos ORDER BY id
            """
        )
        tipos = [
            {
                "id": r[0],
                "nombre": r[1],
                "valor": float(r[2] or 0),
                "tipo_cobro": r[3] or "unico",
                "activo": bool(r[4]) if r[4] is not None else True,
                "mes_inicial": r[5],
                "frecuencia_meses": int(r[6]) if r[6] is not None else 1,
                "dia_limite_mes": r[7],
                "dias_gracia": int(r[8]) if r[8] is not None else 0,
                "mora_tipo": r[9],
                "mora_valor": float(r[10] or 0),
            }
            for r in cursor.fetchall()
        ]

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
                   c.id AS curso_id, c.nombre AS curso_nombre,
                   c.matricula, c.mensualidad, c.meses,
                   COALESCE(e.descuento_matricula, 0),
                   COALESCE(e.descuento_mensualidad, 0)
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

        # 7. Calcular deuda académica por estudiante
        hoy = date.today()
        resultado = []

        for est in estudiantes:
            (
                est_id, nombre, apellido, _estado,
                c_id, c_nombre,
                matricula, mensualidad, meses,
                desc_mat, desc_men,
            ) = est

            pagos_nombre = pagos_por_est_tipo.get(est_id, {})
            pagos_desc = pagos_por_est_desc.get(est_id, {})
            asign_curso = asignaciones_por_curso.get(c_id, {})

            conceptos = []
            deuda_academica = 0.0
            mora_total = 0.0
            cuotas_vencidas_total = 0

            for tp in tipos:
                tipo_cobro = (tp["tipo_cobro"] or "unico").lower()
                if not tp["activo"] or tipo_cobro == "opcional":
                    continue

                nombre_lower = tp["nombre"].lower()
                es_legacy_matricula = nombre_lower in ("matricula", "matrícula")
                es_legacy_mensualidad = nombre_lower in (
                    "pension", "pensión", "mensualidad", "colegiatura"
                )
                es_legacy = es_legacy_matricula or es_legacy_mensualidad
                tiene_asignacion = tp["id"] in asign_curso

                if not tiene_asignacion and not es_legacy:
                    continue

                # Valor unitario
                if tiene_asignacion:
                    valor_unitario = asign_curso[tp["id"]]
                elif es_legacy_matricula:
                    base = tp["valor"] if tp["valor"] > 0 else float(matricula or 0)
                    valor_unitario = base - float(desc_mat or 0)
                else:
                    base = tp["valor"] if tp["valor"] > 0 else float(mensualidad or 0)
                    valor_unitario = base - float(desc_men or 0)

                pagado = pagos_nombre.get(nombre_lower, 0.0)
                if pagado == 0.0:
                    pagado = pagos_desc.get(nombre_lower, 0.0)

                r = calcular_deuda_concepto(
                    valor_unitario=valor_unitario,
                    tipo_cobro=tipo_cobro,
                    pagado=pagado,
                    hoy=hoy,
                    mes_inicial=tp["mes_inicial"],
                    frecuencia_meses=tp["frecuencia_meses"],
                    dia_limite_mes=tp["dia_limite_mes"],
                    dias_gracia=tp["dias_gracia"],
                    max_cuotas=int(meses or 10),
                    mora_tipo=tp["mora_tipo"],
                    mora_valor=tp["mora_valor"],
                    es_legacy_mensualidad=es_legacy_mensualidad,
                )

                if r["deuda"] > 0:
                    deuda_academica += r["deuda"]
                    mora_total += r["mora"]
                    cuotas_vencidas_total += r["cuotas_vencidas"]
                    conceptos.append(
                        {
                            "concepto": tp["nombre"],
                            "tipo_cobro": tipo_cobro,
                            "valor_total": r["valor_total"],
                            "pagado": r["pagado"],
                            "mora": r["mora"],
                            "cuotas_vencidas": r["cuotas_vencidas"],
                            "deuda": r["deuda"],
                        }
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
