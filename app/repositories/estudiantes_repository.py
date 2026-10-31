"""Persistencia de `estudiantes`, extraida en la subcapa 6.1.

Cada funcion recibe el cursor que ya abrio el controlador y ejecuta una sola
sentencia. Ninguna abre, cierra, confirma ni revierte recursos: la propiedad de
la conexion, el cursor, el `commit`, el `rollback`, la normalizacion de estado,
la construccion del filtro y el formateo de la respuesta siguen siendo del
controlador, igual que en `pagos_repository`.

Las cadenas SQL heredadas conservan su sangria y los espacios significativos
con `\\x20` explicito. Excepcion de producto: en la fase 5.1 del año lectivo,
el INSERT y el UPDATE dejaron de incluir `curso_id`; ese valor vive en
`matriculas` y solo se copia desde el año activo.

Las consultas del filtro llegan ya construidas desde el controlador. El
fragmento `where_sql` no es entrada del cliente: sale de literales del propio
codigo y sus valores viajan siempre parametrizados.

Año lectivo, fase 3 (paso 3.4): la lista, el conteo y la pagina aceptan un
año. Sin el, su SQL es el de siempre, letra por letra; con el, va por otro
camino que lee las matriculas de ese año. Ver `_MATRICULAS_DEL_ANIO`.
"""

from app.core.nivel_academico import NOMBRE_MATERIA_ASISTENCIA_JORNADA
from app.repositories.anios_lectivos_repository import condicion_anio
# Las mismas reglas del reporte parcial para saber que materias salen: el
# resumen del estudiante tiene que mostrar las mismas (ver
# docs/funcionalidades/NOTAS_RESUMEN_ESTUDIANTE.md).
from app.repositories.boletin_repository import _curso_del_estudiante, _materia_visible


def insertar_estudiante(cursor, valores):
    """Inserta los 34 datos globales del estudiante y devuelve su id.

    El orden de `valores` es contrato: un desplazamiento guardaria el telefono
    del padre en el campo de la madre sin lanzar ningun error. El curso vive en
    `matriculas`; `sincronizar_curso_vigente` mantiene aqui su copia activa.
    """
    cursor.execute("""
            INSERT INTO estudiantes
            (
            nombre,\x20
            apellido,
            documento_identidad,
            fecha_nacimiento,
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, valores)
    return cursor.fetchone()[0]


def actualizar_estudiante(cursor, valores):
    """Actualiza los 34 datos globales y devuelve la fila afectada.

    `estado = COALESCE(%s, estado, 'activo')` es lo que hace que enviar `None`
    conserve el estado guardado en vez de sobrescribirlo.
    """
    cursor.execute("""
            UPDATE estudiantes
            SET nombre = %s,
            apellido = %s,
            documento_identidad = %s,
            fecha_nacimiento = %s,
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


# SISBÉN y lugar de residencia (docs/funcionalidades/SISBEN_RESIDENCIA.md). Van
# aparte de los 34 datos globales para no mover esa tupla. El nombre de cada
# columna es también el del campo de `EstudianteCreate`.
COLUMNAS_SISBEN_Y_RESIDENCIA = (
    "sisben",
    "sisben_grupo",
    "sisben_subgrupo",
    "sisben_nivel",
    "barrio",
    "municipio",
    "zona_residencia",
    "punto_referencia",
)


def guardar_sisben_y_residencia(cursor, estudiante_id, valores):
    """Reemplaza los ocho datos, en el orden de `COLUMNAS_SISBEN_Y_RESIDENCIA`.

    Devuelve cuántas filas cambió. Los nombres de columna salen de la tupla de
    arriba, nunca del cliente; los valores viajan parametrizados.
    """
    asignaciones = ", ".join(
        f"{columna} = %s" for columna in COLUMNAS_SISBEN_Y_RESIDENCIA
    )
    cursor.execute(
        f"UPDATE estudiantes SET {asignaciones} WHERE id = %s",
        (*valores, estudiante_id),
    )
    return cursor.rowcount


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


def leer_planilla_del_anio(cursor, est_id, anio_lectivo_id=None):
    """La planilla del estudiante en los cuatro periodos, para su resumen.

    Las mismas materias que `boletin_repository.leer_planilla_vigente` (la del
    reporte parcial): las del curso del estudiante en ese año, sin "ASISTENCIA
    DIARIA" y sin las inactivas, en el orden del boletin. La diferencia es que
    trae **todos los periodos a la vez**, para que cambiar de periodo en la
    pantalla no cueste otra peticion.

    Cada fila: `(asignacion_id, materia, nivel_del_curso, periodo, tipo_nota,
    nota, tipo_evaluacion, valoracion)`. Una materia sin notas trae una sola
    fila con el periodo vacio. El calculo vive en `app/core/notas_resumen.py`.
    """
    curso, params_curso = _curso_del_estudiante(anio_lectivo_id)
    materia_visible, params_materia = _materia_visible(anio_lectivo_id)
    cursor.execute(f'''
            WITH asignaciones_academicas AS (
                SELECT DISTINCT ON (COALESCE(a.asignacion_academica_id, a.id))
                    COALESCE(a.asignacion_academica_id, a.id) AS id,
                    a.curso_id,
                    a.materia_id,
                    a.profesor_id,
                    COALESCE(a.orden_boletin, 100) AS orden_boletin
                FROM asignaciones a
                WHERE a.activo = TRUE
                ORDER BY
                    COALESCE(a.asignacion_academica_id, a.id),
                    COALESCE(a.orden_boletin, 100),
                    a.id
            )
            SELECT
                asig.id AS asignacion_id,
                m.nombre AS materia,
                cu.nivel,
                nd.periodo,
                nd.descripcion,
                nd.nota,
                COALESCE(nd.tipo_evaluacion, 'numerica') AS tipo_evaluacion,
                nd.valoracion
            FROM estudiantes e
            JOIN asignaciones_academicas asig ON asig.curso_id = {curso}
            JOIN cursos cu ON cu.id = asig.curso_id
            JOIN materias m ON m.id = asig.materia_id
            JOIN profesor p ON p.id = asig.profesor_id
            LEFT JOIN notas_detalle nd
                ON nd.estudiante_id = e.id
                AND nd.asignacion_id = asig.id
            WHERE e.id = %s
              AND m.nombre <> %s
              AND {materia_visible}
            ORDER BY asig.orden_boletin, m.nombre, asig.id, nd.periodo, nd.id
        ''', (*params_curso, est_id, NOMBRE_MATERIA_ASISTENCIA_JORNADA, *params_materia))
    return cursor.fetchall()


def contar_inasistencias_por_periodo(cursor, est_id, anio_lectivo_id=None):
    """Ausencias por periodo y su total, en una fila: `(p1, p2, p3, p4, total)`.

    El filtro es `ILIKE 'ausente'`, no una igualdad. Un periodo vacio cuenta
    como el 1 (la columna tiene ese valor por defecto), y el total cuenta
    todas: es el mismo numero que daba antes la cuenta del año.

    Las de un año, por el curso de su clase. `asistencia.asignacion_id` admite
    nulos y hoy esas filas se cuentan: en el año activo se siguen contando, para
    que nada cambie; en otro año no, porque no se sabe de que año son.
    """
    condicion, params_anio = condicion_anio("c.anio_lectivo_id", anio_lectivo_id)
    sin_clase = "asignacion_id IS NULL OR " if anio_lectivo_id is None else ""
    cursor.execute(f'''
                SELECT
                    count(*) FILTER (WHERE COALESCE(periodo, 1) = 1),
                    count(*) FILTER (WHERE periodo = 2),
                    count(*) FILTER (WHERE periodo = 3),
                    count(*) FILTER (WHERE periodo = 4),
                    count(*)
                FROM asistencia
                WHERE estudiante_id = %s AND estado ILIKE 'ausente'
                  AND ({sin_clase}asignacion_id IN (
                      SELECT a.id FROM asignaciones a
                      JOIN cursos c ON c.id = a.curso_id
                      WHERE {condicion}
                  ))
            ''', (est_id, *params_anio))
    return cursor.fetchone()


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
