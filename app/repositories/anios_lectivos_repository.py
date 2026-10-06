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


def leer_anio_lectivo_para_actualizar(cursor, anio_lectivo_id):
    """Lee y bloquea un año mientras se copia su configuración."""
    cursor.execute(
        "SELECT id, anio, estado FROM anios_lectivos WHERE id = %s FOR UPDATE",
        (anio_lectivo_id,),
    )
    return cursor.fetchone()


def buscar_choque_curso_para_copia(cursor, anio_origen_id, anio_destino_id):
    """Primer curso del origen cuyo nombre y jornada ya existen en destino."""
    cursor.execute(
        """
        SELECT origen.nombre, origen.jornada
        FROM cursos origen
        JOIN cursos destino
          ON destino.anio_lectivo_id = %s
         AND UPPER(REGEXP_REPLACE(TRIM(destino.nombre), '[[:space:]]+', ' ', 'g')) =
             UPPER(REGEXP_REPLACE(TRIM(origen.nombre), '[[:space:]]+', ' ', 'g'))
         AND LOWER(COALESCE(NULLIF(TRIM(destino.jornada), ''), 'Mañana')) =
             LOWER(COALESCE(NULLIF(TRIM(origen.jornada), ''), 'Mañana'))
        WHERE origen.anio_lectivo_id = %s
          AND COALESCE(LOWER(origen.estado), 'activo') = 'activo'
        ORDER BY origen.id
        LIMIT 1
        """,
        (anio_destino_id, anio_origen_id),
    )
    return cursor.fetchone()


def buscar_choque_concepto_para_copia(cursor, anio_origen_id, anio_destino_id):
    """Primer concepto del origen cuyo nombre ya existe en el destino."""
    cursor.execute(
        """
        SELECT origen.nombre
        FROM tipos_de_pagos origen
        JOIN tipos_de_pagos destino
          ON destino.anio_lectivo_id = %s
         AND LOWER(TRIM(destino.nombre)) = LOWER(TRIM(origen.nombre))
        WHERE origen.anio_lectivo_id = %s
        ORDER BY origen.id
        LIMIT 1
        """,
        (anio_destino_id, anio_origen_id),
    )
    return cursor.fetchone()


def _filas_como_diccionarios(filas, columnas):
    return [
        dict(fila) if isinstance(fila, dict) else dict(zip(columnas, fila))
        for fila in filas
    ]


def listar_cursos_para_copiar(cursor, anio_origen_id):
    """Datos de curso definidos por el contrato de la fase 5."""
    columnas = ("id", "nombre", "jornada", "nivel", "director_grupo_id")
    cursor.execute(
        """
        SELECT id, nombre, jornada, nivel, director_grupo_id
        FROM cursos
        WHERE anio_lectivo_id = %s
          AND COALESCE(LOWER(estado), 'activo') = 'activo'
        ORDER BY id
        """,
        (anio_origen_id,),
    )
    return _filas_como_diccionarios(cursor.fetchall(), columnas)


def insertar_curso_copiado(
    cursor, curso, anio_destino_id, copiar_director
):
    """Crea el curso activo del destino y conserva el id de su origen."""
    cursor.execute(
        """
        INSERT INTO cursos (
            nombre, jornada, estado, nivel, director_grupo_id,
            anio_lectivo_id, curso_origen_id
        )
        VALUES (%s, %s, 'activo', %s, %s, %s, %s)
        RETURNING id
        """,
        (
            curso["nombre"],
            curso["jornada"],
            curso["nivel"],
            curso["director_grupo_id"] if copiar_director else None,
            anio_destino_id,
            curso["id"],
        ),
    )
    return cursor.fetchone()[0]


_COLUMNAS_CONCEPTO_COPIA = (
    "id",
    "nombre",
    "valor",
    "descripcion",
    "tipo_cobro",
    "fecha_limite",
    "dia_limite_mes",
    "dias_gracia",
    "mora_tipo",
    "mora_valor",
    "mes_inicial",
    "mes_final",
    "frecuencia_meses",
    "generacion_automatica",
    "activo",
)


def listar_conceptos_para_copiar(cursor, anio_origen_id):
    """Todos los conceptos y toda su configuración financiera."""
    cursor.execute(
        """
        SELECT id, nombre, valor, descripcion, tipo_cobro, fecha_limite,
               dia_limite_mes, dias_gracia, mora_tipo, mora_valor,
               mes_inicial, mes_final, frecuencia_meses,
               generacion_automatica, activo
        FROM tipos_de_pagos
        WHERE anio_lectivo_id = %s
        ORDER BY id
        """,
        (anio_origen_id,),
    )
    return _filas_como_diccionarios(cursor.fetchall(), _COLUMNAS_CONCEPTO_COPIA)


def insertar_concepto_copiado(cursor, concepto, anio_destino_id):
    """Copia la configuración del concepto y conserva su origen."""
    cursor.execute(
        """
        INSERT INTO tipos_de_pagos (
            nombre, valor, descripcion, tipo_cobro, fecha_limite,
            dia_limite_mes, dias_gracia, mora_tipo, mora_valor,
            mes_inicial, mes_final, frecuencia_meses,
            generacion_automatica, activo, anio_lectivo_id,
            tipo_pago_origen_id
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s
        )
        RETURNING id
        """,
        (
            concepto["nombre"],
            concepto["valor"],
            concepto["descripcion"],
            concepto["tipo_cobro"],
            concepto["fecha_limite"],
            concepto["dia_limite_mes"],
            concepto["dias_gracia"],
            concepto["mora_tipo"],
            concepto["mora_valor"],
            concepto["mes_inicial"],
            concepto["mes_final"],
            concepto["frecuencia_meses"],
            concepto["generacion_automatica"],
            concepto["activo"],
            anio_destino_id,
            concepto["id"],
        ),
    )
    return cursor.fetchone()[0]


def listar_precios_para_copiar(cursor, anio_origen_id):
    """Precios cuyos conceptos y cursos pertenecen al año de origen."""
    columnas = ("tipo_pago_id", "curso_id", "valor", "activo")
    cursor.execute(
        """
        SELECT tpc.tipo_pago_id, tpc.curso_id, tpc.valor, tpc.activo
        FROM tipos_pagos_cursos tpc
        JOIN tipos_de_pagos tp ON tp.id = tpc.tipo_pago_id
        JOIN cursos c ON c.id = tpc.curso_id
        WHERE tp.anio_lectivo_id = %s
          AND c.anio_lectivo_id = %s
          AND COALESCE(LOWER(c.estado), 'activo') = 'activo'
        ORDER BY tpc.id
        """,
        (anio_origen_id, anio_origen_id),
    )
    return _filas_como_diccionarios(cursor.fetchall(), columnas)


def insertar_precio_copiado(cursor, precio, tipo_pago_id, curso_id):
    """Copia un precio apuntando al concepto y curso nuevos."""
    cursor.execute(
        """
        INSERT INTO tipos_pagos_cursos (tipo_pago_id, curso_id, valor, activo)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (tipo_pago_id, curso_id, precio["valor"], precio["activo"]),
    )
    return cursor.fetchone()[0]


_COLUMNAS_ASIGNACION_COPIA = (
    "id",
    "curso_id",
    "materia_id",
    "profesor_id",
    "dia",
    "horas",
    "hora_inicio",
    "hora_fin",
    "activo",
    "asignacion_academica_id",
    "orden_boletin",
)


def listar_asignaciones_para_copiar(cursor, anio_origen_id):
    """Carga académica completa de los cursos del año de origen."""
    cursor.execute(
        """
        SELECT a.id, a.curso_id, a.materia_id, a.profesor_id, a.dia, a.horas,
               a.hora_inicio, a.hora_fin, a.activo,
               a.asignacion_academica_id, a.orden_boletin
        FROM asignaciones a
        JOIN cursos c ON c.id = a.curso_id
        WHERE c.anio_lectivo_id = %s
          AND COALESCE(LOWER(c.estado), 'activo') = 'activo'
        ORDER BY a.id
        """,
        (anio_origen_id,),
    )
    return _filas_como_diccionarios(
        cursor.fetchall(), _COLUMNAS_ASIGNACION_COPIA
    )


def insertar_asignacion_copiada(cursor, asignacion, curso_id):
    """Copia una franja sin enlazarla todavía a una cabecera académica."""
    cursor.execute(
        """
        INSERT INTO asignaciones (
            curso_id, materia_id, profesor_id, dia, horas,
            hora_inicio, hora_fin, activo, orden_boletin
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            curso_id,
            asignacion["materia_id"],
            asignacion["profesor_id"],
            asignacion["dia"],
            asignacion["horas"],
            asignacion["hora_inicio"],
            asignacion["hora_fin"],
            asignacion["activo"],
            asignacion["orden_boletin"],
        ),
    )
    return cursor.fetchone()[0]


def enlazar_asignacion_academica_copiada(
    cursor, asignacion_id, asignacion_academica_id
):
    """Enlaza una franja nueva con la cabecera nueva de su grupo."""
    cursor.execute(
        """
        UPDATE asignaciones
        SET asignacion_academica_id = %s
        WHERE id = %s
        """,
        (asignacion_academica_id, asignacion_id),
    )


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
