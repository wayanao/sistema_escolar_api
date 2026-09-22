"""Consultas de `listas_seguimiento_columnas` y `listas_seguimiento_marcas`.

Ver `docs/funcionalidades/LISTAS_SEGUIMIENTO.md`. Como los demas repositorios,
recibe el cursor que ya abrio quien llama y no abre, cierra, confirma ni
revierte nada: el `commit` es del controlador.

Lo que hay que vigilar aqui es **cuantas** consultas se hacen, no lo complicada
que sea cada una: contra Neon (`us-east-1`) cada ida y vuelta cuesta ~180 ms se
consulte lo que se consulte. Es la leccion que dejo escrita
`observador_repository.py` despues de que la pantalla vieja del observador
tardara 16-20 s haciendo una peticion por alumno.

Por eso, de este modulo:

- `guardar_marcas` escribe **el lote entero en una sola sentencia**, con
  `UNNEST`, y no una por celda. Marcar una columna de 30 alumnos serian 30 idas
  y vueltas -5,4 s- con el patron por fila que todavia tiene
  `asistencia_repository`. Con `UNNEST` es una, cueste lo que cueste el lote.
- `leer_marcas_de_columnas` y `guardar_marcas` **no consultan nada** si reciben
  una lista vacia: devuelven el vacio sin gastar el viaje.

Ninguna funcion valida: el curso, el lote y el nombre los valida el
controlador. Lo unico que este modulo garantiza es que la comprobacion de
nombre duplicado use **exactamente** la misma expresion que el indice unico de
la migracion, porque si las dos se separan el 409 deja de coincidir con lo que
la base acepta. `tests/test_listas_seguimiento_repositorio.py` lo comprueba
leyendo el propio archivo .sql.
"""


def existe_curso(cursor, curso_id):
    """`True` si el curso existe.

    El controlador la necesita para el 404. Sin ella, un curso inventado y un
    curso real recien creado se ven igual: los dos devuelven cero columnas y
    cero alumnos.

    No filtra por `estado`: un curso inactivo sigue existiendo, y ocultarlo
    aqui seria una regla de producto que el documento no pide.
    """
    cursor.execute("SELECT 1 FROM cursos WHERE id = %s", (curso_id,))
    return cursor.fetchone() is not None


def leer_columnas_del_curso(cursor, curso_id):
    """Las columnas de un curso, en el orden en que se crearon.

    Devuelve filas `(id, nombre)`.

    Ordena por `id` y no por `created_at` a proposito: dos columnas creadas en
    la misma transaccion comparten el `CURRENT_TIMESTAMP` al milisegundo,
    porque es el instante de la transaccion y no el de la fila, y su orden
    entre si quedaria a criterio de PostgreSQL. El `id` es SERIAL, asi que el
    orden de creacion es exacto.

    El usuario confirmo el 2026-09-22 que el orden de creacion le sirve y que
    no hace falta poder reordenarlas; por eso la tabla no lleva columna de
    orden.
    """
    cursor.execute(
        """
        SELECT id, nombre
        FROM listas_seguimiento_columnas
        WHERE curso_id = %s
        ORDER BY id
        """,
        (curso_id,),
    )
    return cursor.fetchall()


def leer_estudiantes_del_curso(cursor, curso_id):
    """Los alumnos del curso, por apellido y nombre. Filas `(id, nombre, apellido)`.

    Es la misma consulta que ya usa, para otro fin,
    `estado_cuenta_curso_controller`, replicada aqui sin la parte de deudas
    porque alla vive dentro de un controlador de cartera y no en un
    repositorio.

    No filtra por `estado`, igual que el original: la lista de seguimiento
    muestra el curso completo. Cambiar eso seria una decision de producto que
    el documento no toma.
    """
    cursor.execute(
        """
        SELECT id, nombre, apellido
        FROM estudiantes
        WHERE curso_id = %s
        ORDER BY apellido, nombre
        """,
        (curso_id,),
    )
    return cursor.fetchall()


def leer_marcas_de_columnas(cursor, columna_ids):
    """Las marcas de esas columnas. Filas `(columna_id, estudiante_id, marcado, nota)`.

    Con la lista vacia **no consulta**: un curso sin columnas no tiene marcas
    posibles, y la ida y vuelta no cambiaria la respuesta.

    Una celda sin fila simplemente no aparece. El default
    (`marcado: false`, `nota: ""`) lo pone quien llama, igual que ya hace la
    planilla con las notas ausentes.
    """
    if not columna_ids:
        return []

    cursor.execute(
        """
        SELECT columna_id, estudiante_id, marcado, nota
        FROM listas_seguimiento_marcas
        WHERE columna_id = ANY(%s)
        """,
        (list(columna_ids),),
    )
    return cursor.fetchall()


def existe_columna_con_ese_nombre(cursor, curso_id, nombre):
    """`True` si el curso ya tiene una columna con ese nombre.

    **La misma expresion se aplica a los dos lados**, al nombre guardado y al
    que llega, y es la del indice `idx_listas_seguimiento_columnas_nombre_unico`
    de `migrations/20260921_listas_seguimiento.sql`: mayusculas fuera, espacios
    de los extremos fuera, y los espacios interiores repetidos colapsados a
    uno. Asi "  asistio  a la CUMBRE " y "Asistio a la cumbre" son el mismo
    nombre.

    Normalizar en SQL y no en Python es deliberado: hay una sola definicion de
    "mismo nombre", la de PostgreSQL, y no dos que puedan separarse.

    Esto sirve para devolver un 409 legible en el caso normal. **La garantia
    real es el indice unico**, que es lo unico que cierra la carrera entre dos
    peticiones casi simultaneas: entre este SELECT y el INSERT hay una ventana
    por la que otra peticion puede colarse, y ahi quien falla es el indice.
    Quien llame tiene que tratar tambien el error de unicidad, no solo este
    `True`.
    """
    cursor.execute(
        """
        SELECT 1
        FROM listas_seguimiento_columnas
        WHERE curso_id = %s
          AND UPPER(REGEXP_REPLACE(TRIM(nombre), '[[:space:]]+', ' ', 'g'))
            = UPPER(REGEXP_REPLACE(TRIM(%s), '[[:space:]]+', ' ', 'g'))
        """,
        (curso_id, nombre),
    )
    return cursor.fetchone() is not None


def crear_columna(cursor, curso_id, nombre):
    """Inserta una columna y devuelve su id.

    Guarda el `nombre` **tal como llega**. Quien lo recorta es
    `ColumnaSeguimientoCreate`, en la frontera HTTP, asi que aqui ya llega
    limpio. Este modulo no decide que es un nombre valido.

    El `commit` es de quien llama, como en los demas repositorios.
    """
    cursor.execute(
        """
        INSERT INTO listas_seguimiento_columnas (curso_id, nombre)
        VALUES (%s, %s)
        RETURNING id
        """,
        (curso_id, nombre),
    )
    return cursor.fetchone()[0]


def eliminar_columna(cursor, curso_id, columna_id):
    """Borra la columna **solo si es de ese curso**. `True` si borro algo.

    El `curso_id` va en el `WHERE` y no en un `if` previo: la comprobacion de
    pertenencia y el borrado son la misma sentencia, asi que no hay ventana
    entre comprobar y escribir. Es el mismo criterio que
    `actualizar_anotacion_del_autor` en `observador_repository`.

    Sus marcas se van con ella por el `ON DELETE CASCADE` de la migracion, sin
    una segunda sentencia. El borrado es definitivo: no hay baja logica aqui,
    porque no hay historial financiero que proteger.
    """
    cursor.execute(
        """
        DELETE FROM listas_seguimiento_columnas
        WHERE id = %s AND curso_id = %s
        RETURNING id
        """,
        (columna_id, curso_id),
    )
    return cursor.fetchone() is not None


# Una sola sentencia para el lote entero. Los cuatro arrays van en paralelo: la
# celda i es (columnas[i], estudiantes[i], marcados[i], notas[i]).
#
# `ON CONFLICT (columna_id, estudiante_id)` se apoya en el UNIQUE de la
# migracion, igual que el upsert de `tipos_pagos_estudiantes`. Una celda nueva
# se inserta y una que ya existia se pisa, sin que quien llama tenga que saber
# cual era cual.
#
# **Si el lote trae la misma celda dos veces, PostgreSQL aborta** la sentencia
# entera con "ON CONFLICT DO UPDATE command cannot affect row a second time".
# Por eso el 422 por celdas repetidas que pide el documento no es cosmetico: es
# lo que evita ese error. La validacion vive en el controlador; esta nota esta
# aqui para que nadie la quite pensando que sobra.
_UPSERT_MARCAS = """
    INSERT INTO listas_seguimiento_marcas (columna_id, estudiante_id, marcado, nota)
    SELECT * FROM UNNEST(%s::int[], %s::int[], %s::boolean[], %s::text[])
    ON CONFLICT (columna_id, estudiante_id)
    DO UPDATE SET marcado = EXCLUDED.marcado,
                  nota = EXCLUDED.nota,
                  updated_at = CURRENT_TIMESTAMP
"""


def guardar_marcas(cursor, marcas):
    """Guarda el lote entero en una sola ida y vuelta. Devuelve cuantas filas toco.

    `marcas` es una lista de tuplas `(columna_id, estudiante_id, marcado,
    nota)`: datos simples, como pide `app/repositories/README.md`. Convertir
    los objetos del esquema a tuplas es cosa del controlador.

    Con el lote vacio no consulta y devuelve 0. El documento pide que un lote
    vacio sea un 422, pero esa es la respuesta HTTP y la decide el controlador;
    aqui, sin nada que escribir, no hay nada que preguntarle a la base.

    Los valores se pasan tal cual: este modulo no convierte una nota vacia en
    `NULL` ni al reves, ni recorta nada. Si una nota pasa de 240 caracteres, la
    rechaza el CHECK de la tabla.

    El `commit` es de quien llama.
    """
    if not marcas:
        return 0

    columnas = [marca[0] for marca in marcas]
    estudiantes = [marca[1] for marca in marcas]
    marcados = [marca[2] for marca in marcas]
    notas = [marca[3] for marca in marcas]

    cursor.execute(_UPSERT_MARCAS, (columnas, estudiantes, marcados, notas))
    return cursor.rowcount
