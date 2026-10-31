"""Consultas de `plan_de_clases_cuadros`.

Ver `docs/funcionalidades/NOMBRES_CUADROS_PLAN.md`. Como los demas
repositorios, cada funcion recibe el cursor que ya abrio quien llama, ejecuta
**una sola sentencia** y no abre, cierra, confirma ni revierte nada: el
`commit` es del controlador. Ninguna funcion valida; eso lo hace el
controlador con `app/core/cuadros_plan_de_clases.py`.
"""


def _tupla(fila, *columnas):
    if isinstance(fila, dict):
        return tuple(fila[columna] for columna in columnas)
    return tuple(fila)


def leer_cuadros(cursor):
    """`(clave, nombre, ayuda)` de cada cuadro renombrado, sin orden fijo."""
    cursor.execute("SELECT clave, nombre, ayuda FROM plan_de_clases_cuadros")
    return [_tupla(fila, "clave", "nombre", "ayuda") for fila in cursor.fetchall()]


def bloquear_cuadros(cursor):
    """Pone en fila a quienes guardan nombres, sin frenar a quienes los leen.

    Guardar es borrar e insertar. Sin este bloqueo, dos guardados a la vez
    podrian mezclar sus listas o chocar con la llave primaria. `SHARE ROW
    EXCLUSIVE` choca consigo mismo pero no con un `SELECT`, y se suelta al
    terminar la transaccion: gana el ultimo que guarda.
    """
    cursor.execute("LOCK TABLE plan_de_clases_cuadros IN SHARE ROW EXCLUSIVE MODE")


def borrar_cuadros(cursor):
    """Borra todos los nombres del colegio: todos vuelven a su original."""
    cursor.execute("DELETE FROM plan_de_clases_cuadros")


def insertar_cuadros(cursor, cuadros, usuario_id):
    """Inserta los cuadros `(clave, nombre, ayuda)` en **un solo `INSERT`**.

    `actualizado_por` es el admin que guarda; la hora la pone la base.
    """
    # Solo se repiten marcadores `%s`, nunca datos: el SQL no lleva nada que
    # venga de fuera.
    filas = ", ".join(["(%s, %s, %s, %s)"] * len(cuadros))
    parametros = []
    for clave, nombre, ayuda in cuadros:
        parametros.extend([clave, nombre, ayuda, usuario_id])
    cursor.execute(
        "INSERT INTO plan_de_clases_cuadros (clave, nombre, ayuda, actualizado_por) "
        f"VALUES {filas}",
        parametros,
    )
