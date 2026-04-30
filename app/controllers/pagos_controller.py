from app.database import get_connection
import datetime
from zoneinfo import ZoneInfo


CONCEPTOS_MATRICULA = {"matricula", "matrícula"}
CONCEPTOS_MENSUALIDAD = {"pension", "mensualidad", "pensión", "colegiatura"}
ZONA_HORARIA_LOCAL = ZoneInfo("America/Bogota")


def _normalizar(texto):
    return str(texto or "").strip().lower()


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
    concepto_normalizado = _normalizar(concepto)
    if not concepto_normalizado:
        raise ValueError("Debe seleccionar un concepto de pago.")

    cursor.execute("""
        SELECT c.matricula, c.mensualidad, c.meses,
               e.descuento_matricula, e.descuento_mensualidad
        FROM estudiantes e
        JOIN cursos c ON e.curso_id = c.id
        WHERE e.id = %s
    """, (estudiante_id,))
    est_data = cursor.fetchone()
    if not est_data:
        raise ValueError("El estudiante seleccionado no existe.")

    matricula, mensualidad, meses, desc_mat, desc_men = est_data

    cursor.execute("""
        SELECT nombre, valor
        FROM tipos_de_pagos
        WHERE LOWER(nombre) = %s
        LIMIT 1
    """, (concepto_normalizado,))
    tipo_pago = cursor.fetchone()
    if not tipo_pago:
        raise ValueError("El concepto seleccionado no existe.")

    nombre, valor = tipo_pago
    valor_cobrado = float(valor or 0)
    nombre_normalizado = _normalizar(nombre)

    if nombre_normalizado in CONCEPTOS_MATRICULA:
        base_mat = valor_cobrado if valor_cobrado > 0 else float(matricula or 0)
        valor_cobrado = base_mat - float(desc_mat or 0)
    elif nombre_normalizado in CONCEPTOS_MENSUALIDAD:
        base_men = valor_cobrado if valor_cobrado > 0 else float(mensualidad or 0)
        meses_totales = int(meses or 10)
        meses_transcurridos = min(datetime.datetime.now().month, meses_totales)
        valor_cobrado = (base_men - float(desc_men or 0)) * meses_transcurridos

    cursor.execute("""
        SELECT COALESCE(SUM(monto), 0)
        FROM pagos
        WHERE estudiante_id = %s
          AND (LOWER(COALESCE(descripcion, '')) = %s OR LOWER(COALESCE(tipo_pago, '')) = %s)
    """, (estudiante_id, concepto_normalizado, concepto_normalizado))
    pagado = float(cursor.fetchone()[0] or 0)

    return max(0.0, valor_cobrado - pagado)


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
