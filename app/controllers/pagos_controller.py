from app.database import get_connection


# 🎯 Registrar pago
def registrar_pago_controller(pago):

    conn = get_connection()
    cursor = conn.cursor()


    pago_ids = []
    metodos = getattr(pago, 'metodos', None)
    if metodos and isinstance(metodos, list) and len(metodos) > 0:
        for metodo in metodos:
            if pago.fecha:
                cursor.execute("""
                    INSERT INTO pagos (estudiante_id, monto, descripcion, fecha, tipo_pago)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (pago.estudiante_id, metodo.monto, getattr(pago, 'descripcion', ''), pago.fecha, metodo.tipo))
            else:
                cursor.execute("""
                    INSERT INTO pagos (estudiante_id, monto, descripcion, tipo_pago)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (pago.estudiante_id, metodo.monto, getattr(pago, 'descripcion', ''), metodo.tipo))
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
        if pago.fecha:
            cursor.execute("""
                INSERT INTO pagos (estudiante_id, monto, descripcion, fecha, tipo_pago)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (pago.estudiante_id, pago.monto, getattr(pago, 'descripcion', ''), pago.fecha, getattr(pago, 'tipo_pago', None)))
        else:
            cursor.execute("""
                INSERT INTO pagos (estudiante_id, monto, descripcion, tipo_pago)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (pago.estudiante_id, pago.monto, getattr(pago, 'descripcion', ''), getattr(pago, 'tipo_pago', None)))
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
    cursor.close()
    conn.close()

    return pago_ids[0] if len(pago_ids) == 1 else pago_ids


# 🎯 Historial de pagos por estudiante
def historial_pagos_controller(estudiante_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            id, 
            estudiante_id,
            monto, 
            fecha AT TIME ZONE 'UTC' AT TIME ZONE 'America/Bogota',
            descripcion,
            tipo_pago
        FROM pagos
        WHERE estudiante_id = %s
        ORDER BY id DESC
    """, (estudiante_id,))

    resultado = cursor.fetchall()

    cursor.close()
    conn.close()

    data = []

    for row in resultado:
        data.append({
            "pago_id": row[0],
            "estudiante_id": row[1],
            "monto": float(row[2]),
            "fecha": row[3].strftime("%d/%m/%Y %I:%M %p"),
            "descripcion": row[4] if len(row) > 4 else '',
            "tipo_pago": row[5] if len(row) > 5 else None
        })

    return data
