from app.database import get_cursor
from app.repositories.anios_lectivos_repository import condicion_anio
from app.services.anio_lectivo import exigir_asignacion_editable, exigir_plan_editable
from app.services.asignacion_academica import resolver_asignacion_academica_id_cursor


PLAN_SELECT = """
    SELECT
        pdc.id,
        pdc.asignacion_id,
        COALESCE(pdc.periodo, 1) AS periodo,
        pdc.unidad,
        pdc.proposito,
        COALESCE(pdc.clase, '') AS clase,
        pdc.estandar,
        pdc.dba,
        pdc.competencias,
        COALESCE(pdc.actividad_casa, '') AS actividad_casa,
        pdc.tema,
        pdc.fecha,
        pdc.imagen1,
        pdc.imagen2,
        a.profesor_id,
        CONCAT(pr.nombre, ' ', pr.apellido) AS profesor,
        c.nombre AS curso,
        m.nombre AS materia,
        pdc.created_at,
        pdc.updated_at,
        COALESCE(pdc.estado_revision, 'pendiente') AS estado_revision,
        COALESCE(pdc.version_revision, 1) AS version_revision,
        pdc.enviado_at,
        pdc.admin_visto_at,
        pdc.revisado_at,
        (
            SELECT COUNT(*)
            FROM plan_de_clases_observaciones pco
            WHERE pco.plan_id = pdc.id
        ) AS total_observaciones,
        (
            SELECT COUNT(*)
            FROM plan_de_clases_observaciones pco
            WHERE pco.plan_id = pdc.id
              AND pco.vista_por_profesor_at IS NULL
        ) AS observaciones_no_vistas,
        (
            SELECT MAX(pco.creada_at)
            FROM plan_de_clases_observaciones pco
            WHERE pco.plan_id = pdc.id
        ) AS ultima_observacion_at
    FROM plan_de_clases pdc
    JOIN asignaciones a ON pdc.asignacion_id = a.id
    JOIN profesor pr ON a.profesor_id = pr.id
    JOIN cursos c ON a.curso_id = c.id
    JOIN materias m ON a.materia_id = m.id
"""

REVISION_FINALIZADA_SQL = """
    plan_de_clases.estado_revision IN ('revisado', 'con_observaciones')
"""


def profesor_tiene_acceso_plan_de_clases_cursor(cursor, plan_id, profesor_id):
    cursor.execute(
        """
            SELECT 1
            FROM plan_de_clases pdc
            JOIN asignaciones a ON pdc.asignacion_id = a.id
            WHERE pdc.id = %s AND a.profesor_id = %s
            """,
        (plan_id, profesor_id),
    )
    return bool(cursor.fetchone())


def profesor_tiene_acceso_imagen_plan_de_clases_cursor(
    cursor,
    stored_path,
    profesor_id,
):
    cursor.execute(
        """
                SELECT 1
                FROM plan_de_clases pdc
                JOIN asignaciones a ON a.id = pdc.asignacion_id
                WHERE (pdc.imagen1 = %s OR pdc.imagen2 = %s)
                  AND a.profesor_id = %s
                """,
        (stored_path, stored_path, profesor_id),
    )
    return bool(cursor.fetchone())


def _row_to_plan(row):
    return {
        "id": row[0],
        "asignacion_id": row[1],
        "periodo": row[2],
        "unidad": row[3],
        "proposito": row[4],
        "clase": row[5],
        "estandar": row[6],
        "dba": row[7],
        "competencias": row[8],
        "actividad_casa": row[9],
        "tema": row[10],
        "fecha": row[11],
        "imagen1": row[12],
        "imagen2": row[13],
        "profesor_id": row[14],
        "profesor": row[15],
        "curso": row[16],
        "materia": row[17],
        "created_at": row[18],
        "updated_at": row[19],
        "estado_revision": row[20],
        "version_revision": row[21],
        "enviado_at": row[22],
        "admin_visto_at": row[23],
        "revisado_at": row[24],
        "total_observaciones": row[25],
        "observaciones_no_vistas": row[26],
        "ultima_observacion_at": row[27],
    }


def _crear_notificacion_admin(cursor, plan_id, version):
    cursor.execute(
        """
        INSERT INTO plan_de_clases_notificaciones_admin (
            plan_id, plan_version
        )
        VALUES (%s, %s)
        ON CONFLICT (plan_id, plan_version)
        DO UPDATE SET
            creada_at = CURRENT_TIMESTAMP,
            leida_at = NULL
        """,
        (plan_id, version),
    )


def _marcar_notificaciones_admin_leidas(cursor, plan_id, version):
    cursor.execute(
        """
        UPDATE plan_de_clases_notificaciones_admin
        SET leida_at = COALESCE(leida_at, CURRENT_TIMESTAMP)
        WHERE plan_id = %s
          AND plan_version <= %s
          AND leida_at IS NULL
        """,
        (plan_id, version),
    )


def guardar_plan_de_clases(plan, imagen1_path=None, imagen2_path=None, *, usuario):
    with get_cursor(commit=True) as cursor:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_asignacion_editable(cursor, plan.asignacion_id, usuario)
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, plan.asignacion_id)
        version_esperada = getattr(plan, "version_esperada", None)

        if version_esperada is not None:
            cursor.execute(
                """
                SELECT COALESCE(version_revision, 1)
                FROM plan_de_clases
                WHERE asignacion_id = %s AND fecha = %s
                FOR UPDATE
                """,
                (asignacion_id, plan.fecha),
            )
            version_actual_row = cursor.fetchone()
            version_actual = version_actual_row[0] if version_actual_row else None
            if (
                (version_esperada == 0 and version_actual is not None)
                or (version_esperada > 0 and version_actual != version_esperada)
            ):
                return {
                    "resultado": "version_desactualizada",
                    "version_actual": version_actual,
                }

        cursor.execute(
            f"""
            INSERT INTO plan_de_clases (
                asignacion_id, periodo, unidad, proposito, clase, estandar,
                dba, competencias, actividad_casa, tema, fecha, imagen1, imagen2
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (asignacion_id, fecha)
            DO UPDATE SET
                periodo = EXCLUDED.periodo,
                unidad = EXCLUDED.unidad,
                proposito = EXCLUDED.proposito,
                clase = EXCLUDED.clase,
                estandar = EXCLUDED.estandar,
                dba = EXCLUDED.dba,
                competencias = EXCLUDED.competencias,
                actividad_casa = EXCLUDED.actividad_casa,
                tema = EXCLUDED.tema,
                imagen1 = COALESCE(EXCLUDED.imagen1, plan_de_clases.imagen1),
                imagen2 = COALESCE(EXCLUDED.imagen2, plan_de_clases.imagen2),
                estado_revision = CASE
                    WHEN {REVISION_FINALIZADA_SQL}
                        THEN plan_de_clases.estado_revision
                    ELSE 'pendiente'
                END,
                version_revision = plan_de_clases.version_revision + 1,
                enviado_at = CURRENT_TIMESTAMP,
                admin_visto_at = CASE
                    WHEN {REVISION_FINALIZADA_SQL}
                        THEN plan_de_clases.admin_visto_at
                    ELSE NULL
                END,
                admin_visto_por = CASE
                    WHEN {REVISION_FINALIZADA_SQL}
                        THEN plan_de_clases.admin_visto_por
                    ELSE NULL
                END,
                revisado_at = CASE
                    WHEN {REVISION_FINALIZADA_SQL}
                        THEN plan_de_clases.revisado_at
                    ELSE NULL
                END,
                revisado_por = CASE
                    WHEN {REVISION_FINALIZADA_SQL}
                        THEN plan_de_clases.revisado_por
                    ELSE NULL
                END,
                updated_at = CURRENT_TIMESTAMP
            WHERE %s IS NULL
               OR COALESCE(plan_de_clases.version_revision, 1) = %s
            RETURNING id, version_revision, estado_revision
            """,
            (
                asignacion_id,
                plan.periodo,
                plan.unidad,
                plan.proposito,
                plan.clase,
                plan.estandar,
                plan.dba,
                plan.competencias,
                plan.actividad_casa,
                plan.tema,
                plan.fecha,
                imagen1_path,
                imagen2_path,
                version_esperada,
                version_esperada,
            ),
        )
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                """
                SELECT COALESCE(version_revision, 1)
                FROM plan_de_clases
                WHERE asignacion_id = %s AND fecha = %s
                """,
                (asignacion_id, plan.fecha),
            )
            version_actual_row = cursor.fetchone()
            return {
                "resultado": "version_desactualizada",
                "version_actual": version_actual_row[0] if version_actual_row else None,
            }

        if row[2] == "pendiente":
            _crear_notificacion_admin(cursor, row[0], row[1])
        return {
            "id": row[0],
            "version_revision": row[1],
            "estado_revision": row[2],
        }


def obtener_plan_por_dia(asignacion_id, fecha):
    with get_cursor() as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)
        cursor.execute(
            PLAN_SELECT
            + """
            WHERE pdc.asignacion_id = %s AND pdc.fecha = %s
            """,
            (asignacion_id, fecha),
        )
        row = cursor.fetchone()
        return _row_to_plan(row) if row else None


def obtener_planes_por_asignacion(asignacion_id, limit=None, offset=0):
    with get_cursor() as cursor:
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, asignacion_id)
        paginacion_sql = ""
        params = [asignacion_id]
        if limit is not None:
            paginacion_sql = " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
        cursor.execute(
            PLAN_SELECT
            + """
            WHERE pdc.asignacion_id = %s
            ORDER BY pdc.fecha DESC, pdc.created_at DESC
            """
            + paginacion_sql,
            tuple(params),
        )
        return [_row_to_plan(row) for row in cursor.fetchall()]


def obtener_plan_por_id(plan_id):
    with get_cursor() as cursor:
        cursor.execute(
            PLAN_SELECT
            + """
            WHERE pdc.id = %s
            """,
            (plan_id,),
        )
        row = cursor.fetchone()
        return _row_to_plan(row) if row else None


def listar_planes_admin(
    profesor_id=None,
    fecha_desde=None,
    fecha_hasta=None,
    busqueda=None,
    estado_revision=None,
    limit=50,
    offset=0,
    anio_lectivo_id=None,
):
    """Planes para revisar, de un año: el pedido o, sin el, el activo (año
    lectivo, fase 3, paso 3.5b). No valida que el año exista, porque abre su
    propia conexion y hacerlo costaria otra: un año inexistente da una lista
    vacia."""
    condiciones = []
    parametros = []

    if profesor_id:
        condiciones.append("a.profesor_id = %s")
        parametros.append(profesor_id)
    if fecha_desde:
        condiciones.append("pdc.fecha >= %s")
        parametros.append(fecha_desde)
    if fecha_hasta:
        condiciones.append("pdc.fecha <= %s")
        parametros.append(fecha_hasta)
    if busqueda:
        condiciones.append(
            """
            (
                pdc.tema ILIKE %s OR
                pdc.unidad ILIKE %s OR
                CONCAT(pr.nombre, ' ', pr.apellido) ILIKE %s OR
                c.nombre ILIKE %s OR
                m.nombre ILIKE %s
            )
            """
        )
        like = f"%{busqueda}%"
        parametros.extend([like, like, like, like, like])
    if estado_revision:
        if estado_revision == "pendiente":
            condiciones.append("pdc.estado_revision = 'pendiente'")
        elif estado_revision == "revisado":
            condiciones.append(
                "pdc.estado_revision IN ('revisado', 'con_observaciones')"
            )
        else:
            condiciones.append("pdc.estado_revision = %s")
            parametros.append(estado_revision)

    condicion, params_anio = condicion_anio("c.anio_lectivo_id", anio_lectivo_id)
    condiciones.append(condicion)
    parametros.extend(params_anio)

    where_sql = " WHERE " + " AND ".join(condiciones) if condiciones else ""

    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM plan_de_clases pdc
            JOIN asignaciones a ON pdc.asignacion_id = a.id
            JOIN profesor pr ON a.profesor_id = pr.id
            JOIN cursos c ON a.curso_id = c.id
            JOIN materias m ON a.materia_id = m.id
            """
            + where_sql,
            tuple(parametros),
        )
        total = cursor.fetchone()[0]

        cursor.execute(
            PLAN_SELECT
            + where_sql
            + """
            ORDER BY pdc.fecha DESC, pdc.created_at DESC
            LIMIT %s OFFSET %s
            """,
            tuple(parametros + [limit, offset]),
        )
        return {"total": total, "items": [_row_to_plan(row) for row in cursor.fetchall()]}


def _bloquear_version_plan(cursor, plan_id, version):
    cursor.execute(
        """
        SELECT version_revision
        FROM plan_de_clases
        WHERE id = %s
        FOR UPDATE
        """,
        (plan_id,),
    )
    row = cursor.fetchone()
    if not row:
        return {"resultado": "no_encontrado"}
    if row[0] != version:
        return {
            "resultado": "version_desactualizada",
            "version_actual": row[0],
        }
    return {"resultado": "ok", "version_actual": row[0]}


def actualizar_estado_revision_plan(
    plan_id,
    estado,
    admin_id,
    version,
    comentario=None,
):
    with get_cursor(commit=True) as cursor:
        bloqueo = _bloquear_version_plan(cursor, plan_id, version)
        if bloqueo["resultado"] != "ok":
            return bloqueo

        observacion_guardada = None
        if estado == "visto":
            cursor.execute(
                """
                UPDATE plan_de_clases
                SET
                    estado_revision = CASE
                        WHEN estado_revision = 'pendiente' THEN 'visto'
                        ELSE estado_revision
                    END,
                    admin_visto_por = CASE
                        WHEN admin_visto_at IS NULL THEN %s
                        ELSE admin_visto_por
                    END,
                    admin_visto_at = COALESCE(admin_visto_at, CURRENT_TIMESTAMP)
                WHERE id = %s
                RETURNING estado_revision, version_revision,
                          admin_visto_at, revisado_at
                """,
                (admin_id, plan_id),
            )
        else:
            if comentario:
                cursor.execute(
                    """
                    INSERT INTO plan_de_clases_observaciones (
                        plan_id, admin_id, plan_version, observacion
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, plan_id, admin_id, plan_version, observacion,
                              creada_at, vista_por_profesor_at
                    """,
                    (plan_id, admin_id, version, comentario),
                )
                observacion_guardada = cursor.fetchone()

            cursor.execute(
                """
                UPDATE plan_de_clases
                SET
                    estado_revision = 'revisado',
                    admin_visto_por = COALESCE(admin_visto_por, %s),
                    admin_visto_at = COALESCE(admin_visto_at, CURRENT_TIMESTAMP),
                    revisado_por = %s,
                    revisado_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING estado_revision, version_revision,
                          admin_visto_at, revisado_at
                """,
                (admin_id, admin_id, plan_id),
            )

        row = cursor.fetchone()
        _marcar_notificaciones_admin_leidas(cursor, plan_id, version)
        resultado = {
            "resultado": "ok",
            "estado_revision": row[0],
            "version_revision": row[1],
            "admin_visto_at": row[2],
            "revisado_at": row[3],
        }
        if observacion_guardada:
            resultado["observacion"] = {
                "id": observacion_guardada[0],
                "plan_id": observacion_guardada[1],
                "admin_id": observacion_guardada[2],
                "plan_version": observacion_guardada[3],
                "observacion": observacion_guardada[4],
                "creada_at": observacion_guardada[5],
                "vista_por_profesor_at": observacion_guardada[6],
            }
        return resultado


def agregar_observacion_plan(plan_id, admin_id, version, observacion):
    with get_cursor(commit=True) as cursor:
        bloqueo = _bloquear_version_plan(cursor, plan_id, version)
        if bloqueo["resultado"] != "ok":
            return bloqueo

        cursor.execute(
            """
            INSERT INTO plan_de_clases_observaciones (
                plan_id, admin_id, plan_version, observacion
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id, plan_id, admin_id, plan_version, observacion,
                      creada_at, vista_por_profesor_at
            """,
            (plan_id, admin_id, version, observacion),
        )
        row = cursor.fetchone()

        cursor.execute(
            """
            UPDATE plan_de_clases
            SET
                estado_revision = 'con_observaciones',
                admin_visto_por = COALESCE(admin_visto_por, %s),
                admin_visto_at = COALESCE(admin_visto_at, CURRENT_TIMESTAMP),
                revisado_por = NULL,
                revisado_at = NULL
            WHERE id = %s
            """,
            (admin_id, plan_id),
        )
        _marcar_notificaciones_admin_leidas(cursor, plan_id, version)

        return {
            "resultado": "ok",
            "observacion": {
                "id": row[0],
                "plan_id": row[1],
                "admin_id": row[2],
                "plan_version": row[3],
                "observacion": row[4],
                "creada_at": row[5],
                "vista_por_profesor_at": row[6],
            },
            "estado_revision": "con_observaciones",
            "version_revision": version,
        }


def listar_observaciones_plan(plan_id):
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                pco.id,
                pco.plan_id,
                pco.admin_id,
                COALESCE(u.nombre, 'Administracion') AS admin,
                pco.plan_version,
                pco.observacion,
                pco.creada_at,
                pco.vista_por_profesor_at
            FROM plan_de_clases_observaciones pco
            LEFT JOIN usuarios u ON u.id = pco.admin_id
            WHERE pco.plan_id = %s
            ORDER BY pco.creada_at DESC, pco.id DESC
            """,
            (plan_id,),
        )
        return [
            {
                "id": row[0],
                "plan_id": row[1],
                "admin_id": row[2],
                "admin": row[3],
                "plan_version": row[4],
                "observacion": row[5],
                "creada_at": row[6],
                "vista_por_profesor_at": row[7],
            }
            for row in cursor.fetchall()
        ]


def marcar_observacion_vista(plan_id, observacion_id, *, usuario):
    with get_cursor(commit=True) as cursor:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_plan_editable(cursor, plan_id, usuario)
        cursor.execute(
            """
            UPDATE plan_de_clases_observaciones
            SET vista_por_profesor_at = COALESCE(
                vista_por_profesor_at,
                CURRENT_TIMESTAMP
            )
            WHERE id = %s AND plan_id = %s
            RETURNING id, vista_por_profesor_at
            """,
            (observacion_id, plan_id),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {"id": row[0], "vista_por_profesor_at": row[1]}


def listar_notificaciones_admin(limit=8):
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*), COUNT(DISTINCT a.profesor_id)
            FROM plan_de_clases_notificaciones_admin n
            JOIN plan_de_clases pdc ON pdc.id = n.plan_id
            JOIN asignaciones a ON a.id = pdc.asignacion_id
            WHERE n.leida_at IS NULL
            """
        )
        conteos = cursor.fetchone()
        total = conteos[0]
        total_profesores = conteos[1]
        cursor.execute(
            """
            SELECT
                a.profesor_id,
                CONCAT(pr.nombre, ' ', pr.apellido) AS profesor,
                COUNT(*) AS cantidad,
                MAX(n.creada_at) AS ultima_fecha
            FROM plan_de_clases_notificaciones_admin n
            JOIN plan_de_clases pdc ON pdc.id = n.plan_id
            JOIN asignaciones a ON a.id = pdc.asignacion_id
            JOIN profesor pr ON pr.id = a.profesor_id
            WHERE n.leida_at IS NULL
            GROUP BY a.profesor_id, pr.nombre, pr.apellido
            ORDER BY MAX(n.creada_at) DESC, a.profesor_id
            LIMIT %s
            """,
            (limit,),
        )
        return {
            "total_no_leidas": total,
            "total_profesores": total_profesores,
            "items": [
                {
                    "id": row[0],
                    "tipo": "planes_profesor",
                    "profesor_id": row[0],
                    "profesor": row[1],
                    "cantidad": row[2],
                    "creada_at": row[3],
                }
                for row in cursor.fetchall()
            ],
        }


def listar_notificaciones_profesor(profesor_id, limit=8):
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM plan_de_clases_observaciones pco
            JOIN plan_de_clases pdc ON pdc.id = pco.plan_id
            JOIN asignaciones a ON a.id = pdc.asignacion_id
            WHERE a.profesor_id = %s
              AND pco.vista_por_profesor_at IS NULL
            """,
            (profesor_id,),
        )
        total = cursor.fetchone()[0]
        cursor.execute(
            """
            SELECT
                pco.id,
                pco.plan_id,
                pco.plan_version,
                pco.creada_at,
                pco.observacion,
                pdc.asignacion_id,
                pdc.fecha,
                pdc.tema,
                COALESCE(u.nombre, 'Administracion') AS admin,
                m.nombre AS materia,
                c.nombre AS curso
            FROM plan_de_clases_observaciones pco
            JOIN plan_de_clases pdc ON pdc.id = pco.plan_id
            JOIN asignaciones a ON a.id = pdc.asignacion_id
            JOIN materias m ON m.id = a.materia_id
            JOIN cursos c ON c.id = a.curso_id
            LEFT JOIN usuarios u ON u.id = pco.admin_id
            WHERE a.profesor_id = %s
              AND pco.vista_por_profesor_at IS NULL
            ORDER BY pco.creada_at DESC, pco.id DESC
            LIMIT %s
            """,
            (profesor_id, limit),
        )
        return {
            "total_no_leidas": total,
            "items": [
                {
                    "id": row[0],
                    "tipo": "observacion_plan",
                    "plan_id": row[1],
                    "plan_version": row[2],
                    "creada_at": row[3],
                    "observacion": row[4],
                    "asignacion_id": row[5],
                    "fecha": row[6],
                    "tema": row[7],
                    "admin": row[8],
                    "materia": row[9],
                    "curso": row[10],
                }
                for row in cursor.fetchall()
            ],
        }


def eliminar_imagen_plan(plan_id, slot, reiniciar_revision=False, *, usuario):
    if slot not in {"imagen1", "imagen2"}:
        raise ValueError("Imagen inválida")

    with get_cursor(commit=True) as cursor:
        # Año lectivo, paso 3.7: lo primero, en la conexion que ya se abrio.
        exigir_plan_editable(cursor, plan_id, usuario)
        cursor.execute(
            f"SELECT {slot}, estado_revision FROM plan_de_clases WHERE id = %s FOR UPDATE",
            (plan_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        if reiniciar_revision:
            cursor.execute(
                f"""
                UPDATE plan_de_clases
                SET
                    {slot} = NULL,
                    estado_revision = CASE
                        WHEN {REVISION_FINALIZADA_SQL}
                            THEN estado_revision
                        ELSE 'pendiente'
                    END,
                    version_revision = version_revision + 1,
                    enviado_at = CURRENT_TIMESTAMP,
                    admin_visto_at = CASE
                        WHEN {REVISION_FINALIZADA_SQL}
                            THEN admin_visto_at
                        ELSE NULL
                    END,
                    admin_visto_por = CASE
                        WHEN {REVISION_FINALIZADA_SQL}
                            THEN admin_visto_por
                        ELSE NULL
                    END,
                    revisado_at = CASE
                        WHEN {REVISION_FINALIZADA_SQL}
                            THEN revisado_at
                        ELSE NULL
                    END,
                    revisado_por = CASE
                        WHEN {REVISION_FINALIZADA_SQL}
                            THEN revisado_por
                        ELSE NULL
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING version_revision, estado_revision
                """,
                (plan_id,),
            )
            revision = cursor.fetchone()
            if revision[1] == "pendiente":
                _crear_notificacion_admin(cursor, plan_id, revision[0])
        else:
            cursor.execute(
                f"""
                UPDATE plan_de_clases
                SET {slot} = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (plan_id,),
            )
        return row[0]
