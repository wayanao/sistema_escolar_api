from app.database import get_connection

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

    data = []
    for row in resultado:
        cost = float(row[2])
        precio = float(row[3])
        stock = int(row[4])
        utilidad_unitaria = precio - cost
        utilidad_total = utilidad_unitaria * stock
        data.append({
            "id": row[0],
            "nombre": row[1],
            "costo": cost,
            "precio_venta": precio,
            "stock_actual": stock,
            "margen_utilidad": round(((precio - cost) / precio * 100), 2) if precio > 0 else 0,
            "utilidad_unitaria": utilidad_unitaria,
            "utilidad_total_proyectada": utilidad_total
        })
    return data

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
