"""Acceso a datos del año lectivo. Ver docs/funcionalidades/ANIO_LECTIVO.md.

Fase 1: lo minimo para que toda fila nueva nazca con su año. Como el resto de
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
