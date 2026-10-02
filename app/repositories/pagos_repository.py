"""Escrituras de `pagos` y `pagos_aplicaciones`, extraidas en la subcapa 5.1.

Cada funcion recibe el cursor que ya abrio el controlador y ejecuta una sola
sentencia. Ninguna abre, cierra, confirma ni revierte recursos: la propiedad de
la conexion, el cursor, el `commit`, el `rollback`, el advisory lock, las
validaciones y la traduccion de errores sigue siendo del controlador.

Las cadenas SQL se conservan con su texto original, incluida la sangria, para
que lo que recibe PostgreSQL no cambie. La unica excepcion autorizada esta
anotada en `insertar_pago`.

Cambio de comportamiento autorizado aparte, que no es una refactorizacion: la
fase 1 del año lectivo (docs/funcionalidades/ANIO_LECTIVO.md) agrega a los dos
INSERT de `pagos` la columna `anio_lectivo_id` con el año activo. Los
parametros no cambian. En la fase 2 los dos aceptan un año pedido, para
registrar un pago en el año de la deuda que salda; sin el, la sentencia y los
parametros son los de la fase 1.
"""

from app.repositories.anios_lectivos_repository import ANIO_ACTIVO_ID_SQL


def _valor_anio(anio_lectivo_id):
    """El año del pago para el INSERT: la subconsulta del año activo, o un
    parametro con el año pedido."""
    if anio_lectivo_id is None:
        return ANIO_ACTIVO_ID_SQL, ()
    return "%s", (int(anio_lectivo_id),)


def insertar_pago(
    cursor, estudiante_id, venta_id, monto, descripcion, fecha, tipo_pago, anio_lectivo_id=None,
):
    """Inserta un pago y devuelve su id.

    Sirve a las dos ramas de `registrar_pago_controller`, la de metodos y la
    simple. Antes eran dos literales identicos salvo cuatro espacios de sangria;
    5.1 los unifico con autorizacion explicita del usuario. El flujo de tokens
    que recibe PostgreSQL es el mismo.
    """
    valor_anio, params_anio = _valor_anio(anio_lectivo_id)
    cursor.execute(f"""
                INSERT INTO pagos (estudiante_id, venta_id, monto, descripcion, fecha, tipo_pago, anio_lectivo_id)
                VALUES (%s, %s, %s, %s, %s, %s, {valor_anio})
                RETURNING id
            """, (estudiante_id, venta_id, monto, descripcion, fecha, tipo_pago, *params_anio))
    return cursor.fetchone()[0]


def insertar_pago_adelantado(
    cursor, estudiante_id, monto, descripcion, fecha, tipo_pago, anio_lectivo_id=None,
):
    """Inserta el pago unico de un adelanto y devuelve su id.

    No admite `venta_id`: un adelanto no puede ser un cargo de inventario.
    """
    valor_anio, params_anio = _valor_anio(anio_lectivo_id)
    cursor.execute(
        f"""
            INSERT INTO pagos (estudiante_id, monto, descripcion, fecha, tipo_pago, anio_lectivo_id)
            VALUES (%s, %s, %s, %s, %s, {valor_anio})
            RETURNING id
            """,
        (estudiante_id, monto, descripcion, fecha, tipo_pago, *params_anio),
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


# ---------------------------------------------------------------------------
# Lecturas de `pagos`
# ---------------------------------------------------------------------------

def leer_pago_para_anular(cursor, pago_id):
    """Bloquea el pago con `FOR UPDATE` y devuelve la fila cruda.

    Quien decide si existe, si ya estaba anulado y que hacer con su venta es el
    controlador. Aqui solo se toma el bloqueo y se leen las cinco columnas.
    """
    cursor.execute("""
            SELECT id, COALESCE(estado, 'Pagado'), monto, venta_id, descripcion
            FROM pagos
            WHERE id = %s
            FOR UPDATE
        """, (pago_id,))
    return cursor.fetchone()


def listar_pagos_de_estudiante(cursor, estudiante_id):
    """Historial completo, mas reciente primero."""
    cursor.execute("""
            SELECT
                id,
                estudiante_id,
                monto,
                fecha,
                descripcion,
                tipo_pago,
                COALESCE(estado, 'Pagado') AS estado,
                motivo_anulacion,
                fecha_anulacion,
                anulado_por
            FROM pagos
            WHERE estudiante_id = %s
            ORDER BY id DESC
        """, (estudiante_id,))
    return cursor.fetchall()


def contar_pagos_de_estudiante(cursor, estudiante_id):
    """Total de pagos del estudiante, sin filtrar por estado."""
    cursor.execute("""
            SELECT COUNT(*)
            FROM pagos
            WHERE estudiante_id = %s
        """, (estudiante_id,))
    return cursor.fetchone()[0]


def leer_aplicaciones_vigentes(cursor, estudiante_id, tipo_pago_id):
    """Suma por periodo lo ya aplicado de un concepto a un estudiante.

    Solo cuenta aplicaciones activas de pagos no anulados: es la lectura que
    decide cuanto saldo queda libre en cada mes.
    """
    cursor.execute(
        """
        SELECT pa.periodo, COALESCE(SUM(pa.monto), 0)
        FROM pagos_aplicaciones pa
        JOIN pagos p ON p.id = pa.pago_id
        WHERE pa.estudiante_id = %s
          AND pa.tipo_pago_id = %s
          AND pa.activo = TRUE
          AND COALESCE(p.estado, 'Pagado') <> 'Anulado'
        GROUP BY pa.periodo
        """,
        (estudiante_id, tipo_pago_id),
    )
    return cursor.fetchall()


def listar_pagos_de_estudiante_paginado(cursor, estudiante_id, limit, offset):
    """Una pagina del historial, con el mismo orden que la version completa."""
    cursor.execute("""
            SELECT
                id,
                estudiante_id,
                monto,
                fecha,
                descripcion,
                tipo_pago,
                COALESCE(estado, 'Pagado') AS estado,
                motivo_anulacion,
                fecha_anulacion,
                anulado_por
            FROM pagos
            WHERE estudiante_id = %s
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """, (estudiante_id, limit, offset))
    return cursor.fetchall()


# ---------------------------------------------------------------------------
# Efecto de un pago sobre una venta
#
# `ventas` pertenece al dominio de inventario y `venta_controller.py` conserva
# su propio SQL. Estas cinco sentencias no son persistencia general de ventas:
# son el efecto que un pago tiene sobre un cargo de inventario, y por eso viven
# aqui. Si alguna vez existe un `ventas_repository` con dos consumidores reales,
# este es el bloque que se mueve.
# ---------------------------------------------------------------------------

def leer_saldo_de_venta(cursor, venta_id):
    """Total, pagado y estado del cargo, para validar antes de cobrar."""
    cursor.execute("""
        SELECT total, COALESCE(pagado, 0), estado
        FROM ventas
        WHERE id = %s
    """, (venta_id,))
    return cursor.fetchone()


def leer_venta_para_anular(cursor, venta_id):
    """Bloquea la venta con `FOR UPDATE` antes de devolverle el saldo."""
    cursor.execute("""
                SELECT id, total, COALESCE(pagado, 0)
                FROM ventas
                WHERE id = %s
                FOR UPDATE
            """, (venta_id,))
    return cursor.fetchone()


def abonar_a_venta(cursor, monto, venta_id):
    """Acumula el abono y devuelve `(total, pagado)` ya actualizados.

    Sirve a las dos ramas de `registrar_pago_controller`. Eran dos literales
    identicos salvo la sangria; se unificaron siguiendo la decision tomada en
    5.1 para `insertar_pago`. El espacio final tras el parametro se conserva
    mediante un escape explicito, para no alterar el valor en tiempo de
    ejecucion y que `git diff --check` siga limpio.
    """
    cursor.execute("""
                    UPDATE ventas SET pagado = COALESCE(pagado, 0) + %s\x20
                    WHERE id = %s RETURNING total, pagado
                """, (monto, venta_id))
    return cursor.fetchone()


def marcar_venta_pagada(cursor, venta_id):
    """Cierra el cargo cuando lo abonado alcanza el total."""
    cursor.execute("UPDATE ventas SET estado = 'Pagado' WHERE id = %s", (venta_id,))


def ajustar_venta_tras_anulacion(cursor, nuevo_pagado, nuevo_estado, venta_id):
    """Devuelve el saldo y recalcula el estado del cargo al anular un pago."""
    cursor.execute("""
                UPDATE ventas
                SET pagado = %s,
                    estado = %s
                WHERE id = %s
            """, (nuevo_pagado, nuevo_estado, venta_id))
