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

El nombre del profesor sale de la misma union y no de una consulta aparte. El
`JOIN` es interno y no `LEFT`: `profesor_id` es `NOT NULL` y su clave foranea no
lleva `ON DELETE CASCADE` ni `SET NULL`, asi que PostgreSQL **impide** borrar un
profesor con anotaciones. La fila siempre existe. Dar de baja a un profesor en
esta aplicacion es cambiarle el `estado`, no borrarlo, y eso no afecta a nada de
aqui.

La materia es una **etiqueta copiada** en la propia fila, no una union con
`materias`: si manana quitan esa materia del horario, la anotacion conserva el
texto. Tambien ahorra la union.
"""

_SELECT = """
    SELECT a.id,
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
    FROM observador_anotaciones a
    JOIN profesor p ON p.id = a.profesor_id
    WHERE a.estudiante_id = %s
"""

_ORDEN = " ORDER BY a.creada_en DESC, a.id DESC"


def leer_anotaciones(cursor, estudiante_id, periodo=None):
    """Todas las anotaciones de un estudiante, la mas nueva primero.

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
        cursor.execute(_SELECT + _ORDEN, (estudiante_id,))
    else:
        cursor.execute(
            _SELECT + " AND a.periodo = %s" + _ORDEN,
            (estudiante_id, periodo),
        )
    return cursor.fetchall()
