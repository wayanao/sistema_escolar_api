"""Escrituras de `asignaciones`, extraidas en la subcapa 6.3.

Cada funcion recibe el cursor que ya abrio el controlador y ejecuta una sola
sentencia. Ninguna abre, cierra, confirma ni revierte recursos: la propiedad de
la conexion, el cursor, el `commit`, el `rollback`, las validaciones de estado,
horario, jornada y cruce, la comprobacion de historial academico y la traduccion
de `IntegrityError` a `AsignacionDuplicadaError` siguen siendo del controlador.

Dos funciones **no hacen `fetchone`** aunque su SQL lleve `RETURNING id`:
`insertar_asignacion` y `actualizar_asignacion`. En el controlador el `execute`
vive dentro de un `try/except IntegrityError` y la lectura del resultado ocurre
**despues** de ese bloque, para que un duplicado se traduzca antes de leer. Mover
el `fetchone` aqui cambiaria ese orden, asi que se deja donde estaba.

Las cadenas SQL se conservan con su texto original, incluida la sangria, para que
lo que recibe PostgreSQL no cambie. Ver la nota de `desactivar_asignacion_por_id`
sobre las dos formas de la misma sentencia.
"""


def insertar_asignacion(cursor, valores):
    """Inserta la asignacion. **No lee el resultado**: ver el docstring del modulo.

    `activo` va fijo a TRUE en el texto de la sentencia, no como parametro.
    """
    cursor.execute("""
                INSERT INTO asignaciones (
                    profesor_id,
                    curso_id,
                    materia_id,
                    dia,
                    hora_inicio,
                    hora_fin,
                    activo,
                    asignacion_academica_id,
                    orden_boletin
                )
                VALUES (%s, %s, %s, %s, %s, %s, TRUE, %s, %s)
                RETURNING id
            """, valores)


def apuntar_asignacion_a_si_misma(cursor, asignacion_id):
    """Hace que la primera asignacion de un grupo sea su propia cabecera.

    Solo se ejecuta cuando el alta no encontro una asignacion academica previa
    para ese profesor, curso y materia.
    """
    cursor.execute(
        """
                UPDATE asignaciones
                SET asignacion_academica_id = id
                WHERE id = %s
                """,
        (asignacion_id,),
    )


def actualizar_asignacion(cursor, valores):
    """Actualiza la asignacion activa. **No lee el resultado**: ver el modulo.

    El `AND activo = TRUE` es parte del contrato: una asignacion desactivada no
    se edita, y el `RETURNING` vacio es lo que el controlador traduce a «no
    encontrada».
    """
    cursor.execute("""
                UPDATE asignaciones
                SET profesor_id = %s,
                    curso_id = %s,
                    materia_id = %s,
                    dia = %s,
                    hora_inicio = %s,
                    hora_fin = %s,
                    asignacion_academica_id = %s
                WHERE id = %s
                  AND activo = TRUE
                RETURNING id
            """, valores)


def desactivar_asignacion(cursor, asignacion_id):
    """Desactiva la asignacion localizada por profesor y curso.

    Nunca borra: el historial academico cuelga de esta fila por seis claves
    foraneas.
    """
    cursor.execute("""
            UPDATE asignaciones
            SET activo = FALSE
            WHERE id = %s
        """, (asignacion_id,))


def desactivar_asignacion_por_id(cursor, asignacion_id):
    """Desactiva la asignacion indicada por su id.

    Su SQL es **la misma sentencia** que `desactivar_asignacion` con otro
    formato: aquella la escribe en cuatro lineas y esta en una. El flujo de
    tokens que recibe PostgreSQL es identico, pero unificarlas cambiaria uno de
    los dos literales, y eso es una decision del usuario, no del asistente. 6.3
    conserva las dos formas tal como estaban.
    """
    cursor.execute("UPDATE asignaciones SET activo = FALSE WHERE id = %s", (asignacion_id,))


def reiniciar_orden_boletin(cursor, curso_id):
    """Devuelve todas las materias activas del curso al orden por defecto, 100.

    Es la primera mitad del reemplazo completo que hace el endpoint de orden: se
    reinicia todo y despues se numera lo enviado.
    """
    cursor.execute(
        """
            UPDATE asignaciones
            SET orden_boletin = 100
            WHERE curso_id = %s
              AND activo = TRUE
            """,
        (curso_id,),
    )


def fijar_orden_boletin_materia(cursor, posicion, curso_id, materia_id):
    """Coloca una materia del curso en su posicion del boletin.

    Se ejecuta una vez por materia enviada, asi que el coste del endpoint crece
    con el numero de materias reordenadas.
    """
    cursor.execute(
        """
                UPDATE asignaciones
                SET orden_boletin = %s
                WHERE curso_id = %s
                  AND materia_id = %s
                  AND activo = TRUE
                """,
        (posicion, curso_id, materia_id),
    )


# ---------------------------------------------------------------------------
# Precondiciones de una asignacion
#
# Lecturas sobre `profesor`, `cursos` y `materias`, extraidas en 6.4. No son
# persistencia de esos catalogos: son las preguntas que hay que responder antes
# de poder asignar. Viven aqui por la decision tomada en 6.4 con evidencia, la
# misma que 6.2 aplico al expediente del estudiante: no existe un repositorio de
# esos dominios, y el patron de estado activo que usan solo aparece en este
# controlador, asi que uno nuevo tendria un solo consumidor real.
# ---------------------------------------------------------------------------


def buscar_profesor_activo(cursor, profesor_id):
    """Fila testigo si el profesor existe y esta activo. `None` si no."""
    cursor.execute(
        """
        SELECT 1
        FROM profesor
        WHERE id = %s
          AND COALESCE(LOWER(estado), 'activo') = 'activo'
        """,
        (profesor_id,),
    )
    return cursor.fetchone()


def buscar_curso_activo(cursor, curso_id):
    """Fila testigo si el curso existe y esta activo. `None` si no."""
    cursor.execute(
        """
        SELECT 1
        FROM cursos
        WHERE id = %s
          AND COALESCE(LOWER(estado), 'activo') = 'activo'
        """,
        (curso_id,),
    )
    return cursor.fetchone()


def buscar_materia_activa(cursor, materia_id):
    """Fila testigo si la materia existe y esta activa. `None` si no."""
    cursor.execute(
        """
        SELECT 1
        FROM materias
        WHERE id = %s
          AND COALESCE(LOWER(estado), 'activo') = 'activo'
        """,
        (materia_id,),
    )
    return cursor.fetchone()


def leer_jornada_curso(cursor, curso_id):
    """Jornada declarada del curso, o `None` si el curso no existe.

    Un curso sin jornada no restringe el horario; quien interpreta eso es el
    controlador.
    """
    cursor.execute("SELECT jornada FROM cursos WHERE id = %s", (curso_id,))
    return cursor.fetchone()


def buscar_curso_activo_para_orden(cursor, curso_id):
    """Fila testigo del curso activo antes de reordenar su boletin.

    Su texto es igual al de `buscar_curso_activo` salvo la sangria, heredada de
    estar una en una funcion suelta y otra dentro de un `try`. **No se
    unificaron**: es el mismo caso que las dos formas de `SET activo = FALSE` de
    6.3, y unificar literales es una decision del usuario.
    """
    cursor.execute(
        """
            SELECT 1
            FROM cursos
            WHERE id = %s
              AND COALESCE(LOWER(estado), 'activo') = 'activo'
            """,
        (curso_id,),
    )
    return cursor.fetchone()


# ---------------------------------------------------------------------------
# Validaciones de unicidad y de cruce de horario
#
# Todas reciben ya construido el fragmento opcional del filtro, y el nombre de
# columna de las dos primeras llega ya validado contra un conjunto cerrado en el
# controlador. **Ninguno de esos fragmentos es entrada del cliente**, y ninguna
# extraccion futura debe abrirlos a ella.
# ---------------------------------------------------------------------------


def leer_horarios_del_dia(cursor, campo_id, valor_id, dia):
    """Horarios activos de un profesor o de un curso en un dia."""
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
    return cursor.fetchall()


def leer_horarios_del_dia_excluyendo(cursor, campo_id, valor_id, dia, asignacion_id_ignorar):
    """Igual que la anterior, pero sin contar la asignacion que se esta editando."""
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
    return cursor.fetchall()


def buscar_responsable_de_materia(cursor, filtro_asignacion, params):
    """Nombre del profesor que ya tiene esa materia en ese curso, si es otro."""
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
    return cursor.fetchone()


def buscar_horario_identico(cursor, filtro_asignacion, params):
    """Fila testigo si ya existe ese mismo horario para profesor, curso y materia.

    Usa `IS NOT DISTINCT FROM` para que dos nulos cuenten como iguales.
    """
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
    return cursor.fetchone()


def buscar_asignacion_academica(cursor, filtro_asignacion, params):
    """Cabecera academica ya existente para ese profesor, curso y materia."""
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
    return cursor.fetchone()


def leer_horarios_ocupados(cursor, filtro_excluir, params):
    """Franjas ocupadas de un profesor en un dia, ordenadas y sin vacios.

    El calculo de los rangos libres a partir de estas franjas se queda en el
    controlador: es aritmetica, no persistencia.
    """
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
    return cursor.fetchall()


# ---------------------------------------------------------------------------
# Lecturas de asignaciones
# ---------------------------------------------------------------------------


def leer_orden_boletin_materia(cursor, curso_id, materia_id):
    """Orden que ya tiene esa materia en el curso, o el 100 por defecto."""
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
    return cursor.fetchone()


def leer_orden_boletin_curso(cursor, curso_id):
    """Materias del curso agrupadas, con su orden y cuantos horarios tienen."""
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
    return cursor.fetchall()


def leer_materias_asignadas(cursor, curso_id):
    """Materias que hoy tienen asignacion activa en el curso."""
    cursor.execute(
        """
            SELECT DISTINCT materia_id
            FROM asignaciones
            WHERE curso_id = %s
              AND activo = TRUE
            """,
        (curso_id,),
    )
    return cursor.fetchall()


def leer_cursos_de_profesor(cursor, profesor_id):
    """Cursos activos en los que el profesor tiene alguna materia activa."""
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
    return cursor.fetchall()


def leer_profesores_de_curso(cursor, curso_id):
    """Profesores con alguna materia activa en el curso."""
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
    return cursor.fetchall()


def leer_horarios_admin(cursor):
    """Todos los horarios completos, ordenados por dia de la semana y hora.

    El `CASE` sobre el nombre del dia es lo que da el orden: los dias se guardan
    como texto en espanol, con tilde en «Miércoles» y «Sábado».
    """
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
    return cursor.fetchall()


def buscar_ultima_asignacion_activa(cursor, profesor_id, curso_id):
    """Asignacion activa mas reciente de ese profesor en ese curso."""
    cursor.execute("""
            SELECT id FROM asignaciones
            WHERE profesor_id = %s AND curso_id = %s AND activo = TRUE
            ORDER BY id DESC
            LIMIT 1
        """, (profesor_id, curso_id))
    return cursor.fetchone()


def buscar_asignacion_activa(cursor, asignacion_id):
    """Fila testigo si la asignacion existe y esta activa."""
    cursor.execute("SELECT id FROM asignaciones WHERE id = %s AND activo = TRUE", (asignacion_id,))
    return cursor.fetchone()


def leer_asignacion_para_editar(cursor, asignacion_id):
    """Estado actual de la asignacion: relacion academica, activo y cabecera.

    El controlador compara estos tres primeros valores con los entrantes para
    decidir si la edicion cambia la relacion academica, que es lo que dispara la
    comprobacion de historial.
    """
    cursor.execute("""
            SELECT profesor_id, curso_id, materia_id, activo, COALESCE(asignacion_academica_id, id)
            FROM asignaciones
            WHERE id = %s
        """, (asignacion_id,))
    return cursor.fetchone()


def leer_clases_de_profesor(cursor, profesor_id):
    """Clases activas del profesor con curso y materia.

    Sirve a `obtener_clases_profesor_controller`, que 6.0 demostro que **no tiene
    consumidores de produccion**. Su SQL se movio igualmente para no dejar
    lecturas inline en el controlador; retirar la funcion muerta exige una
    decision explicita del usuario y sigue pendiente.
    """
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
    return cursor.fetchall()


def leer_todas_las_asignaciones(cursor):
    """Listado heredado sin paginar, mas reciente primero."""
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
    return cursor.fetchall()


def contar_asignaciones(cursor, where_sql, params):
    """Total que acompana a la respuesta paginada."""
    cursor.execute(f"""
            SELECT COUNT(*)
            FROM asignaciones a
            JOIN profesor p ON a.profesor_id = p.id
            JOIN cursos c ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            {where_sql}
        """, params)
    return cursor.fetchone()


def leer_asignaciones_paginado(cursor, where_sql, params):
    """Pagina del listado. El `where_sql` es el mismo que uso el conteo."""
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
        """, params)
    return cursor.fetchall()


# ---------------------------------------------------------------------------
# El historial academico que cuelga de una asignacion
#
# Una sola lectura, repetida sobre siete tablas de otros dominios, que responde
# si una asignacion ya tiene pasado academico. Viene aqui por la decision de 6.4:
# es una pregunta sobre datos, y su sitio es la frontera de persistencia. La
# pregunta hermana, la que consulta `information_schema.columns` para saber si la
# tabla tiene la columna, **se queda en el controlador** por la convencion que
# 5.3 fijo con evidencia: la introspeccion de esquema vive junto al codigo que la
# necesita.
# ---------------------------------------------------------------------------


def leer_clases_con_horario_de_profesor(cursor, profesor_id):
    """Clases del profesor con su horario, curso, jornada y materia.

    Extraida en 6.5 desde `app/routes/asignaciones.py`, donde era **el unico SQL
    de dominio que vivia en la capa HTTP** de todo el programa. La ruta conserva
    el `get_cursor`, la comprobacion de permisos y el formateo del payload.

    Devuelve dos identificadores distintos y **no son intercambiables**: el
    primero resuelve la cabecera academica del grupo con el mismo `CASE` que
    `resolver_asignacion_academica_id_cursor`, y `horario_id` es la fila concreta
    de este horario. El frontend usa el primero para notas y boletines, y el
    segundo para editar la franja.
    """
    cursor.execute("""
            SELECT
                CASE
                    WHEN base.id IS NOT NULL
                     AND base.profesor_id = a.profesor_id
                     AND base.curso_id = a.curso_id
                     AND base.materia_id = a.materia_id
                        THEN base.id
                    ELSE a.id
                END AS asignacion_id,
                a.id AS horario_id,
                m.nombre AS materia,
                c.nombre AS curso,
                c.id AS curso_id,
                c.jornada,
                a.dia,
                a.hora_inicio,
                a.hora_fin

            FROM asignaciones a
            JOIN materias m ON a.materia_id = m.id
            JOIN cursos c ON a.curso_id = c.id
            LEFT JOIN asignaciones base ON base.id = a.asignacion_academica_id

            WHERE a.profesor_id = %s
              AND a.activo = TRUE
              AND COALESCE(LOWER(c.estado), 'activo') = 'activo'
              AND COALESCE(LOWER(m.estado), 'activo') = 'activo'
            ORDER BY
                c.nombre,
                m.nombre,
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
        """, (profesor_id,))
    return cursor.fetchall()


def buscar_historial_en_tabla(cursor, tabla, asignacion_id):
    """Fila testigo si esa tabla tiene historial de la asignacion.

    El nombre de tabla llega interpolado desde la lista fija del controlador y
    **nunca** desde entrada del cliente. Ninguna extraccion futura debe abrirlo.
    """
    cursor.execute(f"SELECT 1 FROM {tabla} WHERE asignacion_id = %s LIMIT 1", (asignacion_id,))
    return cursor.fetchone()
