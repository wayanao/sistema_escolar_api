"""Acceso a datos del año lectivo. Ver docs/funcionalidades/ANIO_LECTIVO.md.

Fase 1: lo minimo para que toda fila nueva nazca con su año. Fase 2: leer un
año pedido, para cobrar en un año que no es el activo. Fase 3: listar los
años, para que el frontend sepa cuales hay y cual es el activo,
`condicion_anio`, el filtro por año que comparten los listados, en que años
se dicta una materia (aviso al renombrarla) y el año de una clase, un plan o
una anotacion (guardia de escritura). Como el resto de
repositorios, cada funcion recibe el cursor de quien llama y no abre, confirma
ni cierra nada.
"""

# Id del año activo como subconsulta, para escribirlo dentro del mismo INSERT
# sin una ida extra a la base. Es una constante del codigo, no entrada del
# usuario, asi que se puede interpolar en el SQL.
#
# Vale NULL si el tenant no tiene año activo (un colegio dado de alta antes de
# que el alta lo sembrara). La columna todavia lo admite; la migracion B
# inserta el año que falte antes de volverla obligatoria.
ANIO_ACTIVO_ID_SQL = "(SELECT id FROM anios_lectivos WHERE estado = 'activo')"


def condicion_anio(columna, anio_lectivo_id=None):
    """Condicion de `WHERE` que deja solo las filas de un año, y sus parametros.

    Sin `anio_lectivo_id`, el año activo como subconsulta y **ningun
    parametro**: la consulta de hoy, que no manda año, conserva sus
    parametros y no gasta una ida extra a la base. Con el, `%s` y el id.

    `columna` es un nombre escrito en el codigo (por ejemplo
    `"c.anio_lectivo_id"`), nunca entrada del cliente.
    """
    if anio_lectivo_id is None:
        return f"{columna} = {ANIO_ACTIVO_ID_SQL}", ()
    return f"{columna} = %s", (anio_lectivo_id,)


def sincronizar_matricula_del_anio_activo(cursor, estudiante_id):
    """Deja la matricula del año activo igual al curso actual del estudiante.

    En la fase 1 `estudiantes.curso_id` sigue siendo lo que edita el
    formulario, asi que la matricula del año activo es su copia: se crea si
    falta y se corrige si el curso cambio. El año sale del curso, como en la
    migracion A, para coincidir siempre con la clave foranea compuesta.

    No hace nada si el curso no es del año activo (un curso creado antes de
    desplegar este codigo, todavia sin año): la migracion B lo sincroniza.
    Nunca borra: el curso es obligatorio en el formulario, asi que un
    estudiante no se queda sin curso.
    """
    cursor.execute(
        """
        INSERT INTO matriculas (estudiante_id, curso_id, anio_lectivo_id)
        SELECT e.id, e.curso_id, c.anio_lectivo_id
        FROM estudiantes e
        JOIN cursos c ON c.id = e.curso_id
        JOIN anios_lectivos al ON al.id = c.anio_lectivo_id
        WHERE e.id = %s
          AND al.estado = 'activo'
        ON CONFLICT (estudiante_id, anio_lectivo_id)
        DO UPDATE SET curso_id = EXCLUDED.curso_id
        """,
        (estudiante_id,),
    )


def leer_anio_lectivo(cursor, anio_lectivo_id):
    """El año lectivo pedido como `(id, anio, estado)`, o `None` si no existe.

    Siempre como tupla, tambien con un cursor de diccionarios
    (`RealDictCursor`, el que usan boletin y conceptos de pago), igual que
    `_columnas_existentes` de `tipos_pagos_controller`.
    """
    cursor.execute(
        "SELECT id, anio, estado FROM anios_lectivos WHERE id = %s",
        (anio_lectivo_id,),
    )
    fila = cursor.fetchone()
    if isinstance(fila, dict):
        return (fila["id"], fila["anio"], fila["estado"])
    return fila


def leer_anio_de_curso(cursor, curso_id):
    """El año lectivo del curso como `(id, estado)`, o `None` si el curso no existe."""
    cursor.execute(
        """
        SELECT c.anio_lectivo_id, al.estado
        FROM cursos c
        JOIN anios_lectivos al ON al.id = c.anio_lectivo_id
        WHERE c.id = %s
        """,
        (curso_id,),
    )
    return cursor.fetchone()


def _anio_y_estado(cursor, sql, params):
    """Ejecuta una lectura de `(anio, estado)` y la devuelve como tupla o `None`.

    Siempre como tupla, tambien con un cursor de diccionarios, como
    `leer_anio_lectivo`.
    """
    cursor.execute(sql, params)
    fila = cursor.fetchone()
    if isinstance(fila, dict):
        return (fila["anio"], fila["estado"])
    return fila


def leer_anio_de_asignacion(cursor, asignacion_id):
    """El año de una clase como `(anio, estado)`, o `None` si no existe.

    El año sale del curso de la clase. Lo usa la guardia de escritura del paso
    3.7 para notas, planilla, asistencia, boletin, observaciones, planeador y
    planes de clase.
    """
    return _anio_y_estado(
        cursor,
        """
        SELECT al.anio, al.estado
        FROM asignaciones a
        JOIN cursos c ON c.id = a.curso_id
        JOIN anios_lectivos al ON al.id = c.anio_lectivo_id
        WHERE a.id = %s
        """,
        (asignacion_id,),
    )


def leer_anio_de_plan(cursor, plan_id):
    """El año de un plan de clases como `(anio, estado)`, o `None` si no existe."""
    return _anio_y_estado(
        cursor,
        """
        SELECT al.anio, al.estado
        FROM plan_de_clases p
        JOIN asignaciones a ON a.id = p.asignacion_id
        JOIN cursos c ON c.id = a.curso_id
        JOIN anios_lectivos al ON al.id = c.anio_lectivo_id
        WHERE p.id = %s
        """,
        (plan_id,),
    )


def leer_anio_de_anotacion(cursor, anotacion_id):
    """El año de una anotacion del observador como `(anio, estado)`, o `None`.

    La anotacion no cuelga de un curso: guarda su propio año.
    """
    return _anio_y_estado(
        cursor,
        """
        SELECT al.anio, al.estado
        FROM observador_anotaciones o
        JOIN anios_lectivos al ON al.id = o.anio_lectivo_id
        WHERE o.id = %s
        """,
        (anotacion_id,),
    )


def leer_nombre_y_anios_de_materia(cursor, materia_id):
    """El nombre guardado de una materia y los años en que se dicta.

    Devuelve `(nombre, [(anio, estado), ...])`, un año por fila y de menor a
    mayor, o `None` si la materia no existe. Una materia sin clases trae la
    lista vacia. Cuenta todas sus clases (asignaciones), tambien las
    inactivas: sus notas siguen ahi, y ante la duda es mejor avisar de mas
    (paso 3.6, decision 12).
    """
    cursor.execute(
        """
        SELECT m.nombre, al.anio, al.estado
        FROM materias m
        LEFT JOIN asignaciones a ON a.materia_id = m.id
        LEFT JOIN cursos c ON c.id = a.curso_id
        LEFT JOIN anios_lectivos al ON al.id = c.anio_lectivo_id
        WHERE m.id = %s
        GROUP BY m.nombre, al.anio, al.estado
        ORDER BY al.anio
        """,
        (materia_id,),
    )
    filas = cursor.fetchall()
    if not filas:
        return None
    return filas[0][0], [(anio, estado) for _, anio, estado in filas if anio is not None]


def listar_anios_lectivos(cursor):
    """Todos los años lectivos como `(id, anio, estado)`, el mas reciente primero.

    El mas reciente primero porque es el orden de un selector de año: el que
    se prepara, luego el activo, luego los cerrados.
    """
    cursor.execute("SELECT id, anio, estado FROM anios_lectivos ORDER BY anio DESC")
    return cursor.fetchall()


def leer_anio_activo(cursor):
    """El año activo como `(id, anio, estado)`, o `None` si el colegio no tiene."""
    cursor.execute(
        "SELECT id, anio, estado FROM anios_lectivos WHERE estado = 'activo'"
    )
    return cursor.fetchone()


def crear_anio_activo_inicial(cursor, anio):
    """Siembra el año activo de un colegio recien creado.

    El esquema base es solo estructura: trae la tabla pero no la fila.
    """
    cursor.execute(
        """
        INSERT INTO anios_lectivos (anio, estado, activado_en)
        VALUES (%s, 'activo', CURRENT_TIMESTAMP)
        """,
        (anio,),
    )
