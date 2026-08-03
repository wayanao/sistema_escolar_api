from app.database import get_connection
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor
from psycopg2.extras import RealDictCursor

def guardar_boletin_controller(data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, data.asignacion_id)
        tipo_evaluacion = getattr(data, "tipo_evaluacion", "numerica") or "numerica"
        cursor.execute("""
            INSERT INTO boletin_cabecera (estudiante_id, asignacion_id, periodo, definitiva)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (estudiante_id, asignacion_id, periodo) 
            DO UPDATE SET definitiva = EXCLUDED.definitiva
            RETURNING id
        """, (data.estudiante_id, asignacion_id, data.periodo, data.definitiva))
        
        boletin_id = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM boletin_detalles WHERE boletin_id = %s", (boletin_id,))
        
        for det in data.detalles:
            cursor.execute("""
                INSERT INTO boletin_detalles (
                    boletin_id,
                    nota,
                    observacion,
                    tipo_evaluacion,
                    valoracion
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                boletin_id,
                det.nota,
                det.observacion,
                getattr(det, "tipo_evaluacion", tipo_evaluacion) or tipo_evaluacion,
                getattr(det, "valoracion", None),
            ))
            
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
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)
        cursor.execute("""
            SELECT e.id as estudiante_id, e.nombre, e.apellido, nd.descripcion as tipo_nota, nd.nota
            FROM estudiantes e
            JOIN asignaciones a ON e.curso_id = a.curso_id
            LEFT JOIN notas_detalle nd ON e.id = nd.estudiante_id AND nd.asignacion_id = a.id AND nd.periodo = %s
            WHERE a.id = %s
              AND COALESCE(LOWER(e.estado), 'activo') = 'activo'
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
def obtener_boletin_para_profesor_controller(asignacion_id: int, periodo: int):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)
        cursor.execute("""
            SELECT e.id as estudiante_id, e.nombre, e.apellido,
                   nd.descripcion as tipo_nota,
                   nd.nota,
                   COALESCE(nd.tipo_evaluacion, 'numerica') AS tipo_evaluacion,
                   nd.valoracion
            FROM estudiantes e
            JOIN asignaciones a ON e.curso_id = a.curso_id
            LEFT JOIN notas_detalle nd ON e.id = nd.estudiante_id
                AND nd.asignacion_id = a.id AND nd.periodo = %s
            WHERE a.id = %s
              AND COALESCE(LOWER(e.estado), 'activo') = 'activo'
            ORDER BY e.apellido, e.nombre, nd.id
        """, (periodo, asignacion_id))

        estudiantes_dict = {}
        for row in cursor.fetchall():
            est_id = row['estudiante_id']
            if est_id not in estudiantes_dict:
                estudiantes_dict[est_id] = {
                    "estudiante_id": est_id,
                    "nombre": f"{row['nombre']} {row['apellido']}",
                    "notas": []
                }
            if row['tipo_nota'] is not None and row['nota'] is not None:
                estudiantes_dict[est_id]["notas"].append({
                    "tipo_nota": row['tipo_nota'],
                    "valor": float(row['nota']),
                    "tipo_evaluacion": row['tipo_evaluacion'] or "numerica",
                    "valoracion": row['valoracion'],
                    "observacion_guardada": ""
                })
            elif row['tipo_nota'] is not None and row['valoracion'] is not None:
                estudiantes_dict[est_id]["notas"].append({
                    "tipo_nota": row['tipo_nota'],
                    "valor": None,
                    "tipo_evaluacion": row['tipo_evaluacion'] or "desarrollo",
                    "valoracion": row['valoracion'],
                    "observacion_guardada": ""
                })

        est_ids = list(estudiantes_dict.keys())
        if est_ids:
            cursor.execute("""
                SELECT
                    bc.estudiante_id,
                    bc.definitiva,
                    bd.nota,
                    bd.observacion,
                    COALESCE(bd.tipo_evaluacion, 'numerica') AS tipo_evaluacion,
                    bd.valoracion
                FROM boletin_cabecera bc
                JOIN boletin_detalles bd ON bd.boletin_id = bc.id
                WHERE bc.asignacion_id = %s AND bc.periodo = %s
                    AND bc.estudiante_id = ANY(%s)
                ORDER BY bc.estudiante_id, bd.id
            """, (asignacion_id, periodo, est_ids))

            saved_by_student = {}
            for row in cursor.fetchall():
                est_id = row['estudiante_id']
                if est_id not in saved_by_student:
                    saved_by_student[est_id] = {
                        'observaciones': []
                    }
                saved_by_student[est_id]['observaciones'].append({
                    'observacion': row['observacion'] or '',
                })

            for est_id, est_data in estudiantes_dict.items():
                if est_id in saved_by_student:
                    saved = saved_by_student[est_id]
                    for i, nota in enumerate(est_data['notas']):
                        if i < len(saved['observaciones']):
                            saved_det = saved['observaciones'][i]
                            nota['observacion_guardada'] = saved_det['observacion']

        return list(estudiantes_dict.values())
    finally:
        cursor.close()
        conn.close()

def obtener_boletin_admin_controller(estudiante_id: int, periodo: int):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('''
            WITH asignaciones_academicas AS (
                SELECT DISTINCT ON (COALESCE(a.asignacion_academica_id, a.id))
                    COALESCE(a.asignacion_academica_id, a.id) AS id,
                    a.curso_id,
                    a.materia_id,
                    a.profesor_id,
                    COALESCE(a.orden_boletin, 100) AS orden_boletin
                FROM asignaciones a
                WHERE a.activo = TRUE
                ORDER BY COALESCE(a.asignacion_academica_id, a.id), COALESCE(a.orden_boletin, 100), a.id
            )
            SELECT 
                asig.id as asignacion_id,
                m.id as materia_id,
                m.nombre AS materia,
                p.nombre AS profesor_nombre,
                p.apellido AS profesor_apellido,
                COALESCE(NULLIF(bc.definitiva, 0), nd_prom.promedio_numerico) AS definitiva,
                bc.id as boletin_id,
                asig.orden_boletin
            FROM estudiantes e
            JOIN asignaciones_academicas asig ON e.curso_id = asig.curso_id
            JOIN materias m ON asig.materia_id = m.id
            JOIN profesor p ON asig.profesor_id = p.id
            LEFT JOIN boletin_cabecera bc ON bc.asignacion_id = asig.id
                AND bc.estudiante_id = e.id
                AND bc.periodo = %s
            LEFT JOIN LATERAL (
                SELECT AVG(nd.nota) AS promedio_numerico
                FROM notas_detalle nd
                WHERE nd.estudiante_id = e.id
                  AND nd.asignacion_id = asig.id
                  AND nd.periodo = %s
                  AND COALESCE(nd.tipo_evaluacion, 'numerica') <> 'desarrollo'
                  AND nd.nota > 0
            ) nd_prom ON TRUE
            WHERE e.id = %s
            ORDER BY asig.orden_boletin, m.nombre
        ''', (periodo, periodo, estudiante_id))
        materias_res = cur.fetchall()
        
        asignacion_ids = [row['asignacion_id'] for row in materias_res]
        detalles_por_asignacion = {}
        if asignacion_ids:
            cur.execute('''
                SELECT
                    bc.asignacion_id,
                    bc.periodo,
                    bd.nota,
                    COALESCE(bd.tipo_evaluacion, 'numerica') AS tipo_evaluacion,
                    bd.valoracion,
                    CASE WHEN bc.periodo = %s THEN bd.observacion ELSE NULL END AS observacion,
                    ROW_NUMBER() OVER (
                        PARTITION BY bc.asignacion_id, bc.periodo
                        ORDER BY bd.id
                    ) AS detalle_idx
                FROM boletin_cabecera bc
                JOIN boletin_detalles bd ON bd.boletin_id = bc.id
                WHERE bc.estudiante_id = %s
                    AND bc.asignacion_id = ANY(%s)
                    AND bc.periodo BETWEEN 1 AND 4
                ORDER BY bc.asignacion_id, detalle_idx, bc.periodo
            ''', (periodo, estudiante_id, asignacion_ids))

            for det in cur.fetchall():
                asignacion_id = det['asignacion_id']
                detalle_idx = det['detalle_idx']
                if asignacion_id not in detalles_por_asignacion:
                    detalles_por_asignacion[asignacion_id] = {}
                if detalle_idx not in detalles_por_asignacion[asignacion_id]:
                    detalles_por_asignacion[asignacion_id][detalle_idx] = {
                        'observacion': '',
                        'tipos_por_periodo': {},
                        'notas_por_periodo': {},
                        'valoraciones_por_periodo': {},
                    }

                detalle = detalles_por_asignacion[asignacion_id][detalle_idx]
                if det['observacion']:
                    detalle['observacion'] = det['observacion']
                if det['tipo_evaluacion']:
                    detalle['tipos_por_periodo'][str(det['periodo'])] = det['tipo_evaluacion']
                if det['nota'] is not None and float(det['nota']) > 0:
                    detalle['notas_por_periodo'][str(det['periodo'])] = float(det['nota'])
                if det['valoracion']:
                    detalle['valoraciones_por_periodo'][str(det['periodo'])] = det['valoracion']
                
        cur.execute('''
            SELECT e.nombre as estudiante_nombre, e.apellido as estudiante_apellido, c.nombre as curso_nombre
            FROM estudiantes e
            LEFT JOIN cursos c ON e.curso_id = c.id
            WHERE e.id = %s
        ''', (estudiante_id,))
        est_info = cur.fetchone()

        if not est_info:
            return None

        # Puesto del estudiante en el curso para el periodo (solo numericas).
        # Promedia las definitivas no nulas por estudiante y rankea descendente.
        cur.execute('''
            WITH promedios AS (
                SELECT
                    bc.estudiante_id,
                    AVG(bc.definitiva) AS promedio
                FROM boletin_cabecera bc
                JOIN estudiantes e ON e.id = bc.estudiante_id
                WHERE e.curso_id = (SELECT curso_id FROM estudiantes WHERE id = %s)
                  AND bc.periodo = %s
                  AND bc.definitiva IS NOT NULL
                GROUP BY bc.estudiante_id
            ),
            ranked AS (
                SELECT
                    estudiante_id,
                    promedio,
                    RANK() OVER (ORDER BY promedio DESC) AS puesto
                FROM promedios
            )
            SELECT
                (SELECT puesto FROM ranked WHERE estudiante_id = %s) AS puesto,
                (SELECT COUNT(*) FROM promedios) AS total
        ''', (estudiante_id, periodo, estudiante_id))
        ranking_row = cur.fetchone() or {}

        resultado = {
            'estudiante_id': estudiante_id,
            'estudiante_nombre': est_info['estudiante_nombre'],
            'estudiante_apellido': est_info['estudiante_apellido'],
            'curso': est_info['curso_nombre'],
            'periodo': periodo,
            'puesto': ranking_row.get('puesto'),
            'total_estudiantes': ranking_row.get('total') or 0,
            'materias': []
        }
        
        for row in materias_res:
            detalles_dict = detalles_por_asignacion.get(row['asignacion_id'], {})
            detalles = []
            for detalle_idx in sorted(detalles_dict):
                detalle = detalles_dict[detalle_idx]
                periodo_key = str(periodo)
                nota_actual = detalle['notas_por_periodo'].get(periodo_key)
                tipo_actual = detalle['tipos_por_periodo'].get(periodo_key)
                if not tipo_actual:
                    tipo_actual = "desarrollo" if detalle['valoraciones_por_periodo'].get(periodo_key) else "numerica"
                detalles.append({
                    'nota': nota_actual,
                    'periodo': periodo,
                    'observacion': detalle['observacion'],
                    'tipo_evaluacion': tipo_actual,
                    'notas_por_periodo': detalle['notas_por_periodo'],
                    'valoraciones_por_periodo': detalle['valoraciones_por_periodo'],
                })

            mat_info = {
                'asignacion_id': row['asignacion_id'],
                'materia_id': row['materia_id'],
                'materia': row['materia'],
                'profesor_nombre': row['profesor_nombre'],
                'profesor_apellido': row['profesor_apellido'],
                'definitiva': float(row['definitiva']) if row['definitiva'] is not None else None,
                'boletin_id': row['boletin_id'],
                'orden_boletin': row['orden_boletin'],
                'detalles': detalles
            }
            resultado['materias'].append(mat_info)
            
        return resultado
    finally:
        conn.close()


def obtener_reporte_parcial_admin_controller(estudiante_id: int, periodo: int):
    """Construye una fotografía de la planilla vigente, sin usar el boletín enviado."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute('''
            SELECT
                e.nombre AS estudiante_nombre,
                e.apellido AS estudiante_apellido,
                c.nombre AS curso_nombre
            FROM estudiantes e
            LEFT JOIN cursos c ON c.id = e.curso_id
            WHERE e.id = %s
        ''', (estudiante_id,))
        est_info = cur.fetchone()
        if not est_info:
            return None

        cur.execute('''
            WITH asignaciones_academicas AS (
                SELECT DISTINCT ON (COALESCE(a.asignacion_academica_id, a.id))
                    COALESCE(a.asignacion_academica_id, a.id) AS id,
                    a.curso_id,
                    a.materia_id,
                    a.profesor_id,
                    COALESCE(a.orden_boletin, 100) AS orden_boletin
                FROM asignaciones a
                WHERE a.activo = TRUE
                ORDER BY
                    COALESCE(a.asignacion_academica_id, a.id),
                    COALESCE(a.orden_boletin, 100),
                    a.id
            )
            SELECT
                asig.id AS asignacion_id,
                m.id AS materia_id,
                m.nombre AS materia,
                p.nombre AS profesor_nombre,
                p.apellido AS profesor_apellido,
                asig.orden_boletin,
                nd.id AS nota_detalle_id,
                nd.descripcion,
                nd.nota,
                COALESCE(nd.tipo_evaluacion, 'numerica') AS tipo_evaluacion,
                nd.valoracion
            FROM estudiantes e
            JOIN asignaciones_academicas asig ON asig.curso_id = e.curso_id
            JOIN materias m ON m.id = asig.materia_id
            JOIN profesor p ON p.id = asig.profesor_id
            LEFT JOIN notas_detalle nd
                ON nd.estudiante_id = e.id
                AND nd.asignacion_id = asig.id
                AND nd.periodo = %s
            WHERE e.id = %s
            ORDER BY asig.orden_boletin, m.nombre, nd.id
        ''', (periodo, estudiante_id))

        materias = {}
        notas_numericas = {}
        for row in cur.fetchall():
            asignacion_id = row['asignacion_id']
            if asignacion_id not in materias:
                materias[asignacion_id] = {
                    'asignacion_id': asignacion_id,
                    'materia_id': row['materia_id'],
                    'materia': row['materia'],
                    'profesor_nombre': row['profesor_nombre'],
                    'profesor_apellido': row['profesor_apellido'],
                    'definitiva': None,
                    'orden_boletin': row['orden_boletin'],
                    'detalles': [],
                }
                notas_numericas[asignacion_id] = []

            if row['nota_detalle_id'] is None:
                continue

            tipo_evaluacion = row['tipo_evaluacion'] or 'numerica'
            nota = float(row['nota']) if row['nota'] is not None else None
            materias[asignacion_id]['detalles'].append({
                'descripcion': row['descripcion'] or '',
                'nota': nota,
                'periodo': periodo,
                'tipo_evaluacion': tipo_evaluacion,
                'valoracion': row['valoracion'],
            })
            if tipo_evaluacion != 'desarrollo' and nota is not None and nota > 0:
                notas_numericas[asignacion_id].append(nota)

        for asignacion_id, materia in materias.items():
            valores = notas_numericas[asignacion_id]
            if valores:
                materia['definitiva'] = sum(valores) / len(valores)

        return {
            'estudiante_id': estudiante_id,
            'estudiante_nombre': est_info['estudiante_nombre'],
            'estudiante_apellido': est_info['estudiante_apellido'],
            'curso': est_info['curso_nombre'],
            'periodo': periodo,
            'materias': list(materias.values()),
        }
    finally:
        cur.close()
        conn.close()

