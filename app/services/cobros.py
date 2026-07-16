"""Servicio central de cobros academicos.

La fuente de deuda academica es `tipos_de_pagos` + `tipos_pagos_cursos`.
Los cursos son academicos; no definen matricula, mensualidad ni numero de meses.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from app.services.cartera import calcular_deuda_concepto


MAX_CUOTAS_ANUALES = 12


def normalizar_concepto(texto) -> str:
    return str(texto or "").strip().lower()


def _col_or_default(columnas, nombre, default_sql):
    return nombre if nombre in columnas else default_sql


def obtener_tipos_pago(cursor) -> list[dict]:
    cursor.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = ANY (current_schemas(false))
          AND table_name = 'tipos_de_pagos'
        """
    )
    columnas = {row[0] for row in cursor.fetchall()}
    col = _col_or_default

    cursor.execute(
        f"""
        SELECT id, nombre, valor,
            {col(columnas, 'tipo_cobro', "'unico'")} AS tipo_cobro,
            {col(columnas, 'activo', 'TRUE')} AS activo,
            {col(columnas, 'mes_inicial', 'NULL')} AS mes_inicial,
            {col(columnas, 'frecuencia_meses', '1')} AS frecuencia_meses,
            {col(columnas, 'dia_limite_mes', 'NULL')} AS dia_limite_mes,
            {col(columnas, 'dias_gracia', '0')} AS dias_gracia,
            {col(columnas, 'mora_tipo', 'NULL')} AS mora_tipo,
            {col(columnas, 'mora_valor', '0')} AS mora_valor
        FROM tipos_de_pagos
        ORDER BY id
        """
    )

    return [
        {
            "id": row[0],
            "nombre": row[1],
            "valor": float(row[2] or 0),
            "tipo_cobro": row[3] or "unico",
            "activo": bool(row[4]) if row[4] is not None else True,
            "mes_inicial": row[5],
            "frecuencia_meses": int(row[6]) if row[6] is not None else 1,
            "dia_limite_mes": row[7],
            "dias_gracia": int(row[8]) if row[8] is not None else 0,
            "mora_tipo": row[9],
            "mora_valor": float(row[10] or 0),
        }
        for row in cursor.fetchall()
    ]


def _tabla_puente_existe(cursor) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = ANY (current_schemas(false))
          AND table_name = 'tipos_pagos_cursos'
        """
    )
    return cursor.fetchone() is not None


def _tabla_valores_estudiantes_existe(cursor) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = ANY (current_schemas(false))
          AND table_name = 'tipos_pagos_estudiantes'
        """
    )
    return cursor.fetchone() is not None


def tabla_pagos_aplicaciones_existe(cursor) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = ANY (current_schemas(false))
          AND table_name = 'pagos_aplicaciones'
        """
    )
    return cursor.fetchone() is not None


def obtener_asignaciones_cobro_por_curso(cursor, curso_id: int) -> dict[int, float]:
    if not _tabla_puente_existe(cursor):
        return {}

    cursor.execute(
        """
        SELECT tipo_pago_id, valor
        FROM tipos_pagos_cursos
        WHERE curso_id = %s AND activo = TRUE
        """,
        (curso_id,),
    )
    return {row[0]: float(row[1] or 0) for row in cursor.fetchall()}


def obtener_valores_personalizados_estudiante(cursor, estudiante_id: int) -> dict[int, float]:
    if not _tabla_valores_estudiantes_existe(cursor):
        return {}

    cursor.execute(
        """
        SELECT tipo_pago_id, valor
        FROM tipos_pagos_estudiantes
        WHERE estudiante_id = %s AND activo = TRUE
        """,
        (estudiante_id,),
    )
    return {row[0]: float(row[1] or 0) for row in cursor.fetchall()}


def obtener_valores_personalizados_por_estudiantes(
    cursor,
    estudiante_ids: tuple[int, ...],
) -> dict[int, dict[int, float]]:
    if not estudiante_ids or not _tabla_valores_estudiantes_existe(cursor):
        return {}

    cursor.execute(
        """
        SELECT estudiante_id, tipo_pago_id, valor
        FROM tipos_pagos_estudiantes
        WHERE estudiante_id IN %s AND activo = TRUE
        """,
        (estudiante_ids,),
    )

    valores = {}
    for estudiante_id, tipo_pago_id, valor in cursor.fetchall():
        valores.setdefault(estudiante_id, {})[tipo_pago_id] = float(valor or 0)
    return valores


def obtener_curso_estudiante(cursor, estudiante_id: int):
    cursor.execute(
        """
        SELECT c.id
        FROM estudiantes e
        JOIN cursos c ON e.curso_id = c.id
        WHERE e.id = %s
        """,
        (estudiante_id,),
    )
    return cursor.fetchone()


def obtener_pagos_por_concepto_estudiantes(
    cursor,
    estudiante_ids: tuple[int, ...],
    *,
    hoy: Optional[date] = None,
) -> tuple[dict[int, dict[str, float]], dict[int, dict[str, float]], dict[int, dict[str, float]]]:
    if not estudiante_ids:
        return {}, {}, {}

    tiene_aplicaciones = tabla_pagos_aplicaciones_existe(cursor)
    excluir_adelantos = """
      AND NOT EXISTS (
          SELECT 1 FROM pagos_aplicaciones pa
          WHERE pa.pago_id = pagos.id
      )
    """ if tiene_aplicaciones else ""

    cursor.execute(
        f"""
        SELECT estudiante_id, LOWER(COALESCE(tipo_pago, '')), COALESCE(SUM(monto), 0)
        FROM pagos
        WHERE estudiante_id IN %s
          AND COALESCE(estado, 'Pagado') <> 'Anulado'
          {excluir_adelantos}
        GROUP BY estudiante_id, LOWER(COALESCE(tipo_pago, ''))
        """,
        (estudiante_ids,),
    )
    pagos_por_nombre = {}
    for estudiante_id, concepto, monto in cursor.fetchall():
        pagos_por_nombre.setdefault(estudiante_id, {})[concepto] = float(monto or 0)

    cursor.execute(
        f"""
        SELECT estudiante_id, LOWER(COALESCE(descripcion, '')), COALESCE(SUM(monto), 0)
        FROM pagos
        WHERE estudiante_id IN %s
          AND descripcion IS NOT NULL
          AND COALESCE(estado, 'Pagado') <> 'Anulado'
          {excluir_adelantos}
        GROUP BY estudiante_id, LOWER(COALESCE(descripcion, ''))
        """,
        (estudiante_ids,),
    )
    pagos_por_descripcion = {}
    for estudiante_id, concepto, monto in cursor.fetchall():
        pagos_por_descripcion.setdefault(estudiante_id, {})[concepto] = float(monto or 0)

    pagos_aplicados = {}
    if tiene_aplicaciones:
        mes_actual = (hoy or date.today()).replace(day=1)
        cursor.execute(
            """
            SELECT pa.estudiante_id, LOWER(TRIM(tp.nombre)), COALESCE(SUM(pa.monto), 0)
            FROM pagos_aplicaciones pa
            JOIN pagos p ON p.id = pa.pago_id
            JOIN tipos_de_pagos tp ON tp.id = pa.tipo_pago_id
            WHERE pa.estudiante_id IN %s
              AND pa.activo = TRUE
              AND pa.periodo <= %s
              AND COALESCE(p.estado, 'Pagado') <> 'Anulado'
            GROUP BY pa.estudiante_id, LOWER(TRIM(tp.nombre))
            """,
            (estudiante_ids, mes_actual),
        )
        for estudiante_id, concepto, monto in cursor.fetchall():
            pagos_aplicados.setdefault(estudiante_id, {})[concepto] = float(monto or 0)

    return pagos_por_nombre, pagos_por_descripcion, pagos_aplicados


def obtener_pagos_por_concepto(
    cursor,
    estudiante_id: int,
    *,
    hoy: Optional[date] = None,
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    pagos_nombre, pagos_descripcion, pagos_aplicados = obtener_pagos_por_concepto_estudiantes(
        cursor,
        (estudiante_id,),
        hoy=hoy,
    )
    return (
        pagos_nombre.get(estudiante_id, {}),
        pagos_descripcion.get(estudiante_id, {}),
        pagos_aplicados.get(estudiante_id, {}),
    )


def _valor_unitario_concepto(
    *,
    tipo_pago: dict,
    asignaciones_curso: dict[int, float],
    valores_estudiante: dict[int, float],
) -> tuple[Optional[float], str]:
    if tipo_pago["id"] not in asignaciones_curso:
        return None, "sin_asignacion"

    if tipo_pago["id"] in valores_estudiante:
        return max(0.0, float(valores_estudiante[tipo_pago["id"]] or 0)), "estudiante"

    valor_asignado = float(asignaciones_curso[tipo_pago["id"]] or 0)
    if valor_asignado > 0:
        return valor_asignado, "curso"

    return float(tipo_pago["valor"] or 0), "base"


def obtener_conceptos_mensuales_estudiante(cursor, estudiante_id: int) -> list[dict]:
    datos = obtener_curso_estudiante(cursor, estudiante_id)
    if not datos:
        raise ValueError("El estudiante seleccionado no existe.")

    curso_id = datos[0]
    asignaciones_curso = obtener_asignaciones_cobro_por_curso(cursor, curso_id)
    valores_estudiante = obtener_valores_personalizados_estudiante(cursor, estudiante_id)
    conceptos = []

    for tipo_pago in obtener_tipos_pago(cursor):
        if not tipo_pago["activo"] or normalizar_concepto(tipo_pago["tipo_cobro"]) != "mensual":
            continue

        valor_unitario, valor_origen = _valor_unitario_concepto(
            tipo_pago=tipo_pago,
            asignaciones_curso=asignaciones_curso,
            valores_estudiante=valores_estudiante,
        )
        if valor_unitario is None or valor_unitario <= 0:
            continue

        conceptos.append({
            **tipo_pago,
            "curso_id": curso_id,
            "valor_unitario": float(valor_unitario),
            "valor_origen": valor_origen,
        })

    return conceptos


def _calcular_deudas(
    *,
    tipos_pago: list[dict],
    asignaciones_curso: dict[int, float],
    pagos_nombre: dict[str, float],
    pagos_descripcion: dict[str, float],
    pagos_aplicados: Optional[dict[str, float]] = None,
    valores_estudiante: Optional[dict[int, float]] = None,
    hoy: Optional[date] = None,
) -> dict:
    deudas = []
    total_deuda = 0.0
    valores_estudiante = valores_estudiante or {}
    pagos_aplicados = pagos_aplicados or {}

    for tipo_pago in tipos_pago:
        tipo_cobro = normalizar_concepto(tipo_pago["tipo_cobro"] or "unico")
        if not tipo_pago["activo"] or tipo_cobro == "opcional":
            continue

        valor_unitario, valor_origen = _valor_unitario_concepto(
            tipo_pago=tipo_pago,
            asignaciones_curso=asignaciones_curso,
            valores_estudiante=valores_estudiante,
        )
        if valor_unitario is None:
            continue

        nombre = normalizar_concepto(tipo_pago["nombre"])
        pagado = pagos_nombre.get(nombre, 0.0)
        if pagado == 0.0:
            pagado = pagos_descripcion.get(nombre, 0.0)
        pagado += pagos_aplicados.get(nombre, 0.0)

        resultado = calcular_deuda_concepto(
            valor_unitario=max(0.0, float(valor_unitario or 0)),
            tipo_cobro=tipo_cobro,
            pagado=pagado,
            hoy=hoy,
            mes_inicial=tipo_pago.get("mes_inicial"),
            frecuencia_meses=tipo_pago.get("frecuencia_meses", 1),
            dia_limite_mes=tipo_pago.get("dia_limite_mes"),
            dias_gracia=tipo_pago.get("dias_gracia", 0),
            max_cuotas=MAX_CUOTAS_ANUALES,
            mora_tipo=tipo_pago.get("mora_tipo"),
            mora_valor=tipo_pago.get("mora_valor", 0),
        )

        deudas.append(
            {
                "concepto_id": tipo_pago["id"],
                "concepto": tipo_pago["nombre"],
                "tipo_cobro": tipo_cobro,
                "valor_total": resultado["valor_total"],
                "pagado": resultado["pagado"],
                "deuda": resultado["deuda"],
                "mora": resultado["mora"],
                "cuotas_vencidas": resultado["cuotas_vencidas"],
                "valor_unitario": max(0.0, float(valor_unitario or 0)),
                "valor_origen": valor_origen,
                "valor_personalizado": valor_origen == "estudiante",
            }
        )
        total_deuda += resultado["deuda"]

    return {
        "deudas": deudas,
        "total_deuda": total_deuda,
    }


def calcular_deudas_estudiante(
    cursor,
    estudiante_id: int,
    *,
    hoy: Optional[date] = None,
) -> dict:
    datos = obtener_curso_estudiante(cursor, estudiante_id)
    if not datos:
        raise ValueError("El estudiante seleccionado no existe.")

    curso_id = datos[0]
    asignaciones_curso = obtener_asignaciones_cobro_por_curso(cursor, curso_id)
    valores_estudiante = obtener_valores_personalizados_estudiante(cursor, estudiante_id)
    pagos_nombre, pagos_descripcion, pagos_aplicados = obtener_pagos_por_concepto(
        cursor,
        estudiante_id,
        hoy=hoy,
    )

    resultado = _calcular_deudas(
        tipos_pago=obtener_tipos_pago(cursor),
        asignaciones_curso=asignaciones_curso,
        valores_estudiante=valores_estudiante,
        pagos_nombre=pagos_nombre,
        pagos_descripcion=pagos_descripcion,
        pagos_aplicados=pagos_aplicados,
        hoy=hoy,
    )
    resultado["curso_id"] = curso_id
    return resultado


def calcular_deudas_desde_contexto(
    *,
    tipos_pago: list[dict],
    asignaciones_curso: dict[int, float],
    pagos_nombre: dict[str, float],
    pagos_descripcion: dict[str, float],
    pagos_aplicados: Optional[dict[str, float]] = None,
    valores_estudiante: Optional[dict[int, float]] = None,
    hoy: Optional[date] = None,
) -> dict:
    """Calcula deuda con datos ya precargados.

    Esta variante permite que reportes masivos como cartera vencida eviten N+1
    queries y aun asi usen exactamente las mismas reglas centrales.
    """
    return _calcular_deudas(
        tipos_pago=tipos_pago,
        asignaciones_curso=asignaciones_curso,
        valores_estudiante=valores_estudiante,
        pagos_nombre=pagos_nombre,
        pagos_descripcion=pagos_descripcion,
        pagos_aplicados=pagos_aplicados,
        hoy=hoy,
    )


def obtener_saldo_concepto(cursor, estudiante_id: int, concepto) -> float:
    concepto_normalizado = normalizar_concepto(concepto)
    if not concepto_normalizado:
        raise ValueError("Debe seleccionar un concepto de pago.")

    resultado = calcular_deudas_estudiante(cursor, estudiante_id)
    for deuda in resultado["deudas"]:
        if normalizar_concepto(deuda["concepto"]) == concepto_normalizado:
            return max(0.0, float(deuda["deuda"] or 0))

    return 0.0
