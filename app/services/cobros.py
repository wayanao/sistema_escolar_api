"""Servicio central de cobros academicos.

La fuente de deuda academica es `tipos_de_pagos` + `tipos_pagos_cursos`.
Los cursos son academicos; no definen matricula, mensualidad ni numero de meses.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from app.core.fechas import hoy_en_colombia
from app.repositories.anios_lectivos_repository import ANIO_ACTIVO_ID_SQL
from app.services.cartera import calcular_deuda_concepto, listar_cuotas_vencidas


MAX_CUOTAS_ANUALES = 12


def normalizar_concepto(texto) -> str:
    return str(texto or "").strip().lower()


def _col_or_default(columnas, nombre, default_sql):
    # `tp` es el alias de tipos_de_pagos en `obtener_tipos_pago`.
    return f"tp.{nombre}" if nombre in columnas else default_sql


def con_anio(anio_lectivo_id) -> dict:
    """Argumentos para calcular en un año que no es el activo.

    Vacio sin año: el camino de siempre, el del año activo, hace las mismas
    llamadas que antes de la fase 2 del año lectivo.
    """
    return {} if anio_lectivo_id is None else {"anio_lectivo_id": anio_lectivo_id}


def _anio_sql(anio_lectivo_id):
    """El año del calculo para comparar con una columna `anio_lectivo_id`.

    Sin año, la subconsulta del año activo, como siempre; con año, un
    parametro mas.
    """
    if anio_lectivo_id is None:
        return ANIO_ACTIVO_ID_SQL, ()
    return "%s", (int(anio_lectivo_id),)


def _filtro_anios_lectivos(anio_lectivo_id, alias="al"):
    """Filtro sobre `anios_lectivos <alias>`: el año activo, o el pedido."""
    if anio_lectivo_id is None:
        return f"{alias}.estado = 'activo'", ()
    return f"{alias}.id = %s", (int(anio_lectivo_id),)


def _concepto_desde_fila(row) -> dict:
    """Un concepto de pago a partir de una fila con las columnas de
    `obtener_tipos_pago`, en ese orden."""
    return {
        "id": row[0],
        "nombre": row[1],
        "valor": float(row[2] or 0),
        "tipo_cobro": row[3] or "unico",
        "activo": bool(row[4]) if row[4] is not None else True,
        "mes_inicial": row[5],
        "mes_final": int(row[6]) if row[6] is not None else 12,
        "frecuencia_meses": int(row[7]) if row[7] is not None else 1,
        "dia_limite_mes": row[8],
        "dias_gracia": int(row[9]) if row[9] is not None else 0,
        "mora_tipo": row[10],
        "mora_valor": float(row[11] or 0),
        "anio": int(row[12]),
    }


def obtener_tipos_pago(cursor, anio_lectivo_id=None) -> list[dict]:
    """Los conceptos de pago de un año, cada uno con su `anio`.

    Sin `anio_lectivo_id`, los del año activo. Los conceptos son por año
    (decision 17 de docs/funcionalidades/ANIO_LECTIVO.md): cobros, cartera y
    estado de cuenta calculan con los de un solo año. El `anio` viaja con cada
    concepto para contar sus cuotas en ese año y no en el del calendario, y
    sale de la misma consulta de siempre, sin una ida extra a la base.
    """
    cursor.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = ANY (current_schemas(false))
          AND table_name = 'tipos_de_pagos'
        """
    )
    columnas = {row[0] for row in cursor.fetchall()}
    col = _col_or_default
    filtro_anio, params_anio = _filtro_anios_lectivos(anio_lectivo_id)

    consulta = f"""
        SELECT tp.id, tp.nombre, tp.valor,
            {col(columnas, 'tipo_cobro', "'unico'")} AS tipo_cobro,
            {col(columnas, 'activo', 'TRUE')} AS activo,
            {col(columnas, 'mes_inicial', 'NULL')} AS mes_inicial,
            {col(columnas, 'mes_final', '12')} AS mes_final,
            {col(columnas, 'frecuencia_meses', '1')} AS frecuencia_meses,
            {col(columnas, 'dia_limite_mes', 'NULL')} AS dia_limite_mes,
            {col(columnas, 'dias_gracia', '0')} AS dias_gracia,
            {col(columnas, 'mora_tipo', 'NULL')} AS mora_tipo,
            {col(columnas, 'mora_valor', '0')} AS mora_valor,
            al.anio
        FROM tipos_de_pagos tp
        JOIN anios_lectivos al ON al.id = tp.anio_lectivo_id
        WHERE {filtro_anio}
        ORDER BY tp.id
        """
    # El año activo va sin parametros, como siempre.
    if params_anio:
        cursor.execute(consulta, params_anio)
    else:
        cursor.execute(consulta)

    return [_concepto_desde_fila(row) for row in cursor.fetchall()]


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


def obtener_curso_estudiante(cursor, estudiante_id: int, anio_lectivo_id=None):
    """El curso del estudiante en un año, que fija sus precios.

    Sin `anio_lectivo_id`, el del año activo. Sale de su matricula de ese año:
    cada año cobra con los precios de sus propios cursos. En el año activo es
    el mismo curso de `estudiantes.curso_id` (la consulta de control del
    curso vigente da 0).
    """
    filtro_anio, params_anio = _filtro_anios_lectivos(anio_lectivo_id)
    cursor.execute(
        f"""
        SELECT m.curso_id
        FROM matriculas m
        JOIN anios_lectivos al ON al.id = m.anio_lectivo_id
        WHERE m.estudiante_id = %s
          AND {filtro_anio}
        """,
        (estudiante_id, *params_anio),
    )
    return cursor.fetchone()


def _sin_curso_en_el_anio(anio_lectivo_id) -> ValueError:
    """El error cuando el estudiante no tiene curso en el año del calculo."""
    if anio_lectivo_id is None:
        return ValueError("El estudiante seleccionado no existe.")
    return ValueError("El estudiante no tiene matrícula en el año lectivo seleccionado.")


def obtener_pagos_por_concepto_estudiantes(
    cursor,
    estudiante_ids: tuple[int, ...],
    *,
    hoy: Optional[date] = None,
    anio_lectivo_id=None,
) -> tuple[dict[int, dict[str, float]], dict[int, dict[str, float]], dict[int, dict[str, float]]]:
    """Lo pagado por concepto en un año: por nombre, por descripcion y por
    meses aplicados.

    Sin `anio_lectivo_id`, el año activo. Solo cuentan los pagos de ese año y
    las aplicaciones de sus conceptos. Asi una matricula del año siguiente,
    pagada antes, no se suma a la del año en curso. Con un solo año, todos los
    pagos son de el y nada cambia.
    """
    if not estudiante_ids:
        return {}, {}, {}

    anio_sql, params_anio = _anio_sql(anio_lectivo_id)
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
          AND pagos.anio_lectivo_id = {anio_sql}
          {excluir_adelantos}
        GROUP BY estudiante_id, LOWER(COALESCE(tipo_pago, ''))
        """,
        (estudiante_ids, *params_anio),
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
          AND pagos.anio_lectivo_id = {anio_sql}
          {excluir_adelantos}
        GROUP BY estudiante_id, LOWER(COALESCE(descripcion, ''))
        """,
        (estudiante_ids, *params_anio),
    )
    pagos_por_descripcion = {}
    for estudiante_id, concepto, monto in cursor.fetchall():
        pagos_por_descripcion.setdefault(estudiante_id, {})[concepto] = float(monto or 0)

    pagos_aplicados = {}
    if tiene_aplicaciones:
        mes_actual = (hoy or hoy_en_colombia()).replace(day=1)
        cursor.execute(
            f"""
            SELECT pa.estudiante_id, LOWER(TRIM(tp.nombre)), COALESCE(SUM(pa.monto), 0)
            FROM pagos_aplicaciones pa
            JOIN pagos p ON p.id = pa.pago_id
            JOIN tipos_de_pagos tp ON tp.id = pa.tipo_pago_id
            WHERE pa.estudiante_id IN %s
              AND pa.activo = TRUE
              AND pa.periodo <= %s
              AND COALESCE(p.estado, 'Pagado') <> 'Anulado'
              AND tp.anio_lectivo_id = {anio_sql}
            GROUP BY pa.estudiante_id, LOWER(TRIM(tp.nombre))
            """,
            (estudiante_ids, mes_actual, *params_anio),
        )
        for estudiante_id, concepto, monto in cursor.fetchall():
            pagos_aplicados.setdefault(estudiante_id, {})[concepto] = float(monto or 0)

    return pagos_por_nombre, pagos_por_descripcion, pagos_aplicados


def obtener_pagos_por_concepto(
    cursor,
    estudiante_id: int,
    *,
    hoy: Optional[date] = None,
    anio_lectivo_id=None,
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    pagos_nombre, pagos_descripcion, pagos_aplicados = obtener_pagos_por_concepto_estudiantes(
        cursor,
        (estudiante_id,),
        hoy=hoy,
        **con_anio(anio_lectivo_id),
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


def obtener_conceptos_mensuales_estudiante(
    cursor, estudiante_id: int, anio_lectivo_id=None,
) -> list[dict]:
    """Los conceptos mensuales del estudiante en un año, con su precio.

    Sin `anio_lectivo_id`, el año activo. El precio es el del curso de su
    matricula en ese año.
    """
    datos = obtener_curso_estudiante(cursor, estudiante_id, **con_anio(anio_lectivo_id))
    if not datos:
        raise _sin_curso_en_el_anio(anio_lectivo_id)

    curso_id = datos[0]
    asignaciones_curso = obtener_asignaciones_cobro_por_curso(cursor, curso_id)
    valores_estudiante = obtener_valores_personalizados_estudiante(cursor, estudiante_id)
    conceptos = []

    for tipo_pago in obtener_tipos_pago(cursor, **con_anio(anio_lectivo_id)):
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


def obtener_motivos_personalizados_estudiante(cursor, estudiante_id: int) -> dict[int, Optional[str]]:
    """El motivo de cada valor personalizado vigente del estudiante."""
    if not _tabla_valores_estudiantes_existe(cursor):
        return {}

    cursor.execute(
        """
        SELECT tipo_pago_id, motivo
        FROM tipos_pagos_estudiantes
        WHERE estudiante_id = %s AND activo = TRUE
        """,
        (estudiante_id,),
    )
    return {row[0]: row[1] for row in cursor.fetchall()}


def obtener_valores_pago_estudiante(cursor, estudiante_id: int, anio_lectivo_id=None):
    """Lo que se le cobra al estudiante en un año, concepto por concepto.

    Devuelve `(curso_id, conceptos)`; sin `anio_lectivo_id`, el año activo.
    Son los mismos conceptos que cuenta `_calcular_deudas` (activos, no
    opcionales y con precio en el curso de su matricula), aunque todavia no
    deba nada: en noviembre de 2026 la mensualidad de 2027 no tiene cuotas
    vencidas y la ruta de deudas no la trae. Cada uno con el precio de su curso,
    su valor personalizado si tiene y lo que paga; los tres salen de
    `_valor_unitario_concepto`, la regla de los cobros, asi que lo que se ve es
    lo que se cobra. Solo lee.
    """
    datos = obtener_curso_estudiante(cursor, estudiante_id, **con_anio(anio_lectivo_id))
    if not datos:
        raise _sin_curso_en_el_anio(anio_lectivo_id)

    curso_id = datos[0]
    asignaciones_curso = obtener_asignaciones_cobro_por_curso(cursor, curso_id)
    valores_estudiante = obtener_valores_personalizados_estudiante(cursor, estudiante_id)
    motivos = (
        obtener_motivos_personalizados_estudiante(cursor, estudiante_id)
        if valores_estudiante
        else {}
    )
    conceptos = []

    for tipo_pago in obtener_tipos_pago(cursor, **con_anio(anio_lectivo_id)):
        tipo_cobro = normalizar_concepto(tipo_pago["tipo_cobro"] or "unico")
        if not tipo_pago["activo"] or tipo_cobro == "opcional":
            continue

        # La misma regla dos veces: sin el valor del estudiante da el precio
        # de su curso; con el, lo que paga.
        precio_curso, _origen = _valor_unitario_concepto(
            tipo_pago=tipo_pago,
            asignaciones_curso=asignaciones_curso,
            valores_estudiante={},
        )
        if precio_curso is None:
            continue
        valor_a_pagar, origen = _valor_unitario_concepto(
            tipo_pago=tipo_pago,
            asignaciones_curso=asignaciones_curso,
            valores_estudiante=valores_estudiante,
        )
        personalizado = origen == "estudiante"

        conceptos.append({
            "tipo_pago_id": tipo_pago["id"],
            "nombre": tipo_pago["nombre"],
            "tipo_cobro": tipo_cobro,
            "precio_curso": max(0.0, float(precio_curso or 0)),
            "valor_personalizado": valor_a_pagar if personalizado else None,
            "motivo": motivos.get(tipo_pago["id"]) if personalizado else None,
            "valor_a_pagar": max(0.0, float(valor_a_pagar or 0)),
        })

    return curso_id, conceptos


def obtener_cuotas_vencidas_estudiante(
    cursor,
    estudiante_id: int,
    *,
    hoy: Optional[date] = None,
    anio_lectivo_id=None,
) -> list[dict]:
    """Lista saldos de cuotas mensuales aplicando pagos antiguos por FIFO.

    Sin `anio_lectivo_id`, las del año activo. Las aplicaciones se leen por
    concepto, y los conceptos ya son del año pedido.
    """
    fecha_referencia = hoy or hoy_en_colombia()
    conceptos = obtener_conceptos_mensuales_estudiante(
        cursor, estudiante_id, **con_anio(anio_lectivo_id),
    )
    if not conceptos:
        return []

    pagos_nombre, pagos_descripcion, _ = obtener_pagos_por_concepto(
        cursor,
        estudiante_id,
        hoy=fecha_referencia,
        **con_anio(anio_lectivo_id),
    )
    cursor.execute(
        """
        SELECT pa.tipo_pago_id, pa.periodo, COALESCE(SUM(pa.monto), 0)
        FROM pagos_aplicaciones pa
        JOIN pagos p ON p.id = pa.pago_id
        WHERE pa.estudiante_id = %s
          AND pa.activo = TRUE
          AND COALESCE(p.estado, 'Pagado') <> 'Anulado'
        GROUP BY pa.tipo_pago_id, pa.periodo
        """,
        (estudiante_id,),
    )
    aplicaciones = {
        (int(tipo_pago_id), periodo): float(monto or 0)
        for tipo_pago_id, periodo, monto in cursor.fetchall()
    }

    opciones = []
    for concepto in conceptos:
        nombre_normalizado = normalizar_concepto(concepto["nombre"])
        pago_fifo = float(pagos_nombre.get(nombre_normalizado, 0) or 0)
        if pago_fifo == 0:
            pago_fifo = float(pagos_descripcion.get(nombre_normalizado, 0) or 0)

        valor_unitario = round(float(concepto["valor_unitario"] or 0), 2)
        cuotas = []
        for cuota in listar_cuotas_vencidas(
            hoy=fecha_referencia,
            anio=concepto.get("anio"),
            mes_inicial=concepto.get("mes_inicial"),
            mes_final=concepto.get("mes_final", 12),
            frecuencia_meses=concepto.get("frecuencia_meses", 1),
            dia_limite_mes=concepto.get("dia_limite_mes"),
            dias_gracia=concepto.get("dias_gracia", 0),
            max_cuotas=MAX_CUOTAS_ANUALES,
        ):
            aplicado = max(0.0, aplicaciones.get((concepto["id"], cuota.periodo), 0.0))
            saldo = max(0.0, valor_unitario - aplicado)
            if pago_fifo > 0 and saldo > 0:
                usado = min(pago_fifo, saldo)
                saldo -= usado
                pago_fifo -= usado

            saldo = round(saldo, 2)
            if saldo <= 0:
                continue
            cuotas.append({
                "periodo": cuota.periodo.isoformat(),
                "fecha_vencimiento": cuota.fecha_vencimiento.isoformat(),
                "valor_cuota": valor_unitario,
                "saldo": saldo,
                "estado": "parcial" if saldo < valor_unitario else "vencido",
            })

        if cuotas:
            opciones.append({
                "tipo_pago_id": concepto["id"],
                "concepto": concepto["nombre"],
                "valor_unitario": valor_unitario,
                "valor_origen": concepto["valor_origen"],
                "cuotas": cuotas,
            })

    return opciones


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
            anio=tipo_pago.get("anio"),
            mes_inicial=tipo_pago.get("mes_inicial"),
            mes_final=tipo_pago.get("mes_final", 12),
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
    anio_lectivo_id=None,
) -> dict:
    """La deuda del estudiante por concepto en un año; sin `anio_lectivo_id`,
    en el año activo. Conceptos, precios y pagos son todos de ese año."""
    datos = obtener_curso_estudiante(cursor, estudiante_id, **con_anio(anio_lectivo_id))
    if not datos:
        raise _sin_curso_en_el_anio(anio_lectivo_id)

    curso_id = datos[0]
    asignaciones_curso = obtener_asignaciones_cobro_por_curso(cursor, curso_id)
    valores_estudiante = obtener_valores_personalizados_estudiante(cursor, estudiante_id)
    pagos_nombre, pagos_descripcion, pagos_aplicados = obtener_pagos_por_concepto(
        cursor,
        estudiante_id,
        hoy=hoy,
        **con_anio(anio_lectivo_id),
    )

    resultado = _calcular_deudas(
        tipos_pago=obtener_tipos_pago(cursor, **con_anio(anio_lectivo_id)),
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


def _conceptos_por_anio(cursor, anio_lectivo_ids: tuple[int, ...]) -> dict[int, list[dict]]:
    """Los conceptos de varios años en una consulta, agrupados por `anio`.

    A diferencia de `obtener_tipos_pago`, no revisa columnas: los años
    anteriores solo existen en colegios con todas las migraciones aplicadas.
    """
    cursor.execute(
        """
        SELECT tp.id, tp.nombre, tp.valor, tp.tipo_cobro, tp.activo,
            tp.mes_inicial, tp.mes_final, tp.frecuencia_meses, tp.dia_limite_mes,
            tp.dias_gracia, tp.mora_tipo, tp.mora_valor, al.anio
        FROM tipos_de_pagos tp
        JOIN anios_lectivos al ON al.id = tp.anio_lectivo_id
        WHERE tp.anio_lectivo_id IN %s
        ORDER BY tp.id
        """,
        (anio_lectivo_ids,),
    )
    conceptos = {}
    for row in cursor.fetchall():
        concepto = _concepto_desde_fila(row)
        conceptos.setdefault(concepto["anio"], []).append(concepto)
    return conceptos


def _asignaciones_de_cursos(cursor, curso_ids: tuple[int, ...]) -> dict[int, dict[int, float]]:
    """Los precios por concepto de varios cursos, en una consulta."""
    cursor.execute(
        """
        SELECT curso_id, tipo_pago_id, valor
        FROM tipos_pagos_cursos
        WHERE curso_id IN %s AND activo = TRUE
        """,
        (curso_ids,),
    )
    asignaciones = {}
    for curso_id, tipo_pago_id, valor in cursor.fetchall():
        asignaciones.setdefault(curso_id, {})[tipo_pago_id] = float(valor or 0)
    return asignaciones


def _pagado_por_estudiante_y_anio(cursor, estudiante_ids, anio_lectivo_ids, hoy):
    """Lo pagado por concepto, agrupado por estudiante y año, en tres consultas.

    Las mismas reglas de `obtener_pagos_por_concepto_estudiantes` (sin
    anulados, los adelantos aparte y solo los meses ya maduros), pero para
    varios años a la vez. Cada resultado va por `(estudiante_id,
    anio_lectivo_id)`.
    """
    sumas = []
    for columna, solo_con_texto in (("tipo_pago", ""), ("descripcion", "AND descripcion IS NOT NULL")):
        cursor.execute(
            f"""
            SELECT estudiante_id, anio_lectivo_id, LOWER(COALESCE({columna}, '')),
                   COALESCE(SUM(monto), 0)
            FROM pagos
            WHERE estudiante_id IN %s
              AND anio_lectivo_id IN %s
              {solo_con_texto}
              AND COALESCE(estado, 'Pagado') <> 'Anulado'
              AND NOT EXISTS (
                  SELECT 1 FROM pagos_aplicaciones pa
                  WHERE pa.pago_id = pagos.id
              )
            GROUP BY estudiante_id, anio_lectivo_id, LOWER(COALESCE({columna}, ''))
            """,
            (estudiante_ids, anio_lectivo_ids),
        )
        suma = {}
        for estudiante_id, anio_lectivo_id, concepto, monto in cursor.fetchall():
            suma.setdefault((estudiante_id, anio_lectivo_id), {})[concepto] = float(monto or 0)
        sumas.append(suma)

    mes_actual = (hoy or hoy_en_colombia()).replace(day=1)
    cursor.execute(
        """
        SELECT pa.estudiante_id, tp.anio_lectivo_id, LOWER(TRIM(tp.nombre)),
               COALESCE(SUM(pa.monto), 0)
        FROM pagos_aplicaciones pa
        JOIN pagos p ON p.id = pa.pago_id
        JOIN tipos_de_pagos tp ON tp.id = pa.tipo_pago_id
        WHERE pa.estudiante_id IN %s
          AND tp.anio_lectivo_id IN %s
          AND pa.activo = TRUE
          AND pa.periodo <= %s
          AND COALESCE(p.estado, 'Pagado') <> 'Anulado'
        GROUP BY pa.estudiante_id, tp.anio_lectivo_id, LOWER(TRIM(tp.nombre))
        """,
        (estudiante_ids, anio_lectivo_ids, mes_actual),
    )
    aplicados = {}
    for estudiante_id, anio_lectivo_id, concepto, monto in cursor.fetchall():
        aplicados.setdefault((estudiante_id, anio_lectivo_id), {})[concepto] = float(monto or 0)

    pagos_nombre, pagos_descripcion = sumas
    return pagos_nombre, pagos_descripcion, aplicados


def calcular_deudas_anios_anteriores(
    cursor,
    estudiante_ids: tuple[int, ...],
    *,
    hoy: Optional[date] = None,
    anio_lectivo_id=None,
    asignaciones_por_curso: Optional[dict[int, dict[int, float]]] = None,
    valores_por_estudiante: Optional[dict[int, dict[int, float]]] = None,
) -> dict[int, list[dict]]:
    """La deuda de cada año anterior en que cada estudiante tuvo matricula.

    Decision 2 de docs/funcionalidades/ANIO_LECTIVO.md: la deuda de años
    anteriores se sigue viendo, aparte de la del año. "Anterior" es anterior
    al año que se mira (`anio_lectivo_id`; sin el, el activo). Cada año se
    calcula con la misma regla de siempre (`_calcular_deudas`) y con sus
    propios conceptos, el curso de su matricula, sus precios y sus pagos.

    Devuelve `{estudiante_id: [{anio_lectivo_id, anio, curso_id, deudas,
    total_deuda}, ...]}`, del año mas viejo al mas nuevo, solo con los años
    y los conceptos que tienen deuda.

    Mientras no haya años anteriores hace una sola consulta. Si los hay,
    calcula todos los estudiantes y años de una vez: las consultas no crecen
    con los estudiantes. Quien ya cargo los precios por curso o los valores
    por estudiante (cartera) los pasa y se ahorra esas consultas.
    """
    if not estudiante_ids:
        return {}

    filtro_anio, params_anio = _filtro_anios_lectivos(anio_lectivo_id, alias="referencia")
    cursor.execute(
        f"""
        SELECT m.estudiante_id, m.anio_lectivo_id, al.anio, m.curso_id
        FROM matriculas m
        JOIN anios_lectivos al ON al.id = m.anio_lectivo_id
        WHERE m.estudiante_id IN %s
          AND m.curso_id IS NOT NULL
          AND al.anio < (
              SELECT referencia.anio FROM anios_lectivos referencia
              WHERE {filtro_anio}
          )
        ORDER BY m.estudiante_id, al.anio
        """,
        (estudiante_ids, *params_anio),
    )
    matriculas = cursor.fetchall()
    if not matriculas:
        return {}

    anio_lectivo_ids = tuple(sorted({fila[1] for fila in matriculas}))
    conceptos = _conceptos_por_anio(cursor, anio_lectivo_ids)
    if asignaciones_por_curso is None:
        asignaciones_por_curso = _asignaciones_de_cursos(
            cursor, tuple(sorted({fila[3] for fila in matriculas})),
        )
    if valores_por_estudiante is None:
        valores_por_estudiante = obtener_valores_personalizados_por_estudiantes(
            cursor, tuple(estudiante_ids),
        )
    pagos_nombre, pagos_descripcion, pagos_aplicados = _pagado_por_estudiante_y_anio(
        cursor, tuple(estudiante_ids), anio_lectivo_ids, hoy,
    )

    resultado = {}
    for estudiante_id, anio_id, anio, curso_id in matriculas:
        clave = (estudiante_id, anio_id)
        resumen = _calcular_deudas(
            tipos_pago=conceptos.get(anio, []),
            asignaciones_curso=asignaciones_por_curso.get(curso_id, {}),
            valores_estudiante=valores_por_estudiante.get(estudiante_id, {}),
            pagos_nombre=pagos_nombre.get(clave, {}),
            pagos_descripcion=pagos_descripcion.get(clave, {}),
            pagos_aplicados=pagos_aplicados.get(clave, {}),
            hoy=hoy,
        )
        deudas = [deuda for deuda in resumen["deudas"] if deuda["deuda"] > 0]
        if deudas:
            resultado.setdefault(estudiante_id, []).append({
                "anio_lectivo_id": anio_id,
                "anio": anio,
                "curso_id": curso_id,
                "deudas": deudas,
                "total_deuda": sum(deuda["deuda"] for deuda in deudas),
            })
    return resultado


def obtener_saldo_concepto(cursor, estudiante_id: int, concepto, anio_lectivo_id=None) -> float:
    """Lo que se debe de un concepto en un año; sin `anio_lectivo_id`, en el
    año activo."""
    concepto_normalizado = normalizar_concepto(concepto)
    if not concepto_normalizado:
        raise ValueError("Debe seleccionar un concepto de pago.")

    resultado = calcular_deudas_estudiante(cursor, estudiante_id, **con_anio(anio_lectivo_id))
    for deuda in resultado["deudas"]:
        if normalizar_concepto(deuda["concepto"]) == concepto_normalizado:
            return max(0.0, float(deuda["deuda"] or 0))

    return 0.0
