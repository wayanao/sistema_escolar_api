from app.database import get_connection

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
            resultado.append({
                "id": v[0], 
                "cliente": f"{v[2]} {v[1]}" if v[1] else "Público General",
                "fecha": str(v[3]), 
                "tipo_venta": v[4],
                "total": float(v[5]),
                "estado": v[6],
                "notas": v[7],
                "estudiante_id": v[8],
                "detalles": detalles_por_venta.get(v[0], [])
            })
        return resultado
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