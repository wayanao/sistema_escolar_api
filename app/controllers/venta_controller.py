from app.database import get_connection

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
        "detalles": detalles_por_venta.get(row[0], [])
    }

def obtener_ventas():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Obtener ventas
        cursor.execute('''
            SELECT v.id, e.nombre, e.apellido, v.fecha, v.tipo_venta, v.total, v.estado, v.notas, v.estudiante_id 
            FROM ventas v
            LEFT JOIN estudiantes e ON v.estudiante_id = e.id
            ORDER BY v.fecha DESC, v.id DESC
        ''')
        ventas_rows = cursor.fetchall()
        
        # Obtener todos los detalles
        cursor.execute('''
            SELECT vd.venta_id, i.nombre, vd.cantidad, vd.precio_unitario, vd.subtotal
            FROM ventas_detalle vd
            JOIN inventario i ON vd.inventario_id = i.id
        ''')
        detalles_rows = cursor.fetchall()
        
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

        cursor.execute(f'''
            SELECT COUNT(*)
            FROM ventas v
            LEFT JOIN estudiantes e ON v.estudiante_id = e.id
            {where_sql}
        ''', params)
        total = cursor.fetchone()[0]

        cursor.execute(f'''
            SELECT v.id, e.nombre, e.apellido, v.fecha, v.tipo_venta, v.total, v.estado, v.notas, v.estudiante_id
            FROM ventas v
            LEFT JOIN estudiantes e ON v.estudiante_id = e.id
            {where_sql}
            ORDER BY v.fecha DESC, v.id DESC
            LIMIT %s OFFSET %s
        ''', params + [limit, offset])
        ventas_rows = cursor.fetchall()

        if not ventas_rows:
            return {"total": total, "limit": limit, "offset": offset, "items": []}

        venta_ids = [v[0] for v in ventas_rows]
        cursor.execute('''
            SELECT vd.venta_id, i.nombre, vd.cantidad, vd.precio_unitario, vd.subtotal
            FROM ventas_detalle vd
            JOIN inventario i ON vd.inventario_id = i.id
            WHERE vd.venta_id = ANY(%s)
        ''', (venta_ids,))
        detalles_rows = cursor.fetchall()

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
        cursor.execute('''
            SELECT v.id, v.fecha, v.total, v.estado, v.notas, COALESCE(v.pagado, 0) 
            FROM ventas v
            WHERE v.estudiante_id = %s AND v.estado = 'Pendiente'
            ORDER BY v.fecha ASC
        ''', (estudiante_id,))
        ventas_rows = cursor.fetchall()
        
        # Obtener detalles para esas ventas
        if not ventas_rows:
            return []
            
        venta_ids = tuple([v[0] for v in ventas_rows])
        
        cursor.execute(f'''
            SELECT vd.venta_id, i.nombre, vd.cantidad, vd.precio_unitario, vd.subtotal
            FROM ventas_detalle vd
            JOIN inventario i ON vd.inventario_id = i.id
            WHERE vd.venta_id IN %s
        ''', (venta_ids,))
        detalles_rows = cursor.fetchall()
        
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

def crear_venta(datos):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        estado_inicial = "Pagado" if datos.tipo_venta == "Contado" else "Pendiente"
        
        cursor.execute(
            """INSERT INTO ventas (estudiante_id, tipo_venta, total, estado, notas) 
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (datos.estudiante_id, datos.tipo_venta, datos.total, estado_inicial, datos.notas)
        )
        venta_id = cursor.fetchone()[0]
        
        for det in datos.detalles:
            cursor.execute(
                """INSERT INTO ventas_detalle (venta_id, inventario_id, cantidad, precio_unitario, subtotal) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (venta_id, det.inventario_id, det.cantidad, det.precio_unitario, det.subtotal)
            )
            cursor.execute(
                "UPDATE inventario SET stock_actual = stock_actual - %s WHERE id = %s",
                (det.cantidad, det.inventario_id)
            )
            
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
        cursor.execute("DELETE FROM ventas WHERE id = %s", (venta_id,))
        conn.commit()
        return {"mensaje": "Venta eliminada"}
    finally:
        cursor.close()
        conn.close()
