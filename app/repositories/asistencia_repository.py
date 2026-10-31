"""Consultas y escritura de `asistencia`, extraidas en la subcapa 7.1.

Cada funcion recibe el cursor que ya abrio quien la llama y ejecuta una sola
sentencia. Ninguna abre, cierra, confirma ni revierte recursos: la propiedad de
la conexion, el `commit`, el `rollback`, la resolucion de la asignacion
academica y la agrupacion del historial siguen fuera de aqui, igual que en los
ocho repositorios anteriores.

Este dominio **escribe**, y lo hace con un reemplazo parcial transaccional:
`borrar_asistencia_del_lote` mas una llamada a `insertar_asistencia` por
estudiante, todo dentro de la unica transaccion propia del dominio. El `commit`
**no** es de este modulo.

El controlador conserva **dos idiomas de conexion**, herencia de que la subcapa
1.4g migrase 1 sitio de 2: la escritura abre con `get_connection()` y la lectura
con `get_cursor()`. **Se conservan los dos.** Unificarlos bajaria el coste pero
cambiaria los conteos de conexiones que 7.0 dejo fijados por asercion, y no esta
autorizado aqui.

Las cadenas SQL se conservan con su texto original, incluida la sangria y las
dos lineas en blanco interiores del `SELECT`, para que lo que recibe PostgreSQL
no cambie. Esas lineas quedan **vacias**, sin espacios: es la leccion que 1.4g
registro al reindentar ese mismo literal, porque `git diff --check` rechaza
lineas nuevas con espacios finales y la compuerta lo ejecuta.

Lo que **no** vive aqui, y es deliberado:

- las **tres validaciones de lote** —lote no vacio, contexto homogeneo y sin
  estudiantes duplicados— siguen en `app/routes/asistencia.py`. Son reglas de
  dominio en la capa HTTP, el hallazgo 3 de 7.0, y moverlas cambiaria el
  comportamiento de quien llame al controlador directamente;
- la comprobacion de permisos, incluido el **N+1 en conexiones** del hallazgo 1,
  vive en `app/core/permissions.py`, infraestructura compartida y fuera del
  alcance de esta capa;
- las **dos lecturas ajenas** de esta tabla siguen donde las dejaron las capas 6
  y 7: `contar_inasistencias_por_periodo` en `estudiantes_repository` (hasta
  el 2026-10-31, `contar_inasistencias`), dentro del bloque del
  expediente, y las inasistencias por profesor en `dashboard_repository`. **No
  se movieron.** Ambas filtran con `estado ILIKE 'ausente'`; este modulo no usa
  `ILIKE` en ninguna de sus tres sentencias, y esa asimetria es el hallazgo 6 de
  7.0. Se conserva tal cual: 7.0 la mapeo y tiene prohibido arreglarla.
"""


# ---------------------------------------------------------------------------
# El reemplazo parcial de un lote de asistencia.
#
# El `DELETE` acota por asignacion, fecha, periodo y la lista de estudiantes del
# lote, asi que no alcanza a companeros que no vengan en la peticion. Quien
# decide que fecha y que periodo se usan es el controlador, y toma los de
# `data[0]` mientras cada `INSERT` usa los del item: es el hallazgo 4 de 7.0 y
# **no se corrige aqui**.
# ---------------------------------------------------------------------------


def borrar_asistencia_del_lote(cursor, asignacion_id, fecha, periodo, estudiante_ids):
    """Borra las filas de esa asignacion, fecha y periodo para esos estudiantes."""
    cursor.execute("""
            DELETE FROM asistencia
            WHERE asignacion_id = %s AND fecha = %s AND periodo = %s
              AND estudiante_id = ANY(%s)
        """, (
        asignacion_id,
        fecha,
        periodo,
        estudiante_ids,
    ))


def insertar_asistencia(cursor, estudiante_id, asignacion_id, fecha, estado, periodo):
    """Inserta una fila de asistencia.

    `estado` se escribe tal como llega. El `Literal["presente", "ausente"]` del
    esquema solo protege el camino HTTP; es el hallazgo 5 de 7.0 y este modulo
    no lo valida, igual que no lo validaba el controlador.
    """
    cursor.execute("""
                INSERT INTO asistencia (estudiante_id, asignacion_id, fecha, estado, periodo)
                VALUES (%s, %s, %s, %s, %s)
            """, (
        estudiante_id,
        asignacion_id,
        fecha,
        estado,
        periodo
    ))


# ---------------------------------------------------------------------------
# La lectura del historial.
# ---------------------------------------------------------------------------


def leer_historial_de_asignacion(cursor, asignacion_id, periodo):
    """Filas de asistencia de una asignacion y periodo, una por estudiante y fecha.

    Devuelve las filas crudas. La agrupacion por estudiante, el descarte de la
    fecha nula y el formateo de la respuesta se quedan en el controlador: son
    calculo sobre memoria y 1.4g los dejo expresamente fuera del bloque que
    ocupa la conexion.
    """
    cursor.execute("""
            SELECT
                e.id,
                e.nombre,
                e.apellido,
                a.fecha,
                a.estado
            FROM estudiantes e

            JOIN asistencia a ON a.estudiante_id = e.id

            WHERE a.asignacion_id = %s AND a.periodo = %s
            ORDER BY e.apellido ASC, e.nombre ASC, a.fecha ASC
        """, (asignacion_id, periodo))

    return cursor.fetchall()
