from psycopg2 import IntegrityError, errorcodes

from app.database import get_connection, get_cursor
from app.repositories import asignaciones_repository


ASIGNACION_OTRO_PROFESOR_MENSAJE = (
    "Esta materia ya está asignada en este curso a otro profesor. "
    "No puedes asignarla a un profesor diferente."
)
ASIGNACION_HORARIO_DUPLICADO_MENSAJE = (
    "Ese horario ya está registrado para este profesor, curso y materia."
)


class AsignacionDuplicadaError(Exception):
    pass

# Rangos institucionales permitidos (formato HH:MM 24h)
MANANA_INICIO = "06:30"
MANANA_FIN = "12:30"
TARDE_INICIO = "12:30"
TARDE_FIN = "18:30"
JORNADAS_PERMITIDAS = (
    ("Mañana", MANANA_INICIO, MANANA_FIN),
    ("Tarde", TARDE_INICIO, TARDE_FIN),
)


def normalizar_hora(valor):
    if valor is None:
        return None
    if hasattr(valor, "strftime"):
        return valor.strftime("%H:%M")
    return str(valor)[:5]


def hora_a_minutos(hora):
    hora = normalizar_hora(hora)
    if not hora:
        return None
    try:
        horas, minutos = hora.split(":")
        return int(horas) * 60 + int(minutos)
    except (TypeError, ValueError):
        return None


def minutos_a_hora(total_minutos):
    horas = total_minutos // 60
    minutos = total_minutos % 60
    return f"{horas:02d}:{minutos:02d}"


def validar_rango_institucional(hora_inicio, hora_fin):
    inicio = hora_a_minutos(hora_inicio)
    fin = hora_a_minutos(hora_fin)

    if inicio is None or fin is None:
        return "Formato de hora inválido."

    if inicio >= fin:
        return "La hora de inicio debe ser anterior a la hora de fin."

    for _, ventana_inicio, ventana_fin in JORNADAS_PERMITIDAS:
        if hora_a_minutos(ventana_inicio) <= inicio and fin <= hora_a_minutos(ventana_fin):
            return None

    return (
        "El horario debe estar dentro de una jornada válida: "
        f"{MANANA_INICIO}-{MANANA_FIN} o {TARDE_INICIO}-{TARDE_FIN}."
    )


def validar_jornada_curso(cursor, curso_id, hora_inicio, hora_fin):
    """Devuelve un mensaje de error si la hora no respeta la jornada del curso,
    o None si todo está OK."""
    if not hora_inicio or not hora_fin:
        return None

    cursor.execute("SELECT jornada FROM cursos WHERE id = %s", (curso_id,))
    row = cursor.fetchone()
    if not row:
        return None  # el curso ya se valida por la FK en el INSERT

    jornada = (row[0] or "").strip().lower()
    if not jornada:
        return None  # curso sin jornada definida → no se valida

    hora_inicio = normalizar_hora(hora_inicio)
    hora_fin = normalizar_hora(hora_fin)

    if "mañan" in jornada or "manan" in jornada:
        if hora_fin > MANANA_FIN:
            return f"El curso es jornada Mañana: la clase debe terminar antes o a las {MANANA_FIN}."
    elif "tarde" in jornada:
        if hora_inicio < TARDE_INICIO:
            return f"El curso es jornada Tarde: la clase debe comenzar a partir de las {TARDE_INICIO}."

    return None


def verificar_cruce_horario(cursor, campo_id, valor_id, dia, hora_inicio_nueva, hora_fin_nueva):
    if not hora_inicio_nueva or not hora_fin_nueva:
        return False

    if campo_id not in {"profesor_id", "curso_id"}:
        raise ValueError("Campo de cruce no permitido")

    cursor.execute(
        f"""
        SELECT hora_inicio, hora_fin
        FROM asignaciones
        WHERE {campo_id} = %s
          AND dia = %s
          AND activo = TRUE
        """,
        (valor_id, dia),
    )
    registros = cursor.fetchall()

    hora_inicio_nueva = normalizar_hora(hora_inicio_nueva)
    hora_fin_nueva = normalizar_hora(hora_fin_nueva)
    
    for row in registros:
        h_inicio_db = normalizar_hora(row[0])
        h_fin_db = normalizar_hora(row[1])
        
        # Ignorar si están vacíos o nulos
        if not h_inicio_db or not h_fin_db:
            continue
            
        # Comparamos cadenas asumiendo formato HH:MM (ej. '07:00' < '08:30')
        # Esto funciona perfectamente para formatos de hora en 24h.
        if h_inicio_db < hora_fin_nueva and h_fin_db > hora_inicio_nueva:
            return True
            
    return False


def profesor_activo(cursor, profesor_id):
    cursor.execute(
        """
        SELECT 1
        FROM profesor
        WHERE id = %s
          AND COALESCE(LOWER(estado), 'activo') = 'activo'
        """,
        (profesor_id,),
    )
    return cursor.fetchone() is not None


def curso_activo(cursor, curso_id):
    cursor.execute(
        """
        SELECT 1
        FROM cursos
        WHERE id = %s
          AND COALESCE(LOWER(estado), 'activo') = 'activo'
        """,
        (curso_id,),
    )
    return cursor.fetchone() is not None


def materia_activa(cursor, materia_id):
    cursor.execute(
        """
        SELECT 1
        FROM materias
        WHERE id = %s
          AND COALESCE(LOWER(estado), 'activo') = 'activo'
        """,
        (materia_id,),
    )
    return cursor.fetchone() is not None


def validar_profesor_responsable_materia(cursor, profesor_id, curso_id, materia_id, asignacion_id=None):
    params = [curso_id, materia_id, profesor_id]
    filtro_asignacion = ""
    if asignacion_id is not None:
        filtro_asignacion = "AND a.id != %s"
        params.append(asignacion_id)

    cursor.execute(
        f"""
        SELECT p.nombre || ' ' || p.apellido AS profesor_nombre
        FROM asignaciones a
        JOIN profesor p ON p.id = a.profesor_id
        WHERE a.curso_id = %s
          AND a.materia_id = %s
          AND a.profesor_id != %s
          AND a.activo = TRUE
          {filtro_asignacion}
        LIMIT 1
        """,
        params,
    )
    row = cursor.fetchone()
    if row:
        profesor_nombre = row[0] or "otro profesor"
        raise AsignacionDuplicadaError(
            f"Esta materia ya está asignada en este curso al profesor {profesor_nombre}."
        )


def validar_horario_unico(cursor, profesor_id, curso_id, materia_id, dia, hora_inicio, hora_fin, asignacion_id=None):
    if not dia or not hora_inicio or not hora_fin:
        return

    params = [profesor_id, curso_id, materia_id, dia, hora_inicio, hora_fin]
    filtro_asignacion = ""
    if asignacion_id is not None:
        filtro_asignacion = "AND id != %s"
        params.append(asignacion_id)

    cursor.execute(
        f"""
        SELECT 1
        FROM asignaciones
        WHERE profesor_id = %s
          AND curso_id = %s
          AND materia_id = %s
          AND dia IS NOT DISTINCT FROM %s
          AND hora_inicio IS NOT DISTINCT FROM %s
          AND hora_fin IS NOT DISTINCT FROM %s
          AND activo = TRUE
          {filtro_asignacion}
        LIMIT 1
        """,
        params,
    )
    if cursor.fetchone():
        raise AsignacionDuplicadaError(ASIGNACION_HORARIO_DUPLICADO_MENSAJE)


def obtener_asignacion_academica_id(cursor, profesor_id, curso_id, materia_id, asignacion_id=None):
    params = [profesor_id, curso_id, materia_id]
    filtro_asignacion = ""
    if asignacion_id is not None:
        filtro_asignacion = "AND id != %s"
        params.append(asignacion_id)

    cursor.execute(
        f"""
        SELECT COALESCE(asignacion_academica_id, id)
        FROM asignaciones
        WHERE profesor_id = %s
          AND curso_id = %s
          AND materia_id = %s
          AND activo = TRUE
          {filtro_asignacion}
        ORDER BY id ASC
        LIMIT 1
        """,
        params,
    )
    row = cursor.fetchone()
    return row[0] if row else None


def obtener_orden_boletin_materia_curso(cursor, curso_id, materia_id):
    cursor.execute(
        """
        SELECT COALESCE(MIN(orden_boletin), 100)
        FROM asignaciones
        WHERE curso_id = %s
          AND materia_id = %s
          AND activo = TRUE
        """,
        (curso_id, materia_id),
    )
    row = cursor.fetchone()
    return row[0] if row and row[0] is not None else 100


def _formatear_orden_boletin(row):
    return {
        "asignacion_academica_id": row[0],
        "curso_id": row[1],
        "curso_nombre": row[2],
        "materia_id": row[3],
        "materia_nombre": row[4],
        "profesor_id": row[5],
        "profesor_nombre": row[6],
        "orden_boletin": row[7],
        "horarios": row[8],
    }


def _obtener_orden_boletin_curso(cursor, curso_id):
    cursor.execute(
        """
        SELECT
            MIN(COALESCE(a.asignacion_academica_id, a.id)) AS asignacion_academica_id,
            a.curso_id,
            c.nombre AS curso_nombre,
            a.materia_id,
            m.nombre AS materia_nombre,
            MIN(a.profesor_id) AS profesor_id,
            MIN(p.nombre || ' ' || p.apellido) AS profesor_nombre,
            COALESCE(MIN(a.orden_boletin), 100) AS orden_boletin,
            COUNT(*) AS horarios
        FROM asignaciones a
        JOIN cursos c ON c.id = a.curso_id
        JOIN materias m ON m.id = a.materia_id
        JOIN profesor p ON p.id = a.profesor_id
        WHERE a.curso_id = %s
          AND a.activo = TRUE
          AND COALESCE(LOWER(c.estado), 'activo') = 'activo'
          AND COALESCE(LOWER(m.estado), 'activo') = 'activo'
        GROUP BY a.curso_id, c.nombre, a.materia_id, m.nombre
        ORDER BY COALESCE(MIN(a.orden_boletin), 100), m.nombre
        """,
        (curso_id,),
    )
    return [_formatear_orden_boletin(row) for row in cursor.fetchall()]


def obtener_orden_boletin_curso_controller(curso_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        return {
            "curso_id": curso_id,
            "items": _obtener_orden_boletin_curso(cursor, curso_id),
        }
    finally:
        cursor.close()
        conn.close()


def actualizar_orden_boletin_curso_controller(curso_id, data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 1
            FROM cursos
            WHERE id = %s
              AND COALESCE(LOWER(estado), 'activo') = 'activo'
            """,
            (curso_id,),
        )
        if not cursor.fetchone():
            return {"error": "Curso no encontrado o inactivo."}

        materia_ids = [item.materia_id for item in data.materias]
        if len(materia_ids) != len(set(materia_ids)):
            return {"error": "El orden enviado contiene materias repetidas."}

        cursor.execute(
            """
            SELECT DISTINCT materia_id
            FROM asignaciones
            WHERE curso_id = %s
              AND activo = TRUE
            """,
            (curso_id,),
        )
        materias_asignadas = {row[0] for row in cursor.fetchall()}
        materias_invalidas = [materia_id for materia_id in materia_ids if materia_id not in materias_asignadas]
        if materias_invalidas:
            return {"error": "El orden contiene materias que no están asignadas a este curso."}

        asignaciones_repository.reiniciar_orden_boletin(cursor, curso_id)

        for posicion, item in enumerate(data.materias, start=1):
            asignaciones_repository.fijar_orden_boletin_materia(
                cursor, posicion, curso_id, item.materia_id
            )

        conn.commit()
        return {
            "mensaje": "Orden del boletín actualizado",
            "curso_id": curso_id,
            "items": _obtener_orden_boletin_curso(cursor, curso_id),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


# 🎯 Asignar profesor a curso
def asignar_profesor_controller(asignacion):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if not profesor_activo(cursor, asignacion.profesor_id):
            return {"error": "No se puede asignar un profesor inactivo."}

        if not curso_activo(cursor, asignacion.curso_id):
            return {"error": "No se puede asignar un curso inactivo."}

        if not materia_activa(cursor, asignacion.materia_id):
            return {"error": "No se puede asignar una materia inactiva."}

        validar_profesor_responsable_materia(
            cursor,
            asignacion.profesor_id,
            asignacion.curso_id,
            asignacion.materia_id,
        )
        validar_horario_unico(
            cursor,
            asignacion.profesor_id,
            asignacion.curso_id,
            asignacion.materia_id,
            asignacion.dia,
            asignacion.hora_inicio,
            asignacion.hora_fin,
        )
        asignacion_academica_id = obtener_asignacion_academica_id(
            cursor,
            asignacion.profesor_id,
            asignacion.curso_id,
            asignacion.materia_id,
        )
        orden_boletin = obtener_orden_boletin_materia_curso(
            cursor,
            asignacion.curso_id,
            asignacion.materia_id,
        )

        if asignacion.hora_inicio and asignacion.hora_fin:
            error_rango = validar_rango_institucional(asignacion.hora_inicio, asignacion.hora_fin)
            if error_rango:
                return {"error": error_rango}

            error_jornada = validar_jornada_curso(cursor, asignacion.curso_id, asignacion.hora_inicio, asignacion.hora_fin)
            if error_jornada:
                return {"error": error_jornada}

            if verificar_cruce_horario(cursor, "profesor_id", asignacion.profesor_id, asignacion.dia, asignacion.hora_inicio, asignacion.hora_fin):
                return {"error": "Error: El profesor ya tiene una clase asignada en ese horario y ese día."}

            if verificar_cruce_horario(cursor, "curso_id", asignacion.curso_id, asignacion.dia, asignacion.hora_inicio, asignacion.hora_fin):
                return {"error": "Error: El curso (salón) ya tiene otra clase asignada en ese horario y ese día."}

        try:
            asignaciones_repository.insertar_asignacion(cursor, (
                asignacion.profesor_id,
                asignacion.curso_id,
                asignacion.materia_id,
                asignacion.dia,
                asignacion.hora_inicio,
                asignacion.hora_fin,
                asignacion_academica_id,
                orden_boletin
            ))
        except IntegrityError as exc:
            conn.rollback()
            if exc.pgcode == errorcodes.UNIQUE_VIOLATION:
                raise AsignacionDuplicadaError(ASIGNACION_OTRO_PROFESOR_MENSAJE) from exc
            raise

        asignacion_id = cursor.fetchone()[0]
        if asignacion_academica_id is None:
            asignaciones_repository.apuntar_asignacion_a_si_misma(cursor, asignacion_id)
        conn.commit()
        return {
            "mensaje": "Asignación creada",
            "id": asignacion_id
        }
    finally:
        cursor.close()
        conn.close()


# 🎯 Ver cursos de un profesor
def cursos_por_profesor_controller(profesor_id):

    with get_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT
                c.id,
                c.nombre
            FROM asignaciones a
            JOIN cursos c ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            WHERE a.profesor_id = %s
              AND a.activo = TRUE
              AND COALESCE(LOWER(c.estado), 'activo') = 'activo'
              AND COALESCE(LOWER(m.estado), 'activo') = 'activo'
        """, (profesor_id,))

        resultado = cursor.fetchall()

    data = []

    for row in resultado:
        data.append({
            "curso_id": row[0],
            "nombre": row[1]
        })

    return data


# 🎯 Ver profesor de un curso
def profesor_por_curso_controller(curso_id):

    with get_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT
                p.id,
                p.nombre,
                p.apellido
            FROM asignaciones a
            JOIN profesor p ON a.profesor_id = p.id
            JOIN cursos c ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            WHERE a.curso_id = %s
              AND a.activo = TRUE
              AND COALESCE(LOWER(c.estado), 'activo') = 'activo'
              AND COALESCE(LOWER(m.estado), 'activo') = 'activo'
        """, (curso_id,))

        resultado = cursor.fetchall()

    data = []

    for row in resultado:
        data.append({
            "profesor_id": row[0],
            "nombre": row[1],
            "apellido": row[2]
        })

    return data
def obtener_horarios_admin_controller():
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT
                p.nombre || ' ' || p.apellido AS profesor,
                c.nombre AS curso,
                m.nombre AS materia,
                a.dia,
                a.hora_inicio,
                a.hora_fin
            FROM asignaciones a
            JOIN profesor p ON a.profesor_id = p.id
            JOIN cursos c ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            WHERE a.dia IS NOT NULL
              AND a.hora_inicio IS NOT NULL
              AND a.hora_fin IS NOT NULL
              AND a.hora_inicio != ''
              AND a.hora_fin != ''
              AND a.activo = TRUE
              AND COALESCE(LOWER(c.estado), 'activo') = 'activo'
              AND COALESCE(LOWER(m.estado), 'activo') = 'activo'
            ORDER BY
                CASE a.dia
                    WHEN 'Lunes' THEN 1
                    WHEN 'Martes' THEN 2
                    WHEN 'Miércoles' THEN 3
                    WHEN 'Jueves' THEN 4
                    WHEN 'Viernes' THEN 5
                    WHEN 'Sábado' THEN 6
                    WHEN 'Domingo' THEN 7
                    ELSE 8
                END,
                a.hora_inicio
        """)

        clases = cursor.fetchall()

    resultado = []
    for c in clases:
        resultado.append({
            "profesor": c[0],
            "curso": c[1],
            "materia": c[2],
            "dia": c[3],
            "hora_inicio": c[4],
            "hora_fin": c[5]
        })

    return resultado

# 🎯 Eliminar asignación profesor ↔ curso
def eliminar_asignacion_controller(profesor_id, curso_id):

    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            SELECT id FROM asignaciones
            WHERE profesor_id = %s AND curso_id = %s AND activo = TRUE
            ORDER BY id DESC
            LIMIT 1
        """, (profesor_id, curso_id))

        asignacion = cursor.fetchone()

        if not asignacion:
            return {"mensaje": "Asignación no encontrada"}

        asignacion_id = asignacion[0]

        asignaciones_repository.desactivar_asignacion(cursor, asignacion_id)

    return {"mensaje": "Asignación desactivada. El historial académico se conserva."}

def obtener_clases_profesor_controller(profesor_id):

    with get_cursor() as cursor:
        cursor.execute("""
            SELECT
                a.id,
                c.nombre,
                m.nombre
            FROM asignaciones a
            JOIN cursos c ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            WHERE a.profesor_id = %s
              AND a.activo = TRUE
              AND COALESCE(LOWER(c.estado), 'activo') = 'activo'
              AND COALESCE(LOWER(m.estado), 'activo') = 'activo'
        """, (profesor_id,))

        rows = cursor.fetchall()

    return [
        {
            "id": r[0],
            "curso": r[1],
            "materia": r[2]
        }
        for r in rows
    ]
# Desactivar asignación por ID preservando historial académico
def eliminar_asignacion_por_id_controller(asignacion_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM asignaciones WHERE id = %s AND activo = TRUE", (asignacion_id,))
        if not cursor.fetchone():
            return {"error": "Asignación no encontrada"}

        asignaciones_repository.desactivar_asignacion_por_id(cursor, asignacion_id)
        conn.commit()
        return {"mensaje": "Asignación desactivada. El historial académico se conserva."}
    finally:
        cursor.close()
        conn.close()


def verificar_cruce_horario_editar(cursor, campo_id, valor_id, dia, hora_inicio_nueva, hora_fin_nueva, asignacion_id_ignorar):
    if not hora_inicio_nueva or not hora_fin_nueva:
        return False

    if campo_id not in {"profesor_id", "curso_id"}:
        raise ValueError("Campo de cruce no permitido")

    cursor.execute(
        f"""
        SELECT hora_inicio, hora_fin
        FROM asignaciones
        WHERE {campo_id} = %s
          AND dia = %s
          AND id != %s
          AND activo = TRUE
        """,
        (valor_id, dia, asignacion_id_ignorar),
    )
    registros = cursor.fetchall()

    hora_inicio_nueva = normalizar_hora(hora_inicio_nueva)
    hora_fin_nueva = normalizar_hora(hora_fin_nueva)

    for row in registros:
        h_inicio_db = normalizar_hora(row[0])
        h_fin_db = normalizar_hora(row[1])

        if not h_inicio_db or not h_fin_db:
            continue

        if h_inicio_db < hora_fin_nueva and h_fin_db > hora_inicio_nueva:       
            return True
            
    return False


def tabla_columna_existe(cursor, tabla, columna):
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = %s
          AND column_name = %s
        """,
        (tabla, columna),
    )
    return cursor.fetchone() is not None


def asignacion_tiene_historial(cursor, asignacion_id):
    tablas = [
        "plan_de_clases",
        "planeador_anual",
        "asistencia",
        "notas",
        "notas_detalle",
        "boletin_cabecera",
        "observaciones",
    ]

    for tabla in tablas:
        if not tabla_columna_existe(cursor, tabla, "asignacion_id"):
            continue
        cursor.execute(f"SELECT 1 FROM {tabla} WHERE asignacion_id = %s LIMIT 1", (asignacion_id,))
        if cursor.fetchone():
            return True
    return False

def editar_asignacion_controller(asignacion_id, asignacion):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT profesor_id, curso_id, materia_id, activo, COALESCE(asignacion_academica_id, id)
            FROM asignaciones
            WHERE id = %s
        """, (asignacion_id,))
        actual = cursor.fetchone()
        if not actual:
            return {"error": "Asignación no encontrada"}
        if actual[3] is not True:
            return {"error": "No se puede editar una asignación inactiva."}

        if not profesor_activo(cursor, asignacion.profesor_id):
            return {"error": "No se puede asignar un profesor inactivo."}

        if not curso_activo(cursor, asignacion.curso_id):
            return {"error": "No se puede asignar un curso inactivo."}

        if not materia_activa(cursor, asignacion.materia_id):
            return {"error": "No se puede asignar una materia inactiva."}

        cambia_relacion_academica = (
            actual[0] != asignacion.profesor_id
            or actual[1] != asignacion.curso_id
            or actual[2] != asignacion.materia_id
        )
        if cambia_relacion_academica and asignacion_tiene_historial(cursor, asignacion_id):
            return {
                "error": (
                    "Esta asignación ya tiene historial académico. "
                    "Desactívala y crea una nueva para cambiar profesor, curso o materia."
                )
            }

        validar_profesor_responsable_materia(
            cursor,
            asignacion.profesor_id,
            asignacion.curso_id,
            asignacion.materia_id,
            asignacion_id=asignacion_id,
        )
        validar_horario_unico(
            cursor,
            asignacion.profesor_id,
            asignacion.curso_id,
            asignacion.materia_id,
            asignacion.dia,
            asignacion.hora_inicio,
            asignacion.hora_fin,
            asignacion_id=asignacion_id,
        )
        if cambia_relacion_academica:
            asignacion_academica_id = obtener_asignacion_academica_id(
                cursor,
                asignacion.profesor_id,
                asignacion.curso_id,
                asignacion.materia_id,
                asignacion_id=asignacion_id,
            ) or asignacion_id
        else:
            asignacion_academica_id = actual[4]

        if asignacion.hora_inicio and asignacion.hora_fin:
            error_rango = validar_rango_institucional(asignacion.hora_inicio, asignacion.hora_fin)
            if error_rango:
                return {"error": error_rango}

            error_jornada = validar_jornada_curso(cursor, asignacion.curso_id, asignacion.hora_inicio, asignacion.hora_fin)
            if error_jornada:
                return {"error": error_jornada}

            if verificar_cruce_horario_editar(cursor, "profesor_id", asignacion.profesor_id, asignacion.dia, asignacion.hora_inicio, asignacion.hora_fin, asignacion_id):
                return {"error": "Error: El profesor ya tiene una clase asignada en ese horario y ese día."}

            if verificar_cruce_horario_editar(cursor, "curso_id", asignacion.curso_id, asignacion.dia, asignacion.hora_inicio, asignacion.hora_fin, asignacion_id):
                return {"error": "Error: El curso (salón) ya tiene otra clase asignada en ese horario y ese día."}

        try:
            asignaciones_repository.actualizar_asignacion(cursor, (
                asignacion.profesor_id,
                asignacion.curso_id,
                asignacion.materia_id,
                asignacion.dia,
                asignacion.hora_inicio,
                asignacion.hora_fin,
                asignacion_academica_id,
                asignacion_id
            ))
        except IntegrityError as exc:
            conn.rollback()
            if exc.pgcode == errorcodes.UNIQUE_VIOLATION:
                raise AsignacionDuplicadaError(ASIGNACION_OTRO_PROFESOR_MENSAJE) from exc
            raise

        res = cursor.fetchone()
        if not res:
            return {"error": "Asignación no encontrada"}
            
        conn.commit()
        return {
            "mensaje": "Asignación actualizada"
        }
    finally:
        cursor.close()
        conn.close()

def obtener_todas_asignaciones_controller():
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT
                a.id, a.profesor_id, a.curso_id, a.materia_id, a.dia, a.hora_inicio, a.hora_fin,
                p.nombre || ' ' || p.apellido AS profesor_nombre,
                c.nombre AS curso_nombre,
                m.nombre AS materia_nombre,
                COALESCE(a.asignacion_academica_id, a.id) AS asignacion_academica_id,
                COALESCE(a.orden_boletin, 100) AS orden_boletin
            FROM asignaciones a
            JOIN profesor p ON a.profesor_id = p.id
            JOIN cursos c ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            WHERE a.activo = TRUE
              AND COALESCE(LOWER(c.estado), 'activo') = 'activo'
              AND COALESCE(LOWER(m.estado), 'activo') = 'activo'
            ORDER BY a.id DESC
        """)

        rows = cursor.fetchall()

    resultado = []
    for r in rows:
        resultado.append({
            "id": r[0],
            "profesor_id": r[1],
            "curso_id": r[2],
            "materia_id": r[3],
            "dia": r[4] or "",
            "hora_inicio": r[5] or "",
            "hora_fin": r[6] or "",
            "profesor_nombre": r[7],
            "curso_nombre": r[8],
            "materia_nombre": r[9],
            "asignacion_academica_id": r[10],
            "orden_boletin": r[11]
        })
        
    return resultado

def _formatear_asignacion(row):
    return {
        "id": row[0],
        "profesor_id": row[1],
        "curso_id": row[2],
        "materia_id": row[3],
        "dia": row[4] or "",
        "hora_inicio": row[5] or "",
        "hora_fin": row[6] or "",
        "profesor_nombre": row[7],
        "curso_nombre": row[8],
        "materia_nombre": row[9],
        "asignacion_academica_id": row[10],
        "orden_boletin": row[11]
    }

def obtener_todas_asignaciones_paginado_controller(
    limit=50,
    offset=0,
    profesor_id=None,
    curso_id=None,
    materia_id=None,
    busqueda=None,
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        filtros = []
        params = []

        if profesor_id is not None:
            filtros.append("a.profesor_id = %s")
            params.append(profesor_id)

        if curso_id is not None:
            filtros.append("a.curso_id = %s")
            params.append(curso_id)

        if materia_id is not None:
            filtros.append("a.materia_id = %s")
            params.append(materia_id)

        if busqueda:
            filtros.append("""(
                LOWER(p.nombre || ' ' || p.apellido) LIKE LOWER(%s)
                OR LOWER(c.nombre) LIKE LOWER(%s)
                OR LOWER(m.nombre) LIKE LOWER(%s)
            )""")
            patron = f"%{busqueda}%"
            params.extend([patron, patron, patron])

        filtros.append("a.activo = TRUE")
        filtros.append("COALESCE(LOWER(c.estado), 'activo') = 'activo'")
        filtros.append("COALESCE(LOWER(m.estado), 'activo') = 'activo'")

        where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(f"""
            SELECT COUNT(*)
            FROM asignaciones a
            JOIN profesor p ON a.profesor_id = p.id
            JOIN cursos c ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            {where_sql}
        """, params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT
                a.id, a.profesor_id, a.curso_id, a.materia_id, a.dia, a.hora_inicio, a.hora_fin,
                p.nombre || ' ' || p.apellido AS profesor_nombre,
                c.nombre AS curso_nombre,
                m.nombre AS materia_nombre,
                COALESCE(a.asignacion_academica_id, a.id) AS asignacion_academica_id,
                COALESCE(a.orden_boletin, 100) AS orden_boletin
            FROM asignaciones a
            JOIN profesor p ON a.profesor_id = p.id
            JOIN cursos c ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            {where_sql}
            ORDER BY a.id DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        rows = cursor.fetchall()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_formatear_asignacion(row) for row in rows]
        }
    finally:
        cursor.close()
        conn.close()


def obtener_disponibilidad_profesor_controller(profesor_id, dia, excluir_asignacion_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        params = [profesor_id, dia]
        filtro_excluir = ""
        if excluir_asignacion_id is not None:
            filtro_excluir = "AND id != %s"
            params.append(excluir_asignacion_id)

        cursor.execute(f"""
            SELECT hora_inicio, hora_fin
            FROM asignaciones
            WHERE profesor_id = %s
              AND dia = %s
              AND activo = TRUE
              AND hora_inicio IS NOT NULL
              AND hora_fin IS NOT NULL
              AND hora_inicio != ''
              AND hora_fin != ''
              {filtro_excluir}
            ORDER BY hora_inicio
        """, params)
        ocupadas = []
        for inicio, fin in cursor.fetchall():
            inicio_min = hora_a_minutos(inicio)
            fin_min = hora_a_minutos(fin)
            if inicio_min is None or fin_min is None or inicio_min >= fin_min:
                continue
            ocupadas.append((inicio_min, fin_min))

        jornadas = []
        for nombre, ventana_inicio, ventana_fin in JORNADAS_PERMITIDAS:
            cursor_inicio = hora_a_minutos(ventana_inicio)
            cursor_fin = hora_a_minutos(ventana_fin)
            libres = []

            for ocupado_inicio, ocupado_fin in ocupadas:
                if ocupado_fin <= cursor_inicio or ocupado_inicio >= cursor_fin:
                    continue
                if cursor_inicio < ocupado_inicio:
                    libres.append({
                        "inicio": minutos_a_hora(cursor_inicio),
                        "fin": minutos_a_hora(min(ocupado_inicio, cursor_fin)),
                    })
                cursor_inicio = max(cursor_inicio, ocupado_fin)

            if cursor_inicio < cursor_fin:
                libres.append({
                    "inicio": minutos_a_hora(cursor_inicio),
                    "fin": minutos_a_hora(cursor_fin),
                })

            jornadas.append({
                "jornada": nombre,
                "inicio": ventana_inicio,
                "fin": ventana_fin,
                "rangos": libres,
            })

        return {
            "profesor_id": profesor_id,
            "dia": dia,
            "jornadas": jornadas,
        }
    finally:
        cursor.close()
        conn.close()
