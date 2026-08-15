"""Escrituras de `pagos` y `pagos_aplicaciones`, extraidas en la subcapa 5.1.

Cada funcion recibe el cursor que ya abrio el controlador y ejecuta una sola
sentencia. Ninguna abre, cierra, confirma ni revierte recursos: la propiedad de
la conexion, el cursor, el `commit`, el `rollback`, el advisory lock, las
validaciones y la traduccion de errores sigue siendo del controlador.

Las cadenas SQL se conservan con su texto original, incluida la sangria, para
que lo que recibe PostgreSQL no cambie. La unica excepcion autorizada esta
anotada en `insertar_pago`.
"""


def insertar_pago(cursor, estudiante_id, venta_id, monto, descripcion, fecha, tipo_pago):
    """Inserta un pago y devuelve su id.

    Sirve a las dos ramas de `registrar_pago_controller`, la de metodos y la
    simple. Antes eran dos literales identicos salvo cuatro espacios de sangria;
    5.1 los unifico con autorizacion explicita del usuario. El flujo de tokens
    que recibe PostgreSQL es el mismo.
    """
    cursor.execute("""
                INSERT INTO pagos (estudiante_id, venta_id, monto, descripcion, fecha, tipo_pago)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (estudiante_id, venta_id, monto, descripcion, fecha, tipo_pago))
    return cursor.fetchone()[0]


def insertar_pago_adelantado(cursor, estudiante_id, monto, descripcion, fecha, tipo_pago):
    """Inserta el pago unico de un adelanto y devuelve su id.

    No admite `venta_id`: un adelanto no puede ser un cargo de inventario.
    """
    cursor.execute(
        """
            INSERT INTO pagos (estudiante_id, monto, descripcion, fecha, tipo_pago)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
        (estudiante_id, monto, descripcion, fecha, tipo_pago),
    )
    return cursor.fetchone()[0]


def insertar_aplicacion(cursor, pago_id, estudiante_id, tipo_pago_id, periodo, monto):
    """Registra la aplicacion de un pago a un periodo concreto.

    La colision con el indice parcial unico sube como `IntegrityError`; quien
    la traduce a un mensaje de negocio es el controlador.
    """
    cursor.execute(
        """
                INSERT INTO pagos_aplicaciones
                    (pago_id, estudiante_id, tipo_pago_id, periodo, monto)
                VALUES (%s, %s, %s, %s, %s)
                """,
        (
            pago_id,
            estudiante_id,
            tipo_pago_id,
            periodo,
            monto,
        ),
    )


def asignar_venta_a_pago(cursor, venta_id, pago_id):
    """Rellena `venta_id` en un pago heredado que solo lo tenia en el texto."""
    cursor.execute(
        "UPDATE pagos SET venta_id = %s WHERE id = %s",
        (venta_id, pago_id),
    )


def desactivar_aplicaciones_de_pago(cursor, pago_id):
    """Desactiva las aplicaciones activas de un pago que se esta anulando."""
    cursor.execute(
        """
                UPDATE pagos_aplicaciones
                SET activo = FALSE
                WHERE pago_id = %s AND activo = TRUE
                """,
        (pago_id,),
    )


def marcar_pago_anulado(cursor, motivo, fecha_anulacion, admin_id, pago_id):
    """Marca el pago como anulado con su motivo, fecha y responsable.

    Conserva el `RETURNING id` original aunque el controlador no lo consuma.
    """
    cursor.execute("""
            UPDATE pagos
            SET estado = 'Anulado',
                motivo_anulacion = %s,
                fecha_anulacion = %s,
                anulado_por = %s
            WHERE id = %s
            RETURNING id
        """, (
        motivo,
        fecha_anulacion,
        admin_id,
        pago_id,
    ))
