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

Año lectivo, fase 3 (paso 3.4): la lista, el conteo y la pagina aceptan un
año. Sin el, su SQL es el de siempre, letra por letra; con el, va por otro
camino que lee las matriculas de ese año. Ver `_MATRICULAS_DEL_ANIO`.
"""

from app.repositories.anios_lectivos_repository import condicion_anio


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


# Año lectivo, fase 3 (paso 3.4): mirando un año que no es el activo, la lista
# son los matriculados de ese año, cada uno con el curso que tuvo ese año (su
# `%s` es el año y va antes de los del `where_sql`). Sin año, o con el activo,
# las tres consultas de abajo quedan como siempre: todos los estudiantes, con
# su curso actual, porque Pagos y Ventas tienen que encontrar a cualquiera.
#
# La matricula entra como subconsulta con la columna renombrada para que los
# nombres sin prefijo del `where_sql` (`estado`, `nombre`...) sigan siendo solo
# de `estudiantes`.
_MATRICULAS_DEL_ANIO = """
            JOIN (
                SELECT estudiante_id, curso_id AS curso_del_anio
                FROM matriculas
                WHERE anio_lectivo_id = %s
            ) m ON m.estudiante_id = estudiantes.id
"""


def _columnas_de_la_lista(anio_lectivo_id):
    curso = "curso_id" if anio_lectivo_id is None else "m.curso_del_anio"
    return f"""
            SELECT
                id,
                nombre,
                apellido,
                documento_identidad,
                fecha_nacimiento,
                {curso},
                email,
                COALESCE(LOWER(estado), 'activo') AS estado
            FROM estudiantes"""


def _desde(anio_lectivo_id, parametros):
    """El `JOIN` de las matriculas del año, si se pide uno, y los parametros."""
    if anio_lectivo_id is None:
        return "", tuple(parametros)
    return _MATRICULAS_DEL_ANIO, (anio_lectivo_id, *parametros)


def listar_estudiantes(cursor, where_sql, parametros, anio_lectivo_id=None):
    """Lista sin paginar, ordenada por apellido y nombre.

    Con `anio_lectivo_id`, los matriculados de ese año (ver arriba).
    """
    if anio_lectivo_id is None:
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

    join, params = _desde(anio_lectivo_id, parametros)
    cursor.execute(
        _columnas_de_la_lista(anio_lectivo_id)
        + join
        + f"""
            {where_sql}
            ORDER BY apellido ASC, nombre ASC
        """,
        params,
    )
    return cursor.fetchall()


def contar_estudiantes(cursor, where_sql, parametros, anio_lectivo_id=None):
    """Total que acompana a la respuesta paginada."""
    if anio_lectivo_id is None:
        cursor.execute("SELECT COUNT(*) FROM estudiantes" + where_sql, tuple(parametros))
        return cursor.fetchone()[0]

    join, params = _desde(anio_lectivo_id, parametros)
    cursor.execute("SELECT COUNT(*) FROM estudiantes" + join + where_sql, params)
    return cursor.fetchone()[0]


def listar_estudiantes_paginado(cursor, where_sql, parametros, anio_lectivo_id=None):
    """Pagina de la lista. El `where_sql` es el mismo que uso el conteo."""
    if anio_lectivo_id is None:
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

    join, params = _desde(anio_lectivo_id, parametros)
    cursor.execute(
        _columnas_de_la_lista(anio_lectivo_id)
        + join
        + where_sql
        + """
            ORDER BY apellido ASC, nombre ASC
            LIMIT %s OFFSET %s
            """,
        params,
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
#
# Año lectivo (fase 3, paso 3.5b): notas, faltas y observaciones son las de un
# año, por el curso de su clase. Sin año, el activo, sin parametro nuevo; con
# 2027 activo, el expediente ya no suma lo de 2026.
# ---------------------------------------------------------------------------


def leer_promedios_por_materia(cursor, est_id, anio_lectivo_id=None):
    """Promedio de cada materia del estudiante, redondeado a un decimal en SQL.

    El promedio general NO sale de aqui: el controlador promedia estos
    promedios y redondea otra vez en Python.
    """
    condicion, params_anio = condicion_anio("c.anio_lectivo_id", anio_lectivo_id)
    cursor.execute(f'''
                SELECT m.nombre, ROUND(AVG(n.nota), 1) as promedio
                FROM notas_detalle n
                JOIN asignaciones a ON n.asignacion_id = a.id
                JOIN materias m ON a.materia_id = m.id
                JOIN cursos c ON c.id = a.curso_id
                WHERE n.estudiante_id = %s AND {condicion} GROUP BY m.id
            ''', (est_id, *params_anio))
    return cursor.fetchall()


def contar_inasistencias(cursor, est_id, anio_lectivo_id=None):
    """Numero de ausencias. El filtro es `ILIKE 'ausente'`, no una igualdad.

    Las de un año, por el curso de su clase. `asistencia.asignacion_id` admite
    nulos y hoy esas filas se cuentan: en el año activo se siguen contando, para
    que nada cambie; en otro año no, porque no se sabe de que año son.
    """
    condicion, params_anio = condicion_anio("c.anio_lectivo_id", anio_lectivo_id)
    sin_clase = "asignacion_id IS NULL OR " if anio_lectivo_id is None else ""
    cursor.execute(f'''
                SELECT count(*) FROM asistencia
                WHERE estudiante_id = %s AND estado ILIKE 'ausente'
                  AND ({sin_clase}asignacion_id IN (
                      SELECT a.id FROM asignaciones a
                      JOIN cursos c ON c.id = a.curso_id
                      WHERE {condicion}
                  ))
            ''', (est_id, *params_anio))
    return cursor.fetchone()[0]


def leer_observaciones(cursor, est_id, anio_lectivo_id=None):
    """Observaciones del estudiante con su materia y profesor, mas recientes primero.

    Las de un año, por el curso de su clase.
    """
    condicion, params_anio = condicion_anio("c.anio_lectivo_id", anio_lectivo_id)
    cursor.execute(f'''
                SELECT o.id, o.periodo, o.conductual, o.cognitivo, o.lenguaje, m.nombre AS materia_nombre, p.nombre || ' ' || p.apellido AS profesor_nombre FROM observaciones o JOIN asignaciones a ON o.asignacion_id = a.id JOIN materias m ON a.materia_id = m.id JOIN profesor p ON a.profesor_id = p.id JOIN cursos c ON c.id = a.curso_id WHERE o.estudiante_id = %s AND {condicion} ORDER BY o.periodo DESC
            ''', (est_id, *params_anio))
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
