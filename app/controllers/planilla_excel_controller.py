from app.database import get_connection

def planilla_excel_controller(asignacion_id, periodo=1):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            e.id,
            e.nombre,
            e.apellido,
            m.nombre AS materia,
            nd.descripcion,
            nd.nota,
            COALESCE(nd.tipo_evaluacion, 'numerica') AS tipo_evaluacion,
            nd.valoracion

        FROM asignaciones a
        JOIN cursos c ON a.curso_id = c.id
        JOIN materias m ON a.materia_id = m.id
        JOIN estudiantes e ON e.curso_id = a.curso_id
        
        LEFT JOIN notas_detalle nd 
            ON nd.estudiante_id = e.id 
            AND nd.asignacion_id = a.id
            AND nd.periodo = %s

        WHERE a.id = %s
    """, (periodo, asignacion_id))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    estudiantes = {}
    columnas = set()

    for row in rows:
        est_id = row[0]
        nombre = row[1]
        apellido = row[2]
        materia = row[3]
        descripcion = row[4]
        nota = row[5]
        tipo_evaluacion = row[6] or "numerica"
        valoracion = row[7]

        if est_id not in estudiantes:
            estudiantes[est_id] = {
                "estudiante_id": est_id,
                "nombre": nombre,
                "apellido": apellido,
                "materia": materia,
                "notas": {},
                "tipos_evaluacion": {},
                "valoraciones": {},
                "promedio": 0
            }

        if descripcion and descripcion != "Desde React":
            columnas.add(descripcion)
            estudiantes[est_id]["notas"][descripcion] = float(nota) if nota is not None else None
            estudiantes[est_id]["tipos_evaluacion"][descripcion] = tipo_evaluacion
            estudiantes[est_id]["valoraciones"][descripcion] = valoracion

    # 🔥 calcular promedio
    for est in estudiantes.values():
        notas_validas = [
            n for descripcion, n in est["notas"].items()
            if n is not None and est["tipos_evaluacion"].get(descripcion, "numerica") == "numerica"
        ]
        if notas_validas:
            est["promedio"] = round(sum(notas_validas) / len(notas_validas), 2)
        else:
            est["promedio"] = ""

    return {
        "columnas": sorted([c.strip() for c in columnas]),
        "data": sorted(list(estudiantes.values()), key=lambda x: (x.get("apellido", "").lower(), x.get("nombre", "").lower()))
    }
