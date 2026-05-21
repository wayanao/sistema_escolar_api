from app.database import get_connection

def _formatear_producto(row):
    cost = float(row[2])
    precio = float(row[3])
    stock = int(row[4])
    utilidad_unitaria = precio - cost
    utilidad_total = utilidad_unitaria * stock
    return {
        "id": row[0],
        "nombre": row[1],
        "costo": cost,
        "precio_venta": precio,
        "stock_actual": stock,
        "margen_utilidad": round(((precio - cost) / precio * 100), 2) if precio > 0 else 0,
        "utilidad_unitaria": utilidad_unitaria,
        "utilidad_total_proyectada": utilidad_total
    }

def obtener_inventario_controller():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre, costo, precio_venta, stock_actual 
        FROM inventario ORDER BY nombre
    """)
    resultado = cursor.fetchall()
    cursor.close()
    conn.close()

    return [_formatear_producto(row) for row in resultado]

def obtener_inventario_paginado_controller(limit=50, offset=0, busqueda=None, solo_con_stock=False):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        filtros = []
        params = []

        if busqueda:
            filtros.append("LOWER(nombre) LIKE LOWER(%s)")
            params.append(f"%{busqueda}%")

        if solo_con_stock:
            filtros.append("stock_actual > 0")

        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(f"""
            SELECT COUNT(*)
            FROM inventario
            {where_sql}
        """, params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT id, nombre, costo, precio_venta, stock_actual
            FROM inventario
            {where_sql}
            ORDER BY nombre
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        resultado = cursor.fetchall()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_formatear_producto(row) for row in resultado]
        }
    finally:
        cursor.close()
        conn.close()

def crear_inventario_controller(producto):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO inventario (nombre, costo, precio_venta, stock_actual)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (producto.nombre, producto.costo, producto.precio_venta, producto.stock_actual))
    
    nuevo_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return nuevo_id

def actualizar_inventario_controller(item_id, producto):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE inventario 
        SET nombre = %s, costo = %s, precio_venta = %s, stock_actual = %s 
        WHERE id = %s
    """, (producto.nombre, producto.costo, producto.precio_venta, producto.stock_actual, item_id))
    
    conn.commit()
    cursor.close()
    conn.close()

def eliminar_inventario_controller(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventario WHERE id = %s", (item_id,))
    conn.commit()
    cursor.close()
    conn.close()
