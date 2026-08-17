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
