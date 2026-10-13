"""Consultas de la tabla `admisiones` (entrevista de admisión, paso E2).

Ver `docs/funcionalidades/ENTREVISTA_ADMISION.md`. Recibe y devuelve datos
simples; las reglas (año en preparación, curso del año, documento repetido)
viven en `admisiones_controller`.

Los nombres de columna que se arman en el SQL salen de las tuplas de abajo,
escritas a mano, nunca de lo que manda el cliente.
"""

# Lo que se pide al registrar al aspirante (mismo orden que `AdmisionCreate`).
COLUMNAS_ASPIRANTE = (
    "nombre",
    "apellido",
    "tipo_documento",
    "documento_identidad",
    "fecha_nacimiento",
    "curso_id",
    "acudiente_nombre",
    "acudiente_parentesco",
    "acudiente_telefono",
    "autoriza_datos",
    "autoriza_nombre",
)

# Lo que se agrega al editar: la entrevista (mismo orden que `AdmisionUpdate`).
COLUMNAS_ENTREVISTA = (
    "fecha_entrevista",
    "entrevistador",
    "asistentes",
    "colegio_anterior",
    "anio_cursado_anterior",
    "pre_escolar_anterior",
    "ebp_anterior",
    "motivo_retiro_anterior",
    "paz_salvo_anterior",
    "ocupacion_padre",
    "ocupacion_madre",
    "vive_con",
    "expectativas",
    "observaciones",
)

# Una admisión completa, con su año y su curso.
COLUMNAS_DETALLE = (
    "id",
    "anio_lectivo_id",
    *COLUMNAS_ASPIRANTE,
    *COLUMNAS_ENTREVISTA,
    "resultado",
    "motivo_resultado",
    "decidido_en",
    "estudiante_id",
    "creado_en",
    "actualizado_en",
    "anio",
    "estado_anio",
    "curso_nombre",
    "curso_jornada",
)

# Una fila de la lista: lo que hace falta para reconocer al aspirante.
COLUMNAS_LISTA = (
    "id",
    "nombre",
    "apellido",
    "tipo_documento",
    "documento_identidad",
    "curso_id",
    "curso_nombre",
    "curso_jornada",
    "acudiente_nombre",
    "acudiente_telefono",
    "fecha_entrevista",
    "resultado",
    "estudiante_id",
    "creado_en",
)

_COLUMNAS_DE_LA_TABLA_EN_DETALLE = COLUMNAS_DETALLE[:-4]


def _como_diccionario(fila, columnas):
    if fila is None:
        return None
    return dict(fila) if isinstance(fila, dict) else dict(zip(columnas, fila))


def leer_admision(cursor, admision_id, bloquear=False):
    """La admisión con su año y su curso, o `None` si no existe.

    Con `bloquear`, deja la fila de la admisión bloqueada hasta el final de la
    transacción, para que nadie la matricule mientras se edita o se borra.
    """
    seleccion = ", ".join(f"a.{columna}" for columna in _COLUMNAS_DE_LA_TABLA_EN_DETALLE)
    sql = f"""
        SELECT {seleccion},
               al.anio, al.estado AS estado_anio,
               c.nombre AS curso_nombre, c.jornada AS curso_jornada
        FROM admisiones a
        JOIN anios_lectivos al ON al.id = a.anio_lectivo_id
        LEFT JOIN cursos c ON c.id = a.curso_id
        WHERE a.id = %s
    """
    if bloquear:
        sql += " FOR UPDATE OF a"
    cursor.execute(sql, (admision_id,))
    return _como_diccionario(cursor.fetchone(), COLUMNAS_DETALLE)


def listar_admisiones(cursor, anio_lectivo_id, resultado=None):
    """Las admisiones de un año, opcionalmente de un solo resultado."""
    sql = """
        SELECT a.id, a.nombre, a.apellido, a.tipo_documento,
               a.documento_identidad, a.curso_id,
               c.nombre AS curso_nombre, c.jornada AS curso_jornada,
               a.acudiente_nombre, a.acudiente_telefono, a.fecha_entrevista,
               a.resultado, a.estudiante_id, a.creado_en
        FROM admisiones a
        LEFT JOIN cursos c ON c.id = a.curso_id
        WHERE a.anio_lectivo_id = %s
    """
    params = [anio_lectivo_id]
    if resultado is not None:
        sql += " AND a.resultado = %s"
        params.append(resultado)
    sql += " ORDER BY a.apellido, a.nombre, a.id"
    cursor.execute(sql, tuple(params))
    return [_como_diccionario(fila, COLUMNAS_LISTA) for fila in cursor.fetchall()]


def contar_admisiones(cursor, anio_lectivo_id):
    """Cuántas hay de cada resultado, cuántas se matricularon y el total."""
    cursor.execute(
        """
        SELECT COUNT(*) FILTER (WHERE resultado = 'pendiente'),
               COUNT(*) FILTER (WHERE resultado = 'aprobado'),
               COUNT(*) FILTER (WHERE resultado = 'no_aprobado'),
               COUNT(estudiante_id),
               COUNT(*)
        FROM admisiones
        WHERE anio_lectivo_id = %s
        """,
        (anio_lectivo_id,),
    )
    fila = cursor.fetchone()
    return dict(zip(("pendiente", "aprobado", "no_aprobado", "matriculado", "total"), fila))


def insertar_admision(cursor, anio_lectivo_id, valores):
    """Registra al aspirante y devuelve su id. El resultado nace `pendiente`."""
    columnas = ", ".join(COLUMNAS_ASPIRANTE)
    marcas = ", ".join(["%s"] * len(COLUMNAS_ASPIRANTE))
    cursor.execute(
        f"""
        INSERT INTO admisiones (anio_lectivo_id, {columnas})
        VALUES (%s, {marcas})
        RETURNING id
        """,
        (anio_lectivo_id, *[valores[columna] for columna in COLUMNAS_ASPIRANTE]),
    )
    return cursor.fetchone()[0]


def actualizar_admision(cursor, admision_id, valores):
    """Reemplaza aspirante y entrevista. Devuelve cuántas filas cambió.

    No toca el resultado, el año ni el enlace al estudiante, y no cambia una
    admisión matriculada: en ese caso devuelve 0.
    """
    columnas = COLUMNAS_ASPIRANTE + COLUMNAS_ENTREVISTA
    asignaciones = ", ".join(f"{columna} = %s" for columna in columnas)
    cursor.execute(
        f"""
        UPDATE admisiones
        SET {asignaciones}, actualizado_en = CURRENT_TIMESTAMP
        WHERE id = %s AND estudiante_id IS NULL
        """,
        (*[valores[columna] for columna in columnas], admision_id),
    )
    return cursor.rowcount


def borrar_admision(cursor, admision_id):
    """Borra una admisión no matriculada. Devuelve cuántas filas borró."""
    cursor.execute(
        "DELETE FROM admisiones WHERE id = %s AND estudiante_id IS NULL",
        (admision_id,),
    )
    return cursor.rowcount


def buscar_admision_con_documento(cursor, anio_lectivo_id, documento, excluir_id=None):
    """El id de otra admisión del año con ese documento, o `None`."""
    sql = "SELECT id FROM admisiones WHERE anio_lectivo_id = %s AND documento_identidad = %s"
    params = [anio_lectivo_id, documento]
    if excluir_id is not None:
        sql += " AND id <> %s"
        params.append(excluir_id)
    cursor.execute(sql + " LIMIT 1", tuple(params))
    fila = cursor.fetchone()
    return fila[0] if fila else None


def buscar_estudiante_con_documento(cursor, documento, excluir_id=None):
    """El estudiante del colegio con ese documento, en cualquier estado.

    `estudiantes.documento_identidad` es único en todo el colegio, así que un
    aspirante que ya fue estudiante chocaría al matricularse como nuevo.
    """
    sql = "SELECT id, nombre, apellido, estado FROM estudiantes WHERE documento_identidad = %s"
    params = [documento]
    if excluir_id is not None:
        sql += " AND id <> %s"
        params.append(excluir_id)
    cursor.execute(sql + " LIMIT 1", tuple(params))
    return _como_diccionario(cursor.fetchone(), ("id", "nombre", "apellido", "estado"))


# ---------------------------------------------------------------------------
# Paso E3: resultado y matrícula.
# ---------------------------------------------------------------------------

# Lo que salió del formulario del estudiante y pasó a la entrevista (decisión
# 6). Al matricular se copia a las columnas que el estudiante ya tiene
# (decisión 7), para que la ficha lo lea en un solo lugar.
COLUMNAS_COPIADAS_A_ESTUDIANTE = (
    "colegio_anterior",
    "anio_cursado_anterior",
    "pre_escolar_anterior",
    "ebp_anterior",
    "motivo_retiro_anterior",
    "paz_salvo_anterior",
    "ocupacion_padre",
    "ocupacion_madre",
)


def guardar_resultado(cursor, admision_id, resultado, motivo):
    """Guarda el resultado y cuándo se decidió. Devuelve cuántas filas cambió.

    Volver a `pendiente` borra la fecha de la decisión. No cambia una admisión
    matriculada: en ese caso devuelve 0.
    """
    cursor.execute(
        """
        UPDATE admisiones
        SET resultado = %s, motivo_resultado = %s,
            decidido_en = CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END,
            actualizado_en = CURRENT_TIMESTAMP
        WHERE id = %s AND estudiante_id IS NULL
        """,
        (resultado, motivo, resultado != "pendiente", admision_id),
    )
    return cursor.rowcount


def copiar_datos_a_estudiante(cursor, admision_id, estudiante_id):
    """Copia a la ficha lo que pasó a la entrevista. Devuelve cuántas filas cambió.

    Un dato que la entrevista dejó vacío no borra el que el estudiante ya
    tenía (un exalumno, o lo que traiga la ficha): no se pierde nada.
    """
    asignaciones = ", ".join(
        f"{columna} = COALESCE(a.{columna}, e.{columna})"
        for columna in COLUMNAS_COPIADAS_A_ESTUDIANTE
    )
    cursor.execute(
        f"""
        UPDATE estudiantes e
        SET {asignaciones}
        FROM admisiones a
        WHERE a.id = %s AND e.id = %s
        """,
        (admision_id, estudiante_id),
    )
    return cursor.rowcount


def enlazar_estudiante(cursor, admision_id, estudiante_id):
    """Enlaza la admisión aprobada con su estudiante. Devuelve cuántas cambió.

    Desde aquí la admisión queda de solo consulta.
    """
    cursor.execute(
        """
        UPDATE admisiones
        SET estudiante_id = %s, actualizado_en = CURRENT_TIMESTAMP
        WHERE id = %s AND estudiante_id IS NULL AND resultado = 'aprobado'
        """,
        (estudiante_id, admision_id),
    )
    return cursor.rowcount
