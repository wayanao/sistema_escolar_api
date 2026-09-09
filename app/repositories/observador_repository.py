"""Lectura de `observador_anotaciones`, la bitacora del observador.

Ver `docs/funcionalidades/OBSERVADOR_ESTUDIANTE.md`. Como los demas
repositorios, recibe el cursor que ya abrio quien llama y no abre, cierra,
confirma ni revierte nada.

**Una sola consulta, siempre.** Es el motivo de existir de esta funcionalidad:
la pantalla vieja hacia una peticion HTTP por alumno y con 12 tardaba 16-20 s,
por encima del limite de 10 s del frontend. Aqui se abre **un** estudiante y su
bitacora entera sale de una consulta. Contra Neon (`us-east-1`) cada ida y
vuelta cuesta ~180 ms se consulte lo que se consulte, asi que lo que hay que
vigilar es **cuantas** consultas se hacen, no lo complicada que sea cada una.
Si alguien anade aqui una segunda consulta, que sea sabiendo eso.

El nombre del profesor sale de la misma union y no de una consulta aparte. Ese
`JOIN` es interno: `profesor_id` es `NOT NULL` y su clave foranea no lleva
`ON DELETE CASCADE` ni `SET NULL`, asi que PostgreSQL **impide** borrar un
profesor con anotaciones. La fila siempre existe. Dar de baja a un profesor en
esta aplicacion es cambiarle el `estado`, no borrarlo.

La materia es una **etiqueta copiada** en la propia fila, no una union con
`materias`: si manana quitan esa materia del horario, la anotacion conserva el
texto. Tambien ahorra la union.
"""

# La consulta arranca en `estudiantes`, no en las anotaciones, y eso es lo unico
# que hay que entender de este modulo.
#
# La pantalla necesita el nivel del curso para decidir si muestra la materia
# (preescolar la omite, primaria la lleva en capsula). Si la consulta arrancara
# en `observador_anotaciones`, un alumno **sin anotaciones** devolveria cero
# filas y con ellas ningun nivel: la pantalla no podria ni escribir su titulo.
# Y ese no es un caso raro -hoy es el caso de TODOS los alumnos, porque la
# escritura todavia no existe-.
#
# Arrancando en el estudiante siempre vuelve al menos una fila. Si no tiene
# anotaciones, las columnas de la anotacion llegan en `NULL` y quien llama las
# descarta mirando `id`.
#
# Las dos uniones anadidas son `LEFT` a proposito:
#   - `cursos`, porque `estudiantes.curso_id` es NULABLE. Con un `JOIN` normal,
#     un alumno sin curso desapareceria de su propia bitacora: sin error, sin
#     aviso, simplemente vacia.
#   - `observador_anotaciones`, que es justo lo que permite el caso de arriba.
#
# Ninguna de las dos anade una ida y vuelta: siguen siendo una sola consulta.
_SELECT = """
    SELECT c.nivel,
           a.id,
           a.profesor_id,
           p.nombre,
           p.apellido,
           a.materia,
           a.periodo,
           a.positiva,
           a.conductual,
           a.cognitivo,
           a.lenguaje,
           a.creada_en,
           a.editada_en,
           a.editada_por
    FROM estudiantes e
    LEFT JOIN cursos c ON c.id = e.curso_id
    LEFT JOIN observador_anotaciones a
           ON a.estudiante_id = e.id
"""

# El filtro de periodo va en el ON de la union, NO en el WHERE. En el WHERE
# descartaria tambien la fila del estudiante cuando ese periodo no tuviera
# anotaciones, y volveriamos a quedarnos sin nivel.
_FILTRO_PERIODO = "          AND a.periodo = %s\n"

_RESTO = """
    LEFT JOIN profesor p ON p.id = a.profesor_id
    WHERE e.id = %s
    ORDER BY a.creada_en DESC NULLS LAST, a.id DESC NULLS LAST
"""


def leer_bitacora(cursor, estudiante_id, periodo=None):
    """El nivel del curso del estudiante y todas sus anotaciones.

    Devuelve las filas crudas. Quien llama distingue las anotaciones reales de
    la fila de relleno mirando si el `id` -la segunda columna- es `None`, y
    saca el nivel de la primera columna de cualquier fila.

    Devuelve **lista vacia solo si el estudiante no existe**. Un alumno real sin
    anotaciones devuelve exactamente una fila, con el nivel y el resto en
    `NULL`. Esa diferencia es la que deja distinguir «no existe» de «todavia no
    tiene nada escrito», que en pantalla son mensajes distintos.

    `periodo` es **opcional a proposito**: sin el devuelve el ano entero. El
    periodo es una etiqueta de cada anotacion, no un filtro obligatorio, y
    cambiar de periodo en la pantalla nunca puede ocultar historial. Es el
    invariante 5 del documento.

    El desempate por `id DESC` no es adorno: dos anotaciones guardadas en la
    misma transaccion comparten `creada_en` al milisegundo, porque `now()` es el
    instante de la transaccion y no el de la fila. Sin el, su orden entre si
    quedaria a criterio de PostgreSQL y podria cambiar entre dos lecturas
    identicas.
    """
    if periodo is None:
        cursor.execute(_SELECT + _RESTO, (estudiante_id,))
    else:
        cursor.execute(
            _SELECT + _FILTRO_PERIODO + _RESTO,
            (periodo, estudiante_id),
        )
    return cursor.fetchall()


def crear_anotacion(
    cursor,
    estudiante_id,
    profesor_id,
    periodo,
    positiva,
    conductual,
    cognitivo,
    lenguaje,
):
    """Inserta una anotacion nueva y devuelve su id.

    `profesor_id` lo pone quien llama a partir del token, **nunca** del cuerpo
    de la peticion: es el invariante 4 del documento.

    `materia` no se toca: se queda en su valor por defecto, la cadena vacia. Por
    ahora no se rellena, y el motivo esta en el documento.

    El `commit` es de quien llama, como en los demas repositorios.
    """
    cursor.execute(
        """
        INSERT INTO observador_anotaciones (
            estudiante_id, profesor_id, periodo, positiva,
            conductual, cognitivo, lenguaje
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (estudiante_id, profesor_id, periodo, positiva, conductual, cognitivo, lenguaje),
    )
    return cursor.fetchone()[0]


def actualizar_anotacion_del_autor(
    cursor,
    anotacion_id,
    profesor_id,
    positiva,
    conductual,
    cognitivo,
    lenguaje,
):
    """Actualiza la anotacion **solo si la escribio ese profesor**.

    Devuelve `True` si actualizo, `False` si no habia ninguna fila que
    cumpliera las dos condiciones. Quien llama distingue entonces «no existe»
    de «no es tuya» con una segunda consulta, que solo se paga en el camino de
    error.

    El `profesor_id` va en el `WHERE`, no en un `if` previo: asi la comprobacion
    de autoria y la escritura son **la misma sentencia**, y no hay ventana entre
    comprobar y escribir. Es tambien el invariante 3 -el admin no edita
    anotaciones de profesores-, porque el id de un admin sale de `usuarios` y
    nunca coincidira con el autor... salvo por casualidad numerica, que es justo
    lo que el guard de la ruta impide antes de llegar aqui.

    Editar **siempre deja rastro**: `editada_en` y `editada_por` se fijan en la
    misma sentencia, sin depender de que quien llame se acuerde. Es el
    invariante 2.
    """
    cursor.execute(
        """
        UPDATE observador_anotaciones
           SET positiva = %s,
               conductual = %s,
               cognitivo = %s,
               lenguaje = %s,
               editada_en = now(),
               editada_por = %s
         WHERE id = %s AND profesor_id = %s
        RETURNING id
        """,
        (positiva, conductual, cognitivo, lenguaje, profesor_id, anotacion_id, profesor_id),
    )
    return cursor.fetchone() is not None


def leer_autor(cursor, anotacion_id):
    """El `profesor_id` que escribio la anotacion, o `None` si no existe.

    **Solo se usa en el camino de error de la edicion**, para distinguir un 404
    de un 403. En el camino normal no se ejecuta, asi que guardar sigue
    costando una sola ida y vuelta.
    """
    cursor.execute(
        "SELECT profesor_id FROM observador_anotaciones WHERE id = %s",
        (anotacion_id,),
    )
    fila = cursor.fetchone()
    return fila[0] if fila else None
