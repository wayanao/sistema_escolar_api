"""Lecturas para la puntualidad de pagos (panel del admin, 2026-11-11).

Solo lee. Recibe el cursor y devuelve filas simples; las cuentas están en
`app/services/puntualidad.py`. Todo es del año activo y en consultas
agrupadas: el número de consultas no crece con los estudiantes.
"""
from __future__ import annotations

from app.repositories.anios_lectivos_repository import ANIO_ACTIVO_ID_SQL, condicion_anio


def leer_estudiantes_del_anio_activo(cursor) -> list[tuple]:
    """`(id, nombre, apellido, curso_id, curso_nombre)` de los estudiantes
    activos matriculados en el año activo, con el curso de esa matrícula (el
    que fija sus precios), como en la cartera vencida."""
    condicion, params = condicion_anio("m.anio_lectivo_id")
    cursor.execute(
        f"""
        SELECT e.id, e.nombre, e.apellido, c.id AS curso_id, c.nombre AS curso_nombre
        FROM estudiantes e
        JOIN matriculas m ON m.estudiante_id = e.id
        JOIN cursos c ON c.id = m.curso_id
        WHERE {condicion}
          AND COALESCE(e.estado, 'Activo') ILIKE 'activo'
        ORDER BY c.nombre, e.apellido, e.nombre
        """,
        params,
    )
    return cursor.fetchall()


def leer_precios_por_curso(cursor) -> dict[int, dict[int, float]]:
    """`{curso_id: {tipo_pago_id: valor}}` de `tipos_pagos_cursos` activos.
    Sin esa tabla (colegios viejos), vacío, como en la cartera vencida."""
    cursor.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = ANY (current_schemas(false))
          AND table_name = 'tipos_pagos_cursos'
        """
    )
    if cursor.fetchone() is None:
        return {}

    cursor.execute(
        """
        SELECT curso_id, tipo_pago_id, valor
        FROM tipos_pagos_cursos
        WHERE activo = TRUE
        """
    )
    precios: dict[int, dict[int, float]] = {}
    for curso_id, tipo_pago_id, valor in cursor.fetchall():
        precios.setdefault(curso_id, {})[tipo_pago_id] = float(valor or 0)
    return precios


def leer_pagos_de_cuotas(cursor, estudiante_ids: tuple[int, ...], *, sin_adelantos: bool) -> list[tuple]:
    """Los pagos del año activo sin anular, uno por fila:
    `(estudiante_id, tipo_pago, descripcion, monto, fecha)`, con `tipo_pago` y
    `descripcion` en minúscula para compararlos con el nombre del concepto,
    igual que la cartera. Con `sin_adelantos`, sin los que tienen meses
    aplicados: esos se leen aparte (`leer_adelantos`)."""
    excluir_adelantos = (
        """
          AND NOT EXISTS (
              SELECT 1 FROM pagos_aplicaciones pa
              WHERE pa.pago_id = pagos.id
          )
        """
        if sin_adelantos
        else ""
    )
    cursor.execute(
        f"""
        SELECT estudiante_id,
               LOWER(COALESCE(tipo_pago, '')),
               LOWER(COALESCE(descripcion, '')),
               monto,
               COALESCE(fecha, fecha_pago::timestamp)
        FROM pagos
        WHERE estudiante_id IN %s
          AND COALESCE(estado, 'Pagado') <> 'Anulado'
          AND pagos.anio_lectivo_id = {ANIO_ACTIVO_ID_SQL}
          {excluir_adelantos}
        """,
        (estudiante_ids,),
    )
    return cursor.fetchall()


def leer_adelantos(cursor, estudiante_ids: tuple[int, ...]) -> list[tuple]:
    """Los meses pagados por adelantado, vigentes y de pagos sin anular:
    `(estudiante_id, tipo_pago_id, periodo, monto, fecha_del_pago)`."""
    cursor.execute(
        """
        SELECT pa.estudiante_id, pa.tipo_pago_id, pa.periodo, pa.monto,
               COALESCE(p.fecha, p.fecha_pago::timestamp)
        FROM pagos_aplicaciones pa
        JOIN pagos p ON p.id = pa.pago_id
        WHERE pa.estudiante_id IN %s
          AND pa.activo = TRUE
          AND COALESCE(p.estado, 'Pagado') <> 'Anulado'
        """,
        (estudiante_ids,),
    )
    return cursor.fetchall()
