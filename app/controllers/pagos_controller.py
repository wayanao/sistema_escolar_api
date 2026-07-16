from app.database import get_connection
import datetime
import re
from zoneinfo import ZoneInfo

from psycopg2 import IntegrityError

from app.services.cobros import obtener_conceptos_mensuales_estudiante, obtener_saldo_concepto

ZONA_HORARIA_LOCAL = ZoneInfo("America/Bogota")
VENTA_ID_PATTERN = re.compile(r"Cargo\s+#(\d+)", re.IGNORECASE)
MESES_ES = (
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
)


class MigracionPagosAdelantadosPendienteError(RuntimeError):
    pass


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


def _tabla_pagos_aplicaciones_existe(cursor):
    cursor.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = ANY (current_schemas(false))
          AND table_name = 'pagos_aplicaciones'
        """
    )
    return cursor.fetchone() is not None


def _exigir_tabla_pagos_aplicaciones(cursor):
    if not _tabla_pagos_aplicaciones_existe(cursor):
        raise MigracionPagosAdelantadosPendienteError(
            "La función de pagos adelantados requiere la migración "
            "20260716_pagos_adelantados.sql."
        )


def _periodos_programados(concepto, hoy):
    frecuencia = max(1, int(concepto.get("frecuencia_meses") or 1))
    mes_inicial = concepto.get("mes_inicial")
    periodos = []

    for mes in range(hoy.month + 1, 13):
        if mes_inicial:
            inicio = int(mes_inicial)
            if mes < inicio or (mes - inicio) % frecuencia != 0:
                continue
        elif (mes - (hoy.month + 1)) % frecuencia != 0:
            continue
        periodos.append(datetime.date(hoy.year, mes, 1))

    return periodos


def _etiqueta_periodo(periodo):
    return f"{MESES_ES[periodo.month - 1]} {periodo.year}"


def _periodos_disponibles(cursor, estudiante_id, concepto, hoy):
    cursor.execute(
        """
        SELECT pa.periodo
        FROM pagos_aplicaciones pa
        JOIN pagos p ON p.id = pa.pago_id
        WHERE pa.estudiante_id = %s
          AND pa.tipo_pago_id = %s
          AND pa.activo = TRUE
          AND COALESCE(p.estado, 'Pagado') <> 'Anulado'
        """,
        (estudiante_id, concepto["id"]),
    )
    ocupados = {row[0] for row in cursor.fetchall()}
    return [periodo for periodo in _periodos_programados(concepto, hoy) if periodo not in ocupados]


def _serializar_opcion_adelanto(cursor, estudiante_id, concepto, hoy):
    periodos = _periodos_disponibles(cursor, estudiante_id, concepto, hoy)
    return {
        "tipo_pago_id": concepto["id"],
        "concepto": concepto["nombre"],
        "valor_unitario": round(float(concepto["valor_unitario"]), 2),
        "valor_origen": concepto["valor_origen"],
        "periodos_disponibles": [
            {"periodo": periodo.isoformat(), "etiqueta": _etiqueta_periodo(periodo)}
            for periodo in periodos
        ],
        "max_meses": len(periodos),
    }


def obtener_opciones_adelanto_controller(estudiante_id, hoy=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _exigir_tabla_pagos_aplicaciones(cursor)
        fecha_referencia = hoy or datetime.datetime.now(ZONA_HORARIA_LOCAL).date()
        opciones = [
            _serializar_opcion_adelanto(cursor, estudiante_id, concepto, fecha_referencia)
            for concepto in obtener_conceptos_mensuales_estudiante(cursor, estudiante_id)
        ]
        return {"estudiante_id": estudiante_id, "opciones": opciones}
    finally:
        cursor.close()
        conn.close()


def registrar_pago_adelantado_controller(pago, hoy=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _exigir_tabla_pagos_aplicaciones(cursor)
        fecha_referencia = hoy or datetime.datetime.now(ZONA_HORARIA_LOCAL).date()
        conceptos = obtener_conceptos_mensuales_estudiante(cursor, pago.estudiante_id)
        concepto = next((item for item in conceptos if item["id"] == pago.tipo_pago_id), None)
        if not concepto:
            raise ValueError("El concepto no es mensual o no está asignado al estudiante.")

        disponibles = _periodos_disponibles(cursor, pago.estudiante_id, concepto, fecha_referencia)
        if pago.cantidad_meses > len(disponibles):
            raise ValueError("No hay suficientes meses disponibles para registrar este adelanto.")

        periodos = disponibles[:pago.cantidad_meses]
        valor_unitario = round(float(concepto["valor_unitario"]), 2)
        total = round(valor_unitario * len(periodos), 2)
        total_metodos = round(sum(float(metodo.monto or 0) for metodo in pago.metodos), 2)
        if total_metodos != total:
            raise ValueError(
                f"La suma de los métodos (${total_metodos:,.2f}) debe ser igual "
                f"al total del adelanto (${total:,.2f})."
            )

        etiquetas = [_etiqueta_periodo(periodo) for periodo in periodos]
        descripcion = f"{concepto['nombre']} · Pago adelantado: {', '.join(etiquetas)}"
        resumen_metodos = " + ".join(_formatear_tipo_pago(metodo) for metodo in pago.metodos)[:100]
        fecha_registro = _fecha_pago_local(getattr(pago, "fecha", None))

        cursor.execute(
            """
            INSERT INTO pagos (estudiante_id, monto, descripcion, fecha, tipo_pago)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (pago.estudiante_id, total, descripcion, fecha_registro, resumen_metodos),
        )
        pago_id = cursor.fetchone()[0]

        for periodo in periodos:
            cursor.execute(
                """
                INSERT INTO pagos_aplicaciones
                    (pago_id, estudiante_id, tipo_pago_id, periodo, monto)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (pago_id, pago.estudiante_id, concepto["id"], periodo, valor_unitario),
            )

        conn.commit()
        return {
            "mensaje": "Pago adelantado registrado correctamente",
            "pago_id": pago_id,
            "monto": total,
            "descripcion": descripcion,
            "periodos": [
                {"periodo": periodo.isoformat(), "etiqueta": etiqueta}
                for periodo, etiqueta in zip(periodos, etiquetas)
            ],
        }
    except IntegrityError as exc:
        conn.rollback()
        raise ValueError("Uno de los meses seleccionados ya tiene un pago adelantado.") from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def _formatear_pago(row):
    fecha = row[3]
    estado = row[6] if len(row) > 6 and row[6] else "Pagado"
    return {
        "pago_id": row[0],
        "estudiante_id": row[1],
        "monto": float(row[2]),
        "fecha": fecha.strftime("%d/%m/%Y %I:%M %p") if fecha else "",
        "descripcion": row[4] if len(row) > 4 else '',
        "tipo_pago": row[5] if len(row) > 5 else None,
        "estado": estado,
        "anulado": str(estado).strip().lower() == "anulado",
        "motivo_anulacion": row[7] if len(row) > 7 else None,
        "fecha_anulacion": row[8].strftime("%d/%m/%Y %I:%M %p") if len(row) > 8 and row[8] else None,
        "anulado_por": row[9] if len(row) > 9 else None
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
                    INSERT INTO pagos (estudiante_id, venta_id, monto, descripcion, fecha, tipo_pago)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (pago.estudiante_id, getattr(pago, 'venta_id', None), metodo.monto, getattr(pago, 'descripcion', ''), fecha_registro, _formatear_tipo_pago(metodo)))
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
                INSERT INTO pagos (estudiante_id, venta_id, monto, descripcion, fecha, tipo_pago)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (pago.estudiante_id, getattr(pago, 'venta_id', None), pago.monto, getattr(pago, 'descripcion', ''), fecha_registro, getattr(pago, 'tipo_pago', None)))
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
            tipo_pago,
            COALESCE(estado, 'Pagado') AS estado,
            motivo_anulacion,
            fecha_anulacion,
            anulado_por
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
                tipo_pago,
                COALESCE(estado, 'Pagado') AS estado,
                motivo_anulacion,
                fecha_anulacion,
                anulado_por
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


def anular_pago_controller(pago_id, motivo, admin_id):
    motivo_limpio = str(motivo or "").strip()
    if len(motivo_limpio) < 5:
        raise ValueError("Debes escribir un motivo de anulación de al menos 5 caracteres.")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, COALESCE(estado, 'Pagado'), monto, venta_id, descripcion
            FROM pagos
            WHERE id = %s
            FOR UPDATE
        """, (pago_id,))
        pago = cursor.fetchone()

        if not pago:
            raise ValueError("El pago no existe.")

        if str(pago[1]).strip().lower() == "anulado":
            raise ValueError("Este pago ya está anulado.")

        monto_pago = float(pago[2] or 0)
        venta_id = pago[3]
        descripcion = pago[4] or ""

        if venta_id is None:
            match = VENTA_ID_PATTERN.search(descripcion)
            if match:
                venta_id = int(match.group(1))
                cursor.execute(
                    "UPDATE pagos SET venta_id = %s WHERE id = %s",
                    (venta_id, pago_id),
                )

        if venta_id is not None:
            cursor.execute("""
                SELECT id, total, COALESCE(pagado, 0)
                FROM ventas
                WHERE id = %s
                FOR UPDATE
            """, (venta_id,))
            venta = cursor.fetchone()
            if not venta:
                raise ValueError("La venta asociada a este pago ya no existe.")

            total_venta = float(venta[1] or 0)
            pagado_actual = float(venta[2] or 0)
            nuevo_pagado = max(0.0, pagado_actual - monto_pago)
            nuevo_estado = "Pagado" if nuevo_pagado >= total_venta and total_venta > 0 else "Pendiente"

            cursor.execute("""
                UPDATE ventas
                SET pagado = %s,
                    estado = %s
                WHERE id = %s
            """, (nuevo_pagado, nuevo_estado, venta_id))

        if _tabla_pagos_aplicaciones_existe(cursor):
            cursor.execute(
                """
                UPDATE pagos_aplicaciones
                SET activo = FALSE
                WHERE pago_id = %s AND activo = TRUE
                """,
                (pago_id,),
            )

        cursor.execute("""
            UPDATE pagos
            SET estado = 'Anulado',
                motivo_anulacion = %s,
                fecha_anulacion = %s,
                anulado_por = %s
            WHERE id = %s
            RETURNING id
        """, (
            motivo_limpio,
            datetime.datetime.now(ZONA_HORARIA_LOCAL).replace(tzinfo=None),
            admin_id,
            pago_id,
        ))

        conn.commit()
        return {"mensaje": "Pago anulado correctamente", "pago_id": pago_id}
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
