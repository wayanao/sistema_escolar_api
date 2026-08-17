"""Persistencia de `estudiantes`, extraida en la subcapa 6.1.

Cada funcion recibe el cursor que ya abrio el controlador y ejecuta una sola
sentencia. Ninguna abre, cierra, confirma ni revierte recursos: la propiedad de
la conexion, el cursor, el `commit`, el `rollback`, la normalizacion de estado,
la construccion del filtro y el formateo de la respuesta siguen siendo del
controlador, igual que en `pagos_repository`.

Las cadenas SQL se conservan con su texto original, incluida la sangria, para
que lo que recibe PostgreSQL no cambie. Cinco lineas del INSERT y del UPDATE
terminan en un espacio en el codigo heredado; se conserva con `\\x20` explicito,
como hicieron 4.3 y 5.2, para no alterar el valor y mantener limpio
`git diff --check`.

Las consultas del filtro llegan ya construidas desde el controlador. El
fragmento `where_sql` no es entrada del cliente: sale de literales del propio
codigo y sus valores viajan siempre parametrizados.
"""


def insertar_estudiante(cursor, valores):
    """Inserta un estudiante con sus 35 columnas y devuelve su id.

    El orden de `valores` es contrato: un desplazamiento guardaria el telefono
    del padre en el campo de la madre sin lanzar ningun error.
    """
    cursor.execute("""
            INSERT INTO estudiantes
            (
            nombre,\x20
            apellido,
            documento_identidad,
            fecha_nacimiento,
            curso_id,\x20
            descuento_matricula,\x20
            descuento_mensualidad,
            datos_medicos,
            telefono,
            email,
            direccion,
            nombre_padre,
            telefono_padre,
            nombre_madre,
            telefono_madre,
            contacto_emergencia,
            tipo_documento,
            lugar_expedicion,
            eps,
            estrato,
            jornada,
            colegio_anterior,
            anio_cursado_anterior,
            pre_escolar_anterior,
            ebp_anterior,
            motivo_retiro_anterior,
            paz_salvo_anterior,
            ocupacion_padre,
            tipo_documento_padre,
            documento_padre,
            ocupacion_madre,
            tipo_documento_madre,
            documento_madre,
            condicion_diagnostico,
            estado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, valores)
    return cursor.fetchone()[0]


def actualizar_estudiante(cursor, valores):
    """Actualiza las 35 columnas de un estudiante y devuelve la fila afectada.

    `estado = COALESCE(%s, estado, 'activo')` es lo que hace que enviar `None`
    conserve el estado guardado en vez de sobrescribirlo.
    """
    cursor.execute("""
            UPDATE estudiantes
            SET nombre = %s,
            apellido = %s,
            documento_identidad = %s,
            fecha_nacimiento = %s,
            curso_id = %s,\x20
            descuento_matricula = %s,\x20
            descuento_mensualidad = %s,
            datos_medicos = %s,
            telefono = %s,
            email = %s,
            direccion = %s,
            nombre_padre = %s,
            telefono_padre = %s,
            nombre_madre = %s,
            telefono_madre = %s,
            contacto_emergencia = %s,
            tipo_documento = %s,
            lugar_expedicion = %s,
            eps = %s,
            estrato = %s,
            jornada = %s,
            colegio_anterior = %s,
            anio_cursado_anterior = %s,
            pre_escolar_anterior = %s,
            ebp_anterior = %s,
            motivo_retiro_anterior = %s,
            paz_salvo_anterior = %s,
            ocupacion_padre = %s,
            tipo_documento_padre = %s,
            documento_padre = %s,
            ocupacion_madre = %s,
            tipo_documento_madre = %s,
            documento_madre = %s,
            condicion_diagnostico = %s,
                estado = COALESCE(%s, estado, 'activo')
            WHERE id = %s
            RETURNING id
        """, valores)
    return cursor.fetchone()


def listar_estudiantes(cursor, where_sql, parametros):
    """Lista sin paginar, ordenada por apellido y nombre."""
    cursor.execute(f"""
            SELECT
                id,
                nombre,
                apellido,
                documento_identidad,
                fecha_nacimiento,
                curso_id,
                email,
                COALESCE(LOWER(estado), 'activo') AS estado
            FROM estudiantes
            {where_sql}
            ORDER BY apellido ASC, nombre ASC
        """, tuple(parametros))
    return cursor.fetchall()


def contar_estudiantes(cursor, where_sql, parametros):
    """Total que acompana a la respuesta paginada."""
    cursor.execute("SELECT COUNT(*) FROM estudiantes" + where_sql, tuple(parametros))
    return cursor.fetchone()[0]


def listar_estudiantes_paginado(cursor, where_sql, parametros):
    """Pagina de la lista. El `where_sql` es el mismo que uso el conteo."""
    cursor.execute(
        """
            SELECT
                id,
                nombre,
                apellido,
                documento_identidad,
                fecha_nacimiento,
                curso_id,
                email,
                COALESCE(LOWER(estado), 'activo') AS estado
            FROM estudiantes
            """
        + where_sql
        + """
            ORDER BY apellido ASC, nombre ASC
            LIMIT %s OFFSET %s
            """,
        tuple(parametros),
    )
    return cursor.fetchall()


def obtener_estudiante(cursor, est_id):
    """Devuelve la fila completa del estudiante, o `None`.

    Conserva el `SELECT *` heredado: el contrato de la entrada HTTP que la
    consume es el esquema entero de la tabla, y quien lee `cursor.description`
    para nombrar las columnas sigue siendo el controlador, dueno del cursor.
    """
    cursor.execute("SELECT * FROM estudiantes WHERE id = %s", (est_id,))
    return cursor.fetchone()


def actualizar_estado_estudiante(cursor, estado, est_id):
    """Cambia el estado y devuelve `(id, estado_normalizado)`, o `None`.

    Es la unica baja del dominio: retirar a un estudiante es un `UPDATE`, nunca
    un `DELETE`. Las nueve claves foraneas que apuntan a `estudiantes` dependen
    de que siga siendo asi.
    """
    cursor.execute(
        """
            UPDATE estudiantes
            SET estado = %s
            WHERE id = %s
            RETURNING id, COALESCE(LOWER(estado), 'activo')
            """,
        (estado, est_id),
    )
    return cursor.fetchone()


# ---------------------------------------------------------------------------
# El expediente de un estudiante
#
# Las cuatro lecturas que siguen NO son persistencia de notas, asistencia,
# observaciones ni ventas: son las cuatro preguntas que
# `obtener_detalles_estudiante_controller` hace sobre UN estudiante para armar su
# expediente. Viven aqui por la decision tomada en 6.2 con evidencia, la misma
# que 5.2 aplico al contacto de pagos con `ventas`: no existe un repositorio de
# esos dominios, y crear uno tendria un solo consumidor real porque migrar
# dashboard, notas, planilla, boletin y venta_controller esta fuera del alcance
# de esta capa. Ninguna de estas consultas es un duplicado: dashboard promedia
# con TRUNC a dos decimales y notas con COALESCE(AVG, 0), no con ROUND a uno.
#
# Si algun dia existe un repositorio de esos dominios con dos consumidores
# reales, este bloque es lo que se mueve.
# ---------------------------------------------------------------------------


def leer_promedios_por_materia(cursor, est_id):
    """Promedio de cada materia del estudiante, redondeado a un decimal en SQL.

    El promedio general NO sale de aqui: el controlador promedia estos
    promedios y redondea otra vez en Python.
    """
    cursor.execute('''
                SELECT m.nombre, ROUND(AVG(n.nota), 1) as promedio
                FROM notas_detalle n
                JOIN asignaciones a ON n.asignacion_id = a.id
                JOIN materias m ON a.materia_id = m.id
                WHERE n.estudiante_id = %s GROUP BY m.id
            ''', (est_id,))
    return cursor.fetchall()


def contar_inasistencias(cursor, est_id):
    """Numero de ausencias. El filtro es `ILIKE 'ausente'`, no una igualdad."""
    cursor.execute('''
                SELECT count(*) FROM asistencia
                WHERE estudiante_id = %s AND estado ILIKE 'ausente'
            ''', (est_id,))
    return cursor.fetchone()[0]


def leer_observaciones(cursor, est_id):
    """Observaciones del estudiante con su materia y profesor, mas recientes primero."""
    cursor.execute('''
                SELECT o.id, o.periodo, o.conductual, o.cognitivo, o.lenguaje, m.nombre AS materia_nombre, p.nombre || ' ' || p.apellido AS profesor_nombre FROM observaciones o JOIN asignaciones a ON o.asignacion_id = a.id JOIN materias m ON a.materia_id = m.id JOIN profesor p ON a.profesor_id = p.id WHERE o.estudiante_id = %s ORDER BY o.periodo DESC
            ''', (est_id,))
    return cursor.fetchall()


def leer_cargos_de_inventario(cursor, est_id):
    """Ventas de inventario del estudiante con lo ya pagado de cada una.

    Devuelve `COALESCE(v.pagado, 0)` porque quien decide si hay saldo y si el
    estado se muestra como «Pendiente (Abonado)» es el controlador.
    """
    cursor.execute('''
                SELECT v.id, v.fecha, v.estado, i.nombre, vd.cantidad, vd.subtotal, COALESCE(v.pagado, 0)
                FROM ventas v
                JOIN ventas_detalle vd ON v.id = vd.venta_id
                JOIN inventario i ON vd.inventario_id = i.id
                WHERE v.estudiante_id = %s
                ORDER BY v.fecha DESC
            ''', (est_id,))
    return cursor.fetchall()
