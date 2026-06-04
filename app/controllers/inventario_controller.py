from app.database import get_connection

ESTADOS_INVENTARIO = {"activo", "inactivo"}
ESTADO_INVENTARIO_DEFAULT = "activo"


def _normalizar_estado(value):
    estado = str(value or ESTADO_INVENTARIO_DEFAULT).strip().lower()
    return estado if estado in ESTADOS_INVENTARIO else ESTADO_INVENTARIO_DEFAULT


def _agregar_filtro_estado(filtros, params, estado):
    estado_filtro = str(estado or ESTADO_INVENTARIO_DEFAULT).strip().lower()
    if estado_filtro == "todos":
        return

    filtros.append("COALESCE(LOWER(estado), 'activo') = %s")
    params.append(_normalizar_estado(estado_filtro))


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
        "utilidad_total_proyectada": utilidad_total,
        "estado": _normalizar_estado(row[5] if len(row) > 5 else ESTADO_INVENTARIO_DEFAULT),
    }

def obtener_inventario_controller(estado=ESTADO_INVENTARIO_DEFAULT):
    conn = get_connection()
    cursor = conn.cursor()

    filtros = []
    params = []
    _agregar_filtro_estado(filtros, params, estado)
    where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

    cursor.execute("""
        SELECT id, nombre, costo, precio_venta, stock_actual, COALESCE(LOWER(estado), 'activo') AS estado
        FROM inventario
        {where_sql}
        ORDER BY nombre
    """.format(where_sql=where_sql), params)
    resultado = cursor.fetchall()
    cursor.close()
    conn.close()

    return [_formatear_producto(row) for row in resultado]

def obtener_inventario_paginado_controller(
    limit=50,
    offset=0,
    busqueda=None,
    solo_con_stock=False,
    estado=ESTADO_INVENTARIO_DEFAULT,
):
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

        _agregar_filtro_estado(filtros, params, estado)

        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(f"""
            SELECT COUNT(*)
            FROM inventario
            {where_sql}
        """, params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT id, nombre, costo, precio_venta, stock_actual, COALESCE(LOWER(estado), 'activo') AS estado
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
        INSERT INTO inventario (nombre, costo, precio_venta, stock_actual, estado)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (
        producto.nombre,
        producto.costo,
        producto.precio_venta,
        producto.stock_actual,
        _normalizar_estado(producto.estado),
    ))
    
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
        SET nombre = %s, costo = %s, precio_venta = %s, stock_actual = %s, estado = %s
        WHERE id = %s
    """, (
        producto.nombre,
        producto.costo,
        producto.precio_venta,
        producto.stock_actual,
        _normalizar_estado(producto.estado),
        item_id,
    ))
    
    conn.commit()
    cursor.close()
    conn.close()

def eliminar_inventario_controller(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE inventario SET estado = 'inactivo' WHERE id = %s", (item_id,))
    conn.commit()
    cursor.close()
    conn.close()


def actualizar_estado_inventario_controller(item_id, estado):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        estado_normalizado = _normalizar_estado(estado)
        cursor.execute(
            """
            UPDATE inventario
            SET estado = %s
            WHERE id = %s
            RETURNING id, nombre, costo, precio_venta, stock_actual, COALESCE(LOWER(estado), 'activo') AS estado
            """,
            (estado_normalizado, item_id),
        )
        row = cursor.fetchone()
        if not row:
            return {"error": "Producto no encontrado"}

        conn.commit()
        return _formatear_producto(row)
    finally:
        cursor.close()
        conn.close()
