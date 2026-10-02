from app.core.nivel_academico import (
    NOMBRE_MATERIA_ASISTENCIA_JORNADA,
    resolver_tipo_evaluacion,
)
from app.database import get_connection
from app.repositories import boletin_repository
from app.services.anio_lectivo import anio_distinto_del_activo, exigir_asignacion_editable
from app.services.asignacion_academica import (
    resolver_asignacion_academica_id_cursor,
    resolver_nivel_curso_cursor,
)
from psycopg2.extras import RealDictCursor

def guardar_boletin_controller(data, *, usuario):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_asignacion_editable(cursor, data.asignacion_id, usuario)
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, data.asignacion_id)
        nivel_curso = resolver_nivel_curso_cursor(cursor, asignacion_id)
        tipo_evaluacion = resolver_tipo_evaluacion(
            nivel_curso, getattr(data, "tipo_evaluacion", None)
        )
        boletin_id = boletin_repository.guardar_cabecera(
            cursor, data.estudiante_id, asignacion_id, data.periodo, data.definitiva
        )

        boletin_repository.borrar_detalles_de_boletin(cursor, boletin_id)

        for det in data.detalles:
            tipo_evaluacion_detalle = resolver_tipo_evaluacion(
                nivel_curso,
                getattr(det, "tipo_evaluacion", tipo_evaluacion) or tipo_evaluacion,
            )
            boletin_repository.insertar_detalle(
                cursor,
                boletin_id,
                det.nota,
                det.observacion,
                tipo_evaluacion_detalle,
                getattr(det, "valoracion", None),
            )

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
        filas = boletin_repository.leer_notas_de_planilla(cursor, asignacion_id, periodo)

        estudiantes_dict = {}
        for row in filas:
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
            guardados = boletin_repository.leer_boletines_guardados_de_estudiantes(
                cursor, asignacion_id, periodo, est_ids
            )

            saved_by_student = {}
            for row in guardados:
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

def obtener_boletin_admin_controller(estudiante_id: int, periodo: int, anio_lectivo_id=None):
    """Boletin de un año; sin `anio_lectivo_id`, o con el activo, el de siempre.

    Un año que no existe lanza `AnioLectivoInexistenteError`.
    """
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Año lectivo, fase 3 (paso 3.5a): `None` es el camino de siempre.
        anio = anio_distinto_del_activo(cur, anio_lectivo_id)

        materias_res = boletin_repository.leer_materias_del_estudiante(
            cur, estudiante_id, periodo, NOMBRE_MATERIA_ASISTENCIA_JORNADA,
            anio_lectivo_id=anio,
        )

        asignacion_ids = [row['asignacion_id'] for row in materias_res]
        detalles_por_asignacion = {}
        if asignacion_ids:
            detalles = boletin_repository.leer_detalles_por_asignaciones(
                cur, periodo, estudiante_id, asignacion_ids
            )

            for det in detalles:
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

        est_info = boletin_repository.leer_datos_del_estudiante(
            cur, estudiante_id, anio_lectivo_id=anio
        )

        if not est_info:
            return None

        # Puesto del estudiante en el curso para el periodo (solo numericas).
        # Promedia las definitivas no nulas por estudiante y rankea descendente.
        ranking_row = boletin_repository.leer_puesto_en_el_curso(
            cur, estudiante_id, periodo, anio_lectivo_id=anio
        ) or {}

        resultado = {
            'estudiante_id': estudiante_id,
            'estudiante_nombre': est_info['estudiante_nombre'],
            'estudiante_apellido': est_info['estudiante_apellido'],
            'curso': est_info['curso_nombre'],
            'jornada': est_info.get('jornada'),
            'director_grupo': (
                f"{est_info['director_grupo_nombre']} {est_info['director_grupo_apellido']}"
                if est_info.get('director_grupo_nombre') else None
            ),
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


def obtener_reporte_parcial_admin_controller(estudiante_id: int, periodo: int, anio_lectivo_id=None):
    """Construye una fotografía de la planilla vigente, sin usar el boletín enviado.

    De un año; sin `anio_lectivo_id`, o con el activo, la de siempre. Un año
    que no existe lanza `AnioLectivoInexistenteError`.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Año lectivo, fase 3 (paso 3.5a): `None` es el camino de siempre.
        anio = anio_distinto_del_activo(cur, anio_lectivo_id)

        est_info = boletin_repository.leer_datos_basicos_del_estudiante(
            cur, estudiante_id, anio_lectivo_id=anio
        )
        if not est_info:
            return None

        filas = boletin_repository.leer_planilla_vigente(
            cur, estudiante_id, periodo, NOMBRE_MATERIA_ASISTENCIA_JORNADA,
            anio_lectivo_id=anio,
        )

        materias = {}
        notas_numericas = {}
        for row in filas:
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
            'jornada': est_info.get('jornada'),
            'director_grupo': (
                f"{est_info['director_grupo_nombre']} {est_info['director_grupo_apellido']}"
                if est_info.get('director_grupo_nombre') else None
            ),
            'periodo': periodo,
            'materias': list(materias.values()),
        }
    finally:
        cur.close()
        conn.close()

