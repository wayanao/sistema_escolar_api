from app.core.subnotas_planilla import armar_subnotas_de_planilla
from app.database import get_cursor
from app.repositories import planilla_repository, subnotas_planilla_repository
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor

def planilla_excel_controller(asignacion_id, periodo=1, *, con_subnotas=False):
    """Columnas y filas de la planilla.

    Sin `con_subnotas` es exactamente la respuesta de siempre, con las mismas
    dos consultas: Asistencia usa esta lectura solo para la lista de
    estudiantes. Con `con_subnotas` agrega una consulta en la misma conexion y
    las claves `subnotas` (ver docs/funcionalidades/SUBNOTAS_PLANILLA.md).
    """

    with get_cursor() as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)

        rows = planilla_repository.leer_filas_de_planilla(
            cursor,
            periodo,
            asignacion_id,
        )
        filas_subnotas = (
            subnotas_planilla_repository.leer_subnotas_de_planilla(
                cursor, asignacion_id, periodo
            )
            if con_subnotas
            else None
        )

    estudiantes = {}
    columnas = set()
    primer_id_por_columna = {}

    for row in rows:
        est_id = row[0]
        nombre = row[1]
        apellido = row[2]
        materia = row[3]
        descripcion = row[4]
        nota = row[5]
        tipo_evaluacion = row[6] or "numerica"
        valoracion = row[7]
        nota_id = row[8]

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

            if nota_id is not None:
                anterior = primer_id_por_columna.get(descripcion)
                if anterior is None or nota_id < anterior:
                    primer_id_por_columna[descripcion] = nota_id

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

    columnas_por_orden_de_creacion = sorted(
        columnas, key=lambda c: primer_id_por_columna.get(c, float("inf"))
    )

    respuesta = {
        "columnas": [c.strip() for c in columnas_por_orden_de_creacion],
        "data": sorted(list(estudiantes.values()), key=lambda x: (x.get("apellido", "").lower(), x.get("nombre", "").lower()))
    }

    if filas_subnotas is not None:
        por_tipo, por_estudiante = armar_subnotas_de_planilla(
            respuesta["columnas"], filas_subnotas
        )
        respuesta["subnotas"] = por_tipo
        for est in respuesta["data"]:
            est["subnotas"] = por_estudiante.get(est["estudiante_id"], {})

    return respuesta
