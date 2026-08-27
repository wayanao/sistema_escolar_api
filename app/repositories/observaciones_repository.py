"""Consultas y escritura de `observaciones`, extraidas en la subcapa 7.1.

Cada funcion recibe el cursor que ya abrio quien la llama y ejecuta una sola
sentencia. Ninguna abre, cierra, confirma ni revierte recursos: la propiedad de
la conexion, el `commit`, el `rollback`, la resolucion de la asignacion
academica y el formateo del payload siguen fuera de aqui, igual que en los diez
repositorios anteriores. Este es el **undecimo**.

**Sus dos llamadores son de capas distintas, y eso es deliberado.**
`leer_observacion` la llama `app/routes/observaciones.py` desde su
`with get_cursor()`, y `guardar_observacion` la llama
`app/controllers/observacion_controller.py` desde su `get_connection()`. La 7.0
registro que el dominio conserva **dos idiomas de conexion** repartidos entre la
capa HTTP y la de control; 7.1 **saca el SQL de las dos**, pero **no unifica los
idiomas ni mueve la propiedad del cursor**: hacerlo cambiaria los conteos de
conexiones que 7.0 dejo fijados por asercion, y no esta autorizado.

Este dominio **escribe una sola tabla** con un `UPSERT` que se apoya en
`UNIQUE (estudiante_id, asignacion_id, periodo)`, la unica restriccion que la
tabla tiene. **No tiene ninguna clave foranea**: es el hallazgo 1 de 7.0 y este
modulo **no lo corrige** ni lo compensa validando nada.

Lo que **no** vive aqui, y es deliberado:

- **La normalizacion de las tres dimensiones y el `422`.** Viven en
  `app/schemas/observacion.py`, en un `field_validator` y un `model_validator`.
  Traerlos aqui convertiria el **422 en un 500**: es el hallazgo 4 de 7.0 y hay
  una prueba que lo fija.
- **La resolucion de la asignacion academica.** La hacen los dos llamadores
  sobre su propio cursor, antes de llamar aqui, y sigue costando 1 consulta en
  cada camino.
- **El `None` de la observacion ausente.** `leer_observacion` devuelve la fila
  cruda o `None`; convertir eso en el diccionario de tres dimensiones, o en
  `None`, es contrato HTTP y se queda en la ruta.
"""


def leer_observacion(cursor, estudiante_id, asignacion_id, periodo):
    """Las tres dimensiones de una observacion, o `None` si no existe.

    Devuelve la fila cruda: quien llama decide que hacer con ella. La ruta la
    convierte en un diccionario, y devuelve `None` tal cual cuando no hay fila,
    que es un contrato con el frontend fijado desde la subcapa 1.4.
    """
    cursor.execute("""
            SELECT conductual, cognitivo, lenguaje
            FROM observaciones
            WHERE estudiante_id = %s AND asignacion_id = %s AND periodo = %s
        """, (estudiante_id, asignacion_id, periodo))
    return cursor.fetchone()


def asignacion_esta_activa(cursor, asignacion_id):
    """`True` si la asignacion sigue activa.

    Desactivar una asignacion es el equivalente a borrarla: el proyecto **nunca
    borra** esa fila porque seis claves foraneas cuelgan de ella, asi que
    `activo = FALSE` es la baja real. Escribir una observacion nueva contra una
    asignacion dada de baja es el hallazgo 6 de 7.0.

    **Solo se usa al escribir.** La lectura no la llama a proposito: consultar
    una observacion antigua de una asignacion ya dada de baja es legitimo, y
    bloquearlo escondería historial.
    """
    cursor.execute(
        "SELECT activo FROM asignaciones WHERE id = %s",
        (asignacion_id,),
    )
    fila = cursor.fetchone()
    return bool(fila and fila[0])


def guardar_observacion(cursor, estudiante_id, asignacion_id, periodo,
                        conductual, cognitivo, lenguaje):
    """Crea o actualiza la observacion del trio estudiante/asignacion/periodo.

    Se apoya en `UNIQUE (estudiante_id, asignacion_id, periodo)`. **No comprueba
    que la asignacion siga activa**: es el hallazgo 6 de 7.0 y se conserva. El
    `commit` es del controlador.
    """
    cursor.execute("""
            INSERT INTO observaciones (
                estudiante_id,
                asignacion_id,
                periodo,
                conductual,
                cognitivo,
                lenguaje
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (estudiante_id, asignacion_id, periodo)
            DO UPDATE SET
                conductual = EXCLUDED.conductual,
                cognitivo = EXCLUDED.cognitivo,
                lenguaje = EXCLUDED.lenguaje
        """, (
        estudiante_id,
        asignacion_id,
        periodo,
        conductual,
        cognitivo,
        lenguaje,
    ))
