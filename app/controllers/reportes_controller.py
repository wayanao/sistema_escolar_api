from app.database import get_connection
from app.repositories.reportes_repository import (
    consultar_egresos_rango,
    consultar_estudiantes_estado_cuenta_curso,
    consultar_ingresos_mes,
    consultar_ingresos_rango,
    consultar_otros_pagos_por_estudiantes,
    consultar_pagos_estado_cuenta_por_estudiantes,
    consultar_reporte_general,
)
from app.services.cobros import (
    obtener_asignaciones_cobro_por_curso,
    obtener_pagos_por_concepto_estudiantes,
    obtener_tipos_pago,
    obtener_valores_personalizados_por_estudiantes,
    tabla_pagos_aplicaciones_existe,
)
from app.services.reportes_financieros import construir_estado_cuenta_curso


def _formatear_ingreso(row):
    estado = row[7] if len(row) > 7 and row[7] else "Pagado"
    anulado = str(estado).strip().lower() == "anulado"
    return {
        "id": row[0],
        "estudiante": f"{row[1]} {row[2]}" if row[1] else "Desconocido",
        "monto": float(row[3]),
        "monto_valido": 0 if anulado else float(row[3]),
        "fecha": row[4].strftime("%d/%m/%Y %H:%M") if row[4] else None,
        "descripcion": row[5] or "Sin descripción",
        "tipo_pago": row[6] if len(row) > 6 else None,
        "estado": estado,
        "anulado": anulado,
        "motivo_anulacion": row[8] if len(row) > 8 else None,
        "fecha_anulacion": row[9].strftime("%d/%m/%Y %H:%M") if len(row) > 9 and row[9] else None,
    }


def _formatear_egreso(row):
    return {
        "id": row[0],
        "concepto": row[1] or "Sin concepto",
        "monto": float(row[2] or 0),
        "fecha": row[3].strftime("%d/%m/%Y") if row[3] else None,
        "categoria": row[4] or "Otros",
        "notas": row[5] or "",
        "origen": row[6] if len(row) > 6 and row[6] else "manual",
    }


# 📊 Reporte general del sistema
def reporte_general_controller():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        (
            stats,
            estudiantes_por_curso,
            ingresos_mensuales,
            egresos_mensuales,
        ) = consultar_reporte_general(cursor)

        return {
            "estadisticas_generales": {
                "total_estudiantes": stats[0],
                "total_profesores": stats[1],
                "total_cursos": stats[2],
                "total_materias": stats[3],
                "total_ingresos": float(stats[4] or 0),
                "ingresos_hoy": float(stats[5] or 0),
                "total_egresos": float(stats[6] or 0),
                "egresos_hoy": float(stats[7] or 0),
                "balance_general": float((stats[4] or 0) - (stats[6] or 0)),
                "balance_hoy": float((stats[5] or 0) - (stats[7] or 0)),
            },
            "estudiantes_por_curso": [
                {"curso": row[0], "cantidad": row[1]}
                for row in estudiantes_por_curso
            ],
            "ingresos_mensuales": [
                {"mes": row[0], "total": float(row[1])}
                for row in ingresos_mensuales
            ],
            "egresos_mensuales": [
                {"mes": row[0], "total": float(row[1])}
                for row in egresos_mensuales
            ]
        }

    except Exception as e:
        print(f"Error en reporte_general_controller: {e}")
        return {
            "estadisticas_generales": {
                "total_estudiantes": 0,
                "total_profesores": 0,
                "total_cursos": 0,
                "total_materias": 0,
                "total_ingresos": 0,
                "ingresos_hoy": 0,
                "total_egresos": 0,
                "egresos_hoy": 0,
                "balance_general": 0,
                "balance_hoy": 0,
            },
            "estudiantes_por_curso": [],
            "ingresos_mensuales": [],
            "egresos_mensuales": []
        }
    finally:
        cursor.close()
        conn.close()

# 📊 Detalle de ingresos por mes
def reporte_ingresos_mes_controller(mes: str, limit=None, offset=0):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        total, resultados = consultar_ingresos_mes(cursor, mes, limit, offset)
        items = [_formatear_ingreso(row) for row in resultados]

        if limit is not None:
            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "items": items,
            }

        return items
    except Exception as e:
        print(f"Error en reporte_ingresos_mes_controller: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# 📊 Reporte de estado de cuenta por curso
def reporte_estado_cuenta_curso_controller(curso_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        tipos_list = obtener_tipos_pago(cursor)
        valor_por_tipo_en_curso = obtener_asignaciones_cobro_por_curso(cursor, curso_id)

        estudiantes = consultar_estudiantes_estado_cuenta_curso(cursor, curso_id)
        estudiante_ids = tuple(estudiante[0] for estudiante in estudiantes)
        _, _, pagos_aplicados_por_estudiante = obtener_pagos_por_concepto_estudiantes(
            cursor,
            estudiante_ids,
        )
        tiene_aplicaciones = tabla_pagos_aplicaciones_existe(cursor)

        pagos_concepto_rows, pagos_nombre_rows = (
            consultar_pagos_estado_cuenta_por_estudiantes(
                cursor,
                estudiante_ids,
            )
        )
        valores_por_estudiante = obtener_valores_personalizados_por_estudiantes(
            cursor,
            estudiante_ids,
        )
        pagos_otros_rows = consultar_otros_pagos_por_estudiantes(
            cursor,
            estudiante_ids,
            tiene_aplicaciones,
        )
        return construir_estado_cuenta_curso(
            estudiantes=estudiantes,
            tipos_pago=tipos_list,
            asignaciones_curso=valor_por_tipo_en_curso,
            pagos_concepto_rows=pagos_concepto_rows,
            pagos_nombre_rows=pagos_nombre_rows,
            pagos_aplicados_por_estudiante=pagos_aplicados_por_estudiante,
            valores_por_estudiante=valores_por_estudiante,
            pagos_otros_rows=pagos_otros_rows,
        )

    except Exception as e:
        print(f"Error en reporte_estado_cuenta_curso_controller: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# 📊 Detalle de ingresos por rango de fechas
def reporte_ingresos_rango_controller(fecha_inicio: str, fecha_fin: str, limit=None, offset=0):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        total, resultados = consultar_ingresos_rango(
            cursor,
            fecha_inicio,
            fecha_fin,
            limit,
            offset,
        )
        items = [_formatear_ingreso(row) for row in resultados]

        if limit is not None:
            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "items": items,
            }

        return items
    except Exception as e:
        print(f"Error en reporte_ingresos_rango_controller: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def reporte_egresos_rango_controller(fecha_inicio: str, fecha_fin: str, limit=None, offset=0):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        total, resultados = consultar_egresos_rango(
            cursor,
            fecha_inicio,
            fecha_fin,
            limit,
            offset,
        )
        items = [_formatear_egreso(row) for row in resultados]

        if limit is not None:
            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "items": items,
            }

        return items
    except Exception as e:
        print(f"Error en reporte_egresos_rango_controller: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

