from app.database import get_connection
from app.repositories import ventas_repository
import datetime
from zoneinfo import ZoneInfo

ZONA_HORARIA_LOCAL = ZoneInfo("America/Bogota")

def _formatear_venta(row, detalles_por_venta):
    return {
        "id": row[0],
        "cliente": f"{row[2]} {row[1]}" if row[1] else "Público General",
        "fecha": str(row[3]),
        "tipo_venta": row[4],
        "total": float(row[5]),
        "estado": row[6],
        "notas": row[7],
        "estudiante_id": row[8],
        "motivo_anulacion": row[9] if len(row) > 9 else None,
        "fecha_anulacion": str(row[10]) if len(row) > 10 and row[10] else None,
        "detalles": detalles_por_venta.get(row[0], [])
    }

def obtener_ventas():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Obtener ventas
        ventas_rows = ventas_repository.leer_ventas_con_estudiante(cursor)

        # Obtener todos los detalles
        detalles_rows = ventas_repository.leer_detalles_de_todas_las_ventas(cursor)

        # Agrupar detalles por venta_id
        detalles_por_venta = {}
        for dr in detalles_rows:
            vid = dr[0]
            if vid not in detalles_por_venta:
                detalles_por_venta[vid] = []
            detalles_por_venta[vid].append({
                "producto": dr[1],
                "cantidad": dr[2],
                "precio_unitario": float(dr[3]),
                "subtotal": float(dr[4])
            })

        resultado = []
        for v in ventas_rows:
            resultado.append(_formatear_venta(v, detalles_por_venta))
        return resultado
    finally:
        cursor.close()
        conn.close()

def obtener_ventas_paginado(limit=50, offset=0, busqueda=None, estudiante_id=None, estado=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        filtros = []
        params = []

        if estudiante_id is not None:
            filtros.append("v.estudiante_id = %s")
            params.append(estudiante_id)

        if estado:
            filtros.append("v.estado = %s")
            params.append(estado)

        if busqueda:
            filtros.append("(LOWER(e.nombre) LIKE LOWER(%s) OR LOWER(e.apellido) LIKE LOWER(%s) OR LOWER(v.notas) LIKE LOWER(%s))")
            patron = f"%{busqueda}%"
            params.extend([patron, patron, patron])

        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        total = ventas_repository.contar_ventas(cursor, where_sql, params)

        ventas_rows = ventas_repository.leer_pagina_de_ventas(
            cursor, where_sql, params + [limit, offset]
        )

        if not ventas_rows:
            return {"total": total, "limit": limit, "offset": offset, "items": []}

        venta_ids = [v[0] for v in ventas_rows]
        detalles_rows = ventas_repository.leer_detalles_de_ventas(cursor, venta_ids)

        detalles_por_venta = {}
        for dr in detalles_rows:
            vid = dr[0]
            if vid not in detalles_por_venta:
                detalles_por_venta[vid] = []
            detalles_por_venta[vid].append({
                "producto": dr[1],
                "cantidad": dr[2],
                "precio_unitario": float(dr[3]),
                "subtotal": float(dr[4])
            })

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_formatear_venta(v, detalles_por_venta) for v in ventas_rows]
        }
    finally:
        cursor.close()
        conn.close()

def obtener_ventas_pendientes(estudiante_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Obtener ventas pendientes del estudiante
        ventas_rows = ventas_repository.leer_ventas_pendientes_de_estudiante(
            cursor, estudiante_id
        )

        # Obtener detalles para esas ventas
        if not ventas_rows:
            return []

        venta_ids = tuple([v[0] for v in ventas_rows])

        detalles_rows = ventas_repository.leer_detalles_de_ventas_en(cursor, venta_ids)

        # Agrupar detalles por venta_id
        detalles_por_venta = {}
        for dr in detalles_rows:
            vid = dr[0]
            if vid not in detalles_por_venta:
                detalles_por_venta[vid] = []
            detalles_por_venta[vid].append({
                "producto": dr[1],
                "cantidad": dr[2],
                "subtotal": float(dr[4])
            })

        resultado = []
        for v in ventas_rows:
            # Crear un string descriptivo con los productos
            detalles = detalles_por_venta.get(v[0], [])
            desc_productos = ", ".join([f"{d['cantidad']}x {d['producto']}" for d in detalles])

            saldo_pendiente = float(v[2]) - float(v[5])

            resultado.append({
                "id": v[0],
                "fecha": str(v[1]),
                "total": saldo_pendiente,
                "estado": v[3],
                "descripcion": f"Abono a Cargo #{v[0]} ({desc_productos})" if float(v[5]) > 0 else f"Cargo de Inventario #{v[0]}: {desc_productos}"
            })
        return resultado
    finally:
        cursor.close()
        conn.close()


def validar_producto_vendible(cursor, inventario_id, cantidad):
    if int(cantidad or 0) <= 0:
        raise ValueError("La cantidad de cada producto debe ser mayor a cero.")

    producto = ventas_repository.leer_producto_para_vender(cursor, inventario_id)

    if not producto:
        raise ValueError("Uno de los productos seleccionados no existe.")

    nombre, stock_actual, estado = producto
    if estado != "activo":
        raise ValueError(f"El producto {nombre} está inactivo y no se puede vender.")

    if int(stock_actual or 0) < int(cantidad or 0):
        raise ValueError(f"No hay stock suficiente para {nombre}.")


def crear_venta(datos):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        estado_inicial = "Pagado" if datos.tipo_venta == "Contado" else "Pendiente"

        cantidades_por_producto = {}
        for det in datos.detalles:
            cantidades_por_producto[det.inventario_id] = (
                cantidades_por_producto.get(det.inventario_id, 0) + int(det.cantidad or 0)
            )

        for inventario_id, cantidad in cantidades_por_producto.items():
            validar_producto_vendible(cursor, inventario_id, cantidad)

        venta_id = ventas_repository.insertar_venta(
            cursor,
            datos.estudiante_id,
            datos.tipo_venta,
            datos.total,
            estado_inicial,
            datos.notas,
        )

        for det in datos.detalles:
            ventas_repository.insertar_detalle_de_venta(
                cursor,
                venta_id,
                det.inventario_id,
                det.cantidad,
                det.precio_unitario,
                det.subtotal,
            )
            ventas_repository.descontar_stock(cursor, det.cantidad, det.inventario_id)

        conn.commit()
        return {"id": venta_id, "mensaje": "Venta exitosa registrada!"}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def eliminar_venta(venta_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Recuperar stock antes de eliminar los detalles indirectamente (si quisieramos).
        # Por simplicidad ahora solo lo eliminamos y perdemos el track de reponer devoluciones automáticamente.
        ventas_repository.borrar_venta(cursor, venta_id)
        conn.commit()
        return {"mensaje": "Venta eliminada"}
    finally:
        cursor.close()
        conn.close()


def anular_venta(venta_id, motivo, admin_id):
    motivo_limpio = str(motivo or "").strip()
    if len(motivo_limpio) < 5:
        raise ValueError("Debes escribir un motivo de anulación de al menos 5 caracteres.")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        venta = ventas_repository.leer_venta_y_estado_para_anular(cursor, venta_id)

        if not venta:
            raise ValueError("La venta no existe.")

        if str(venta[1]).strip().lower() == "anulada":
            raise ValueError("Esta venta ya está anulada.")

        detalles = ventas_repository.leer_detalles_para_reponer_stock(cursor, venta_id)

        for inventario_id, cantidad in detalles:
            ventas_repository.reponer_stock(cursor, cantidad, inventario_id)

        fecha_anulacion = datetime.datetime.now(ZONA_HORARIA_LOCAL).replace(tzinfo=None)

        ventas_repository.anular_pagos_de_la_venta(
            cursor,
            f"Venta anulada: {motivo_limpio}",
            fecha_anulacion,
            admin_id,
            venta_id,
            f"%Cargo #{venta_id}%",
        )

        ventas_repository.marcar_venta_anulada(
            cursor, motivo_limpio, fecha_anulacion, admin_id, venta_id
        )

        conn.commit()
        return {"mensaje": "Venta anulada correctamente", "venta_id": venta_id}
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
