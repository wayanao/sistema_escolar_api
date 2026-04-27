from app.database import get_connection

def crear_tipo_pago(nombre, valor=0):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO tipos_de_pagos (nombre, valor) VALUES (%s, %s) RETURNING id', (nombre, valor))
        data = cursor.fetchone()[0]
        conn.commit()
        return {'id': data, 'nombre': nombre, 'valor': valor}
    except Exception as e:
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def listar_tipos_pagos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nombre, valor FROM tipos_de_pagos ORDER BY nombre')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{'id': r[0], 'nombre': r[1], 'valor': float(r[2]) if r[2] is not None else 0} for r in rows]

def actualizar_tipo_pago(id, nombre, valor=0):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE tipos_de_pagos SET nombre = %s, valor = %s WHERE id = %s RETURNING id', (nombre, valor, id))
        if cursor.fetchone():
            conn.commit()
            return True
        return False
    except Exception as e:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def eliminar_tipo_pago(id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM tipos_de_pagos WHERE id = %s RETURNING id', (id,))
        if cursor.fetchone():
            conn.commit()
            return True
        return False
    except Exception as e:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()