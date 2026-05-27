from app.database import get_connection
import datetime
from zoneinfo import ZoneInfo

from app.services.cobros import obtener_saldo_concepto

ZONA_HORARIA_LOCAL = ZoneInfo("America/Bogota")


def _calcular_total_pago(pago):
    metodos = getattr(pago, 'metodos', None)
    if metodos and isinstance(metodos, list) and len(metodos) > 0:
        return sum(float(metodo.monto or 0) for metodo in metodos)
    return float(getattr(pago, 'monto', 0) or 0)


def _formatear_tipo_pago(metodo):
    tipo = str(getattr(metodo, "tipo", "") or "").strip()
    nota = str(getattr(metodo, "nota", "") or "").strip()
    if nota:
        return f"{tipo} - {nota}"
    return tipo


def _fecha_pago_local(fecha_seleccionada=None):
    ahora_bogota = datetime.datetime.now(ZONA_HORARIA_LOCAL)
    if fecha_seleccionada:
        return datetime.datetime.combine(fecha_seleccionada, ahora_bogota.time()).replace(tzinfo=None)
    return ahora_bogota.replace(tzinfo=None)


def _formatear_pago(row):
    fecha = row[3]
    return {
        "pago_id": row[0],
        "estudiante_id": row[1],
        "monto": float(row[2]),
        "fecha": fecha.strftime("%d/%m/%Y %I:%M %p") if fecha else "",
        "descripcion": row[4] if len(row) > 4 else '',
        "tipo_pago": row[5] if len(row) > 5 else None
    }


def _obtener_saldo_venta(cursor, venta_id):
    cursor.execute("""
        SELECT total, COALESCE(pagado, 0), estado
        FROM ventas
        WHERE id = %s
    """, (venta_id,))
    venta = cursor.fetchone()
    if not venta:
        raise ValueError("El cargo de inventario seleccionado no existe.")

    total, pagado, estado = venta
    saldo = max(0.0, float(total or 0) - float(pagado or 0))
    if estado != "Pendiente" or saldo <= 0:
        raise ValueError("Este cargo de inventario ya no tiene saldo pendiente.")
    return saldo


def _obtener_saldo_concepto(cursor, estudiante_id, concepto):
    return obtener_saldo_concepto(cursor, estudiante_id, concepto)


def _validar_pago_no_excede_deuda(cursor, pago):
    monto_total = _calcular_total_pago(pago)
    if monto_total <= 0:
        raise ValueError("El monto del pago debe ser mayor a cero.")

    if getattr(pago, 'venta_id', None):
        saldo = _obtener_saldo_venta(cursor, pago.venta_id)
        if monto_total > saldo:
            raise ValueError(
                f"El monto a pagar (${monto_total:,.2f}) no puede ser mayor al saldo pendiente (${saldo:,.2f})."
            )
        return

    saldo = _obtener_saldo_concepto(cursor, pago.estudiante_id, getattr(pago, 'descripcion', None))
    if monto_total > saldo:
        raise ValueError(
            f"El monto a pagar (${monto_total:,.2f}) no puede ser mayor a la deuda pendiente (${saldo:,.2f})."
        )


# 🎯 Registrar pago
def registrar_pago_controller(pago):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        _validar_pago_no_excede_deuda(cursor, pago)
        fecha_registro = _fecha_pago_local(getattr(pago, "fecha", None))

        pago_ids = []
        metodos = getattr(pago, 'metodos', None)
        if metodos and isinstance(metodos, list) and len(metodos) > 0:
            for metodo in metodos:
                cursor.execute("""
                    INSERT INTO pagos (estudiante_id, monto, descripcion, fecha, tipo_pago)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (pago.estudiante_id, metodo.monto, getattr(pago, 'descripcion', ''), fecha_registro, _formatear_tipo_pago(metodo)))
                pago_id = cursor.fetchone()[0]
                pago_ids.append(pago_id)

                # Si se envía un venta_id, acumular abono a la venta (cargo de inventario)
                if getattr(pago, 'venta_id', None):
                    cursor.execute("""
                        UPDATE ventas SET pagado = COALESCE(pagado, 0) + %s 
                        WHERE id = %s RETURNING total, pagado
                    """, (metodo.monto, pago.venta_id))
                    venta = cursor.fetchone()
                    if venta:
                        total_venta, total_pagado = venta
                        if total_pagado >= total_venta:
                            cursor.execute("UPDATE ventas SET estado = 'Pagado' WHERE id = %s", (pago.venta_id,))
        else:
            # Caso compatibilidad: pago simple
            cursor.execute("""
                INSERT INTO pagos (estudiante_id, monto, descripcion, fecha, tipo_pago)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (pago.estudiante_id, pago.monto, getattr(pago, 'descripcion', ''), fecha_registro, getattr(pago, 'tipo_pago', None)))
            pago_id = cursor.fetchone()[0]
            pago_ids.append(pago_id)

            if getattr(pago, 'venta_id', None):
                cursor.execute("""
                    UPDATE ventas SET pagado = COALESCE(pagado, 0) + %s 
                    WHERE id = %s RETURNING total, pagado
                """, (pago.monto, pago.venta_id))
                venta = cursor.fetchone()
                if venta:
                    total_venta, total_pagado = venta
                    if total_pagado >= total_venta:
                        cursor.execute("UPDATE ventas SET estado = 'Pagado' WHERE id = %s", (pago.venta_id,))

        conn.commit()
        return pago_ids[0] if len(pago_ids) == 1 else pago_ids

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


# 🎯 Historial de pagos por estudiante
def historial_pagos_controller(estudiante_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            id, 
            estudiante_id,
            monto, 
            fecha,
            descripcion,
            tipo_pago
        FROM pagos
        WHERE estudiante_id = %s
        ORDER BY id DESC
    """, (estudiante_id,))

    resultado = cursor.fetchall()

    cursor.close()
    conn.close()

    return [_formatear_pago(row) for row in resultado]


def historial_pagos_paginado_controller(estudiante_id, limit=50, offset=0):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*)
            FROM pagos
            WHERE estudiante_id = %s
        """, (estudiante_id,))
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT
                id,
                estudiante_id,
                monto,
                fecha,
                descripcion,
                tipo_pago
            FROM pagos
            WHERE estudiante_id = %s
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """, (estudiante_id, limit, offset))
        resultado = cursor.fetchall()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_formatear_pago(row) for row in resultado]
        }
    finally:
        cursor.close()
        conn.close()
