"""Acceso a datos del año lectivo. Ver docs/funcionalidades/ANIO_LECTIVO.md.

Fase 1: lo minimo para que toda fila nueva nazca con su año. Fase 2: leer un
año pedido, para cobrar en un año que no es el activo. Fase 3: listar los
años, para que el frontend sepa cuales hay y cual es el activo,
`condicion_anio`, el filtro por año que comparten los listados, en que años
se dicta una materia (aviso al renombrarla) y el año de una clase, un plan,
una anotacion, un curso o un concepto (guardia de escritura). Como el resto de
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


def matricular_en_curso_del_anio_activo(cursor, estudiante_id, curso_id):
    """Crea o corrige la matricula activa solo si el curso pertenece a ella.

    El `INSERT ... SELECT` hace la validacion y la escritura en una sola
    sentencia. Si el curso no existe o no es del año activo, no inserta nada y
    devuelve `False`; quien llama revierte toda la transaccion.
    """
    cursor.execute(
        """
        INSERT INTO matriculas (estudiante_id, curso_id, anio_lectivo_id)
        SELECT %s, c.id, c.anio_lectivo_id
        FROM cursos c
        JOIN anios_lectivos al ON al.id = c.anio_lectivo_id
        WHERE c.id = %s
          AND al.estado = 'activo'
        ON CONFLICT (estudiante_id, anio_lectivo_id)
        DO UPDATE SET curso_id = EXCLUDED.curso_id
        RETURNING matriculas.curso_id
        """,
        (estudiante_id, curso_id),
    )
    return cursor.fetchone() is not None


def sincronizar_curso_vigente(cursor, estudiante_id):
    """Copia al estudiante el curso de su matricula del año activo.

    Esta es la unica escritura de `estudiantes.curso_id` en la aplicacion. Si
    el estudiante no tiene matricula activa, el valor queda en `NULL`; eso es
    lo que necesitara un estudiante creado solo para un año en preparacion.
    """
    cursor.execute(
        """
        WITH curso_vigente AS (
            SELECT e.id AS estudiante_id, m.curso_id
            FROM estudiantes e
            LEFT JOIN anios_lectivos al ON al.estado = 'activo'
            LEFT JOIN matriculas m
              ON m.estudiante_id = e.id
             AND m.anio_lectivo_id = al.id
            WHERE e.id = %s
        )
        UPDATE estudiantes e
        SET curso_id = cv.curso_id
        FROM curso_vigente cv
        WHERE e.id = cv.estudiante_id
          AND e.curso_id IS DISTINCT FROM cv.curso_id
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


def leer_anios_de_cursos(cursor, curso_ids):
    """Los años de uno o varios cursos, como lista de `(anio, estado)`.

    Una fila por curso, en una sola consulta; los cursos que no existen no
    aportan fila. Varios cursos a la vez sirve para editar una clase, que toca
    su curso de antes y el nuevo.
    """
    cursor.execute(
        """
        SELECT al.anio, al.estado
        FROM cursos c
        JOIN anios_lectivos al ON al.id = c.anio_lectivo_id
        WHERE c.id = ANY(%s)
        """,
        (list(curso_ids),),
    )
    return [
        (fila["anio"], fila["estado"]) if isinstance(fila, dict) else tuple(fila)
        for fila in cursor.fetchall()
    ]


def leer_anio_de_concepto(cursor, tipo_pago_id):
    """El año de un concepto de pago como `(anio, estado)`, o `None` si no existe.

    El concepto guarda su propio año (decision 17).
    """
    return _anio_y_estado(
        cursor,
        """
        SELECT al.anio, al.estado
        FROM tipos_de_pagos tp
        JOIN anios_lectivos al ON al.id = tp.anio_lectivo_id
        WHERE tp.id = %s
        """,
        (tipo_pago_id,),
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


def leer_anio_activo_para_actualizar(cursor):
    """El año activo, bloqueado mientras se crea el siguiente.

    Dos peticiones de creación quedan así en fila sobre el mismo año activo.
    La segunda verá el año en preparación que dejó la primera y no intentará
    crear otro.
    """
    cursor.execute(
        "SELECT id, anio, estado FROM anios_lectivos "
        "WHERE estado = 'activo' FOR UPDATE"
    )
    return cursor.fetchone()


def leer_anio_en_preparacion(cursor):
    """El único año en preparación, o `None` si todavía no existe."""
    cursor.execute(
        "SELECT id, anio, estado FROM anios_lectivos WHERE estado = 'preparacion'"
    )
    return cursor.fetchone()


def crear_anio_en_preparacion(cursor, anio):
    """Crea un año en preparación y devuelve `(id, anio, estado)`.

    Los índices únicos de la tabla son la última defensa ante una carrera o
    ante un año ya existente. `DO NOTHING` permite traducir el choque a un
    error de negocio sin dejar abortada la transacción.
    """
    cursor.execute(
        """
        INSERT INTO anios_lectivos (anio, estado)
        VALUES (%s, 'preparacion')
        ON CONFLICT DO NOTHING
        RETURNING id, anio, estado
        """,
        (anio,),
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
