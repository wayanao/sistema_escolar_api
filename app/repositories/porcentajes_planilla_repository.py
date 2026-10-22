"""Consultas de `planilla_tipos_porcentaje`.

Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md` (parte B, PB1). Como los demas
repositorios, cada funcion recibe el cursor que ya abrio quien llama, ejecuta
**una sola sentencia** y no abre, cierra, confirma ni revierte nada: el
`commit` es del controlador. Ninguna funcion valida; eso lo hace el
controlador.

Los tipos de nota se comparan siempre con `LOWER(TRIM(...))`, la misma
expresion de la planilla, de las subnotas y del indice unico de la migracion
`20261022_planilla_tipos_porcentaje.sql`.
"""


def leer_porcentajes_de_planilla(cursor, asignacion_id, periodo):
    """`(tipo_nota, porcentaje)` de cada tipo con porcentaje de esa clase y periodo."""
    cursor.execute("""
            SELECT tipo_nota, porcentaje
            FROM planilla_tipos_porcentaje
            WHERE asignacion_id = %s AND periodo = %s
            ORDER BY id
        """, (asignacion_id, periodo))
    return cursor.fetchall()


def leer_tipos_de_planilla(cursor, asignacion_id, periodo):
    """Los tipos de nota de la planilla: las `descripcion` de sus celdas.

    Incluye las columnas internas; quien llama las descarta con
    `admite_porcentaje`.
    """
    cursor.execute("""
            SELECT DISTINCT descripcion FROM notas_detalle
            WHERE asignacion_id = %s AND periodo = %s
              AND descripcion IS NOT NULL
            ORDER BY descripcion
        """, (asignacion_id, periodo))
    return [fila[0] for fila in cursor.fetchall()]


def bloquear_clase(cursor, asignacion_id):
    """Bloquea la fila de la asignacion hasta el fin de la transaccion.

    Asi dos guardados de porcentajes de la misma clase van uno detras del
    otro, y el segundo ve la suma que dejo el primero (PB3). `FOR NO KEY
    UPDATE` no choca con las claves foraneas: guardar notas de esa clase
    mientras tanto no espera.
    """
    cursor.execute("""
            SELECT id FROM asignaciones WHERE id = %s FOR NO KEY UPDATE
        """, (asignacion_id,))
    return cursor.fetchone()


def guardar_porcentaje(cursor, asignacion_id, periodo, tipo_nota, porcentaje):
    """Crea o cambia el porcentaje de un tipo, en una sentencia."""
    cursor.execute("""
            INSERT INTO planilla_tipos_porcentaje (asignacion_id, periodo, tipo_nota, porcentaje)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (asignacion_id, periodo, (LOWER(TRIM(tipo_nota))))
            DO UPDATE SET porcentaje = EXCLUDED.porcentaje,
                          tipo_nota = EXCLUDED.tipo_nota,
                          actualizado_en = CURRENT_TIMESTAMP
        """, (asignacion_id, periodo, tipo_nota, porcentaje))


def quitar_porcentaje(cursor, asignacion_id, periodo, tipo_nota):
    """Quita el porcentaje de un tipo. Tambien lo usa borrar el tipo (PB10)."""
    cursor.execute("""
            DELETE FROM planilla_tipos_porcentaje
            WHERE asignacion_id = %s AND periodo = %s
              AND LOWER(TRIM(tipo_nota)) = LOWER(TRIM(%s))
        """, (asignacion_id, periodo, tipo_nota))
