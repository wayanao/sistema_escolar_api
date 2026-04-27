from app.database import get_connection
from psycopg2.extras import RealDictCursor

def guardar_boletin_controller(data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO boletin_cabecera (estudiante_id, asignacion_id, periodo, definitiva)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (estudiante_id, asignacion_id, periodo) 
            DO UPDATE SET definitiva = EXCLUDED.definitiva
            RETURNING id
        """, (data.estudiante_id, data.asignacion_id, data.periodo, data.definitiva))
        
        boletin_id = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM boletin_detalles WHERE boletin_id = %s", (boletin_id,))
        
        for det in data.detalles:
            cursor.execute("""
                INSERT INTO boletin_detalles (boletin_id, nota, observacion)
                VALUES (%s, %s, %s)
            """, (boletin_id, det.nota, det.observacion))
            
        conn.commit()
        return {"mensaje": "Boletín guardado exitosamente"}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def obtener_notas_planilla_controller(asignacion_id: int, periodo: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT e.id as estudiante_id, e.nombre, e.apellido, nd.descripcion as tipo_nota, nd.nota
            FROM estudiantes e
            JOIN asignaciones a ON e.curso_id = a.curso_id
            LEFT JOIN notas_detalle nd ON e.id = nd.estudiante_id AND nd.asignacion_id = a.id AND nd.periodo = %s
            WHERE a.id = %s
            ORDER BY e.apellido, e.nombre, nd.id
        """, (periodo, asignacion_id))
        
        resultado = cursor.fetchall()
        
        estudiantes_dict = {}
        for row in resultado:
            est_id = row[0]
            if est_id not in estudiantes_dict:
                estudiantes_dict[est_id] = {
                    "estudiante_id": est_id,
                    "nombre": f"{row[1]} {row[2]}",
                    "notas": []
                }
            if row[3] is not None and row[4] is not None:
                estudiantes_dict[est_id]["notas"].append({
                    "tipo_nota": row[3],
                    "valor": float(row[4])
                })
                
        return list(estudiantes_dict.values())
    finally:
        cursor.close()
        conn.close()
def obtener_boletin_admin_controller(estudiante_id: int, periodo: int):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('''
            SELECT 
                m.id as materia_id,
                m.nombre AS materia,
                p.nombre AS profesor_nombre,
                p.apellido AS profesor_apellido,
                bc.definitiva,
                bc.id as boletin_id
            FROM estudiantes e
            JOIN asignaciones asig ON e.curso_id = asig.curso_id
            JOIN materias m ON asig.materia_id = m.id
            JOIN profesor p ON asig.profesor_id = p.id
            LEFT JOIN boletin_cabecera bc ON bc.asignacion_id = asig.id AND bc.estudiante_id = e.id
            WHERE e.id = %s
        ''', (estudiante_id,)) 
        materias_res = cur.fetchall()
        
        boletin_ids = [row['boletin_id'] for row in materias_res if row['boletin_id'] is not None]
        detalles_por_boletin = {}
        if boletin_ids:
            cur.execute('''
                SELECT 
                bd.boletin_id, 
                bd.nota, 
                bd.observacion,
                bc.periodo
                FROM boletin_detalles bd
                JOIN boletin_cabecera bc ON bd.boletin_id = bc.id
                WHERE bd.boletin_id = ANY(%s)
            ''', (boletin_ids,))
            for det in cur.fetchall():
                bid = det['boletin_id']
                if bid not in detalles_por_boletin:
                    detalles_por_boletin[bid] = []
                detalles_por_boletin[bid].append({
                    'nota': float(det['nota']) if det['nota'] is not None else None,
                    'observacion': det['observacion'],
                    'periodo': det['periodo']  # 🔥 clave
                })
                
        cur.execute('''
            SELECT e.nombre as estudiante_nombre, e.apellido as estudiante_apellido, c.nombre as curso_nombre
            FROM estudiantes e
            LEFT JOIN cursos c ON e.curso_id = c.id
            WHERE e.id = %s
        ''', (estudiante_id,))
        est_info = cur.fetchone()
        
        if not est_info:
            return None
                
        resultado = {
            'estudiante_id': estudiante_id,
            'estudiante_nombre': est_info['estudiante_nombre'],
            'estudiante_apellido': est_info['estudiante_apellido'],
            'curso': est_info['curso_nombre'],
            'periodo': periodo,
            'materias': []
        }
        
        for row in materias_res:
            mat_info = {
                'materia_id': row['materia_id'],
                'materia': row['materia'],
                'profesor_nombre': row['profesor_nombre'],
                'profesor_apellido': row['profesor_apellido'],
                'definitiva': float(row['definitiva']) if row['definitiva'] is not None else None,
                'detalles': detalles_por_boletin.get(row['boletin_id'], []) if row['boletin_id'] else []
            }
            resultado['materias'].append(mat_info)
            
        return resultado
    finally:
        conn.close()

