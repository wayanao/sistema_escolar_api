"""Persistencia del dominio de ventas.

Octavo repositorio del proyecto. Extraido en la subcapa 7.1 de la capa 7 para
`ventas`, moviendo las 17 sentencias que vivian en `venta_controller.py` sin
cambiar su texto.

Todas las funciones **reciben el cursor existente** y ninguna abre, cierra,
confirma ni revierte nada: la propiedad de la conexion, del `commit` y del
`rollback` se queda en el controlador, conforme a la capa 1.

El SQL se conserva **byte a byte**, incluidas la sangria interior de cada
literal y los tres espacios finales que traia el original. Esos tres se
escriben con un escape explicito `\\x20` para no alterar el valor en tiempo de
ejecucion y que `git diff --check` siga limpio; es la misma solucion que 5.1
adopto en `pagos_repository.abonar_a_venta`.
"""


# ---------------------------------------------------------------------------
# Lecturas del listado
# ---------------------------------------------------------------------------


def leer_ventas_con_estudiante(cursor):
    """Listado completo, sin paginar y sin `LIMIT`, tal como esta hoy."""
    cursor.execute('''
            SELECT v.id, e.nombre, e.apellido, v.fecha, v.tipo_venta, v.total, v.estado, v.notas, v.estudiante_id,
                   v.motivo_anulacion, v.fecha_anulacion
            FROM ventas v
            LEFT JOIN estudiantes e ON v.estudiante_id = e.id
            ORDER BY v.fecha DESC, v.id DESC
        ''')
    return cursor.fetchall()


def leer_detalles_de_todas_las_ventas(cursor):
    """Detalles de todas las ventas, para agruparlos despues en memoria."""
    cursor.execute('''
            SELECT vd.venta_id, i.nombre, vd.cantidad, vd.precio_unitario, vd.subtotal
            FROM ventas_detalle vd
            JOIN inventario i ON vd.inventario_id = i.id
        ''')
    return cursor.fetchall()


def contar_ventas(cursor, where_sql, params):
    """Total de filas para la paginacion.

    El `where_sql` llega ya construido desde el controlador, que es quien valida
    los filtros y arma los parametros. Es el mismo reparto que 6.1 fijo para el
    filtro de estado de `estudiantes`.
    """
    cursor.execute(f'''
            SELECT COUNT(*)
            FROM ventas v
            LEFT JOIN estudiantes e ON v.estudiante_id = e.id
            {where_sql}
        ''', params)
    return cursor.fetchone()[0]


def leer_pagina_de_ventas(cursor, where_sql, params):
    """Una pagina del listado, con el mismo orden que la lectura completa."""
    cursor.execute(f'''
            SELECT v.id, e.nombre, e.apellido, v.fecha, v.tipo_venta, v.total, v.estado, v.notas, v.estudiante_id,
                   v.motivo_anulacion, v.fecha_anulacion
            FROM ventas v
            LEFT JOIN estudiantes e ON v.estudiante_id = e.id
            {where_sql}
            ORDER BY v.fecha DESC, v.id DESC
            LIMIT %s OFFSET %s
        ''', params)
    return cursor.fetchall()


def leer_detalles_de_ventas(cursor, venta_ids):
    """Detalles de las ventas de una pagina, filtrados con `= ANY(%s)`."""
    cursor.execute('''
            SELECT vd.venta_id, i.nombre, vd.cantidad, vd.precio_unitario, vd.subtotal
            FROM ventas_detalle vd
            JOIN inventario i ON vd.inventario_id = i.id
            WHERE vd.venta_id = ANY(%s)
        ''', (venta_ids,))
    return cursor.fetchall()


# ---------------------------------------------------------------------------
# Lecturas de los cargos pendientes de un estudiante
# ---------------------------------------------------------------------------


def leer_ventas_pendientes_de_estudiante(cursor, estudiante_id):
    """Cargos con estado `Pendiente`, de los que el controlador deriva el saldo."""
    cursor.execute('''
            SELECT v.id, v.fecha, v.total, v.estado, v.notas, COALESCE(v.pagado, 0)\x20
            FROM ventas v
            WHERE v.estudiante_id = %s AND v.estado = 'Pendiente'
            ORDER BY v.fecha ASC
        ''', (estudiante_id,))
    return cursor.fetchall()


def leer_detalles_de_ventas_en(cursor, venta_ids):
    """Igual que `leer_detalles_de_ventas` pero con `IN %s` y una tupla.

    Las dos formas se conservan como estaban: no son un duplicado exacto, y
    unificarlas cambiaria el texto de una de las dos sentencias.
    """
    cursor.execute('''
            SELECT vd.venta_id, i.nombre, vd.cantidad, vd.precio_unitario, vd.subtotal
            FROM ventas_detalle vd
            JOIN inventario i ON vd.inventario_id = i.id
            WHERE vd.venta_id IN %s
        ''', (venta_ids,))
    return cursor.fetchall()


# ---------------------------------------------------------------------------
# Alta de una venta
# ---------------------------------------------------------------------------


def leer_producto_para_vender(cursor, inventario_id):
    """Bloquea el producto con `FOR UPDATE` antes de comprobar su stock.

    Es el unico lock que toma el alta, y recae sobre `inventario`, no sobre
    `ventas`.
    """
    cursor.execute(
        """
        SELECT nombre, COALESCE(stock_actual, 0), COALESCE(LOWER(estado), 'activo')
        FROM inventario
        WHERE id = %s
        FOR UPDATE
        """,
        (inventario_id,),
    )
    return cursor.fetchone()


def insertar_venta(cursor, estudiante_id, tipo_venta, total, estado, notas):
    """Cabecera de la venta. Devuelve el `id` recien creado."""
    cursor.execute(
        """INSERT INTO ventas (estudiante_id, tipo_venta, total, estado, notas)\x20
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
        (estudiante_id, tipo_venta, total, estado, notas)
    )
    return cursor.fetchone()[0]


def insertar_detalle_de_venta(cursor, venta_id, inventario_id, cantidad, precio_unitario, subtotal):
    """Una linea de la venta."""
    cursor.execute(
        """INSERT INTO ventas_detalle (venta_id, inventario_id, cantidad, precio_unitario, subtotal)\x20
                   VALUES (%s, %s, %s, %s, %s)""",
        (venta_id, inventario_id, cantidad, precio_unitario, subtotal)
    )


def descontar_stock(cursor, cantidad, inventario_id):
    """Descuenta lo vendido, solo si el producto sigue activo."""
    cursor.execute(
        """
                UPDATE inventario
                SET stock_actual = stock_actual - %s
                WHERE id = %s
                  AND COALESCE(LOWER(estado), 'activo') = 'activo'
                """,
        (cantidad, inventario_id)
    )


# ---------------------------------------------------------------------------
# Borrado fisico
# ---------------------------------------------------------------------------


def borrar_venta(cursor, venta_id):
    """Unica sentencia `DELETE` del dominio.

    Su unico llamador, `venta_controller.eliminar_venta`, **no tiene
    consumidor**: la ruta `DELETE /api/ventas/{id}` responde 405. Es el hallazgo
    4 de 7.0 y se conserva sin retirar, siguiendo el precedente que la capa 6
    fijo con el codigo muerto de asignaciones.
    """
    cursor.execute("DELETE FROM ventas WHERE id = %s", (venta_id,))


# ---------------------------------------------------------------------------
# Anulacion de una venta
# ---------------------------------------------------------------------------


def leer_venta_y_estado_para_anular(cursor, venta_id):
    """Bloquea la venta con `FOR UPDATE` antes de anularla.

    No confundir con `pagos_repository.leer_venta_para_anular`, que lee la misma
    tabla para otra cosa: alli se anula **un pago** y se necesita el saldo; aqui
    se anula **la venta** y se necesita el estado.
    """
    cursor.execute("""
            SELECT id, estado
            FROM ventas
            WHERE id = %s
            FOR UPDATE
        """, (venta_id,))
    return cursor.fetchone()


def leer_detalles_para_reponer_stock(cursor, venta_id):
    """Lineas de la venta anulada, para devolver cada cantidad al inventario."""
    cursor.execute("""
            SELECT inventario_id, cantidad
            FROM ventas_detalle
            WHERE venta_id = %s
        """, (venta_id,))
    return cursor.fetchall()


def reponer_stock(cursor, cantidad, inventario_id):
    """Devuelve lo vendido. A diferencia del descuento, **no filtra por estado**."""
    cursor.execute("""
                UPDATE inventario
                SET stock_actual = COALESCE(stock_actual, 0) + %s
                WHERE id = %s
            """, (cantidad, inventario_id))


# ---------------------------------------------------------------------------
# El efecto de anular una venta sobre sus pagos
#
# `pagos` pertenece a un dominio ya migrado y `pagos_repository` es su duenyo
# desde la capa 5. Esta sentencia vive aqui, y no alli, por simetria exacta con
# la decision que aquella capa dejo escrita: alli hay un bloque rotulado «el
# efecto de un pago sobre una venta» que conserva cinco sentencias sobre la
# tabla `ventas`. Esta es la operacion inversa —el efecto de una venta sobre sus
# pagos— y responde al mismo criterio.
#
# Llevarla a `pagos_repository` ampliaria el diff a un modulo que la capa 5
# cerro y obligaria al controlador de ventas a importarlo, creando una
# dependencia entre dominios que 7.1 no esta autorizada a introducir. Es un
# punto de decision registrado en la bitacora, no una eleccion por vecindad.
#
# ATENCION: el `ILIKE` de esta sentencia **no delimita el numero de la venta**,
# asi que anular la venta 4 alcanza los pagos de la venta 40. Es el hallazgo 2
# de 7.0 y se conserva **sin corregir**: cambiarlo altera lo que hoy ocurre en
# produccion y no es trabajo de una extraccion.
# ---------------------------------------------------------------------------


def anular_pagos_de_la_venta(cursor, motivo_para_el_pago, fecha_anulacion, admin_id, venta_id, patron_descripcion):
    """Marca como anulados los pagos de un cargo, por `venta_id` o por texto."""
    cursor.execute("""
            UPDATE pagos
            SET estado = 'Anulado',
                motivo_anulacion = COALESCE(motivo_anulacion, %s),
                fecha_anulacion = COALESCE(fecha_anulacion, %s),
                anulado_por = COALESCE(anulado_por, %s),
                venta_id = COALESCE(venta_id, %s)
            WHERE COALESCE(estado, 'Pagado') <> 'Anulado'
              AND (
                    venta_id = %s
                    OR descripcion ILIKE %s
                  )
        """, (
        motivo_para_el_pago,
        fecha_anulacion,
        admin_id,
        venta_id,
        venta_id,
        patron_descripcion,
    ))


def marcar_venta_anulada(cursor, motivo, fecha_anulacion, admin_id, venta_id):
    """Cierra la anulacion dejando el saldo en cero y la auditoria puesta."""
    cursor.execute("""
            UPDATE ventas
            SET estado = 'Anulada',
                pagado = 0,
                motivo_anulacion = %s,
                fecha_anulacion = %s,
                anulado_por = %s
            WHERE id = %s
        """, (motivo, fecha_anulacion, admin_id, venta_id))
