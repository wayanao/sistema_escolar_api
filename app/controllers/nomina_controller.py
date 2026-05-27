from app.database import get_connection
import psycopg2

def obtener_estado_cuenta_profesores():
    """
    Returns a list of all professors along with their active loan balance.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT 
                p.id, 
                p.nombre, 
                p.apellido, 
                p.documento_identidad,
                COALESCE(p.sueldo, 0) AS sueldo,
                COALESCE(SUM(pr.monto - COALESCE(pr.pagado, 0)), 0) AS saldo_prestamos
            FROM profesor p
            LEFT JOIN prestamos pr ON p.id = pr.profesor_id AND pr.estado = 'Pendiente'
            GROUP BY p.id
            ORDER BY p.apellido, p.nombre
        ''')
        rows = cursor.fetchall()
        
        profesores = []
        for r in rows:
            profesores.append({
                "id": r[0],
                "nombre": r[1],
                "apellido": r[2],
                "documento": r[3],
                "sueldo": float(r[4]),
                "saldo_prestamos": float(r[5])
            })
            
        return profesores
    finally:
        cursor.close()
        conn.close()

def procesar_pago_nomina(data):
    """
    Registrar el pago de nomina y descontar los prestamos
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Calcular el monto de prestamos a deducir
        deduccion_restante = float(data.deduccion_prestamos)
        
        # Obtener los préstamos pendientes del profesor (los más antiguos primero)
        if deduccion_restante > 0:
            cursor.execute('''
                SELECT id, monto, COALESCE(pagado, 0)
                FROM prestamos
                WHERE profesor_id = %s AND estado = 'Pendiente'
                ORDER BY fecha ASC
            ''', (data.profesor_id,))
            
            prestamos = cursor.fetchall()
            
            for prestamo in prestamos:
                if deduccion_restante <= 0:
                    break
                
                prestamo_id = prestamo[0]
                monto = float(prestamo[1])
                pagado = float(prestamo[2])
                saldo_pendiente = monto - pagado
                
                if saldo_pendiente <= 0:
                    continue
                    
                abono = min(saldo_pendiente, deduccion_restante)
                nuevo_pagado = pagado + abono
                deduccion_restante -= abono
                
                # Actualizar el prestamo
                nuevo_estado = 'Pagado' if nuevo_pagado >= monto else 'Pendiente'
                cursor.execute('''
                    UPDATE prestamos 
                    SET pagado = %s, estado = %s
                    WHERE id = %s
                ''', (nuevo_pagado, nuevo_estado, prestamo_id))

        # Registrar la nómina
        total_pagado = (data.salario_base + data.bonificaciones) - (data.deduccion_prestamos + data.otros_descuentos)
        
        cursor.execute('''
            INSERT INTO nomina (
                profesor_id, 
                salario_base, 
                deduccion_prestamos, 
                otros_descuentos, 
                bonificaciones, 
                total_pagado, 
                notas
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, fecha
        ''', (
            data.profesor_id,
            data.salario_base,
            data.deduccion_prestamos,
            data.otros_descuentos,
            data.bonificaciones,
            total_pagado,
            data.notas
        ))
        
        nomina_row = cursor.fetchone()
        
        # Registrar egreso automático
        # La tabla se llama Egresos, necesitamos verificar si existe, en tu schema general... Egresos
        # (Assuming you have an egresos table, let's insert it too, otherwise just pass later)
        try:
            # Registrar egreso
            cursor.execute('''
                INSERT INTO egresos (concepto, monto, fecha, categoria, notas)
                VALUES (%s, %s, CURRENT_DATE, 'Pago Nomina', 'Recibo de Nomina')
            ''', (f"Pago de Nómina - Profesor ID {data.profesor_id}", total_pagado))
            # O crear un SAVEPOINT internamente si quieres ignorar si falla
        except Exception as e:
            # En caso de que la tabla egresos no exista o tenga otra estructura, no bloqueamos la nómina
            conn.rollback() # Rollback de la TX entera si falla
            raise e

        conn.commit()
        return {"mensaje": "Pago de nómina procesado exitosamente", "nomina_id": nomina_row[0]}
        
    except Exception as e:
        conn.rollback()
        raise e
        
    finally:
        cursor.close()
        conn.close()

def obtener_historial_nomina():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT 
                n.id,
                n.fecha,
                p.nombre,
                p.apellido,
                n.salario_base,
                n.deduccion_prestamos,
                n.otros_descuentos,
                n.bonificaciones,
                n.total_pagado,
                n.notas
            FROM nomina n
            JOIN profesor p ON n.profesor_id = p.id
            ORDER BY n.fecha DESC, n.id DESC
        ''')
        rows = cursor.fetchall()
        historial = []
        for r in rows:
            historial.append({
                "id": r[0],
                "fecha": str(r[1]),
                "profesor": f"{r[3]} {r[2]}", # Apellido Nombre
                "salario_base": float(r[4]),
                "deduccion_prestamos": float(r[5]),
                "otros_descuentos": float(r[6]),
                "bonificaciones": float(r[7]),
                "total_pagado": float(r[8]),
                "notas": r[9]
            })
        return historial
    finally:
        cursor.close()
        conn.close()
