from app.database import get_connection, get_cursor
import datetime
import re
from zoneinfo import ZoneInfo

from psycopg2 import IntegrityError

from app.repositories.pagos_repository import (
    abonar_a_venta,
    ajustar_venta_tras_anulacion,
    asignar_venta_a_pago,
    contar_pagos_de_estudiante,
    desactivar_aplicaciones_de_pago,
    insertar_aplicacion,
    insertar_pago,
    insertar_pago_adelantado,
    leer_aplicaciones_vigentes,
    leer_pago_para_anular,
    leer_saldo_de_venta,
    leer_venta_para_anular,
    listar_pagos_de_estudiante,
    listar_pagos_de_estudiante_paginado,
    marcar_pago_anulado,
    marcar_venta_pagada,
)
from app.services.anio_lectivo import exigir_anio_lectivo
from app.services.cobros import (
    con_anio,
    obtener_conceptos_mensuales_estudiante,
    obtener_cuotas_vencidas_estudiante,
    obtener_saldo_concepto,
)

ZONA_HORARIA_LOCAL = ZoneInfo("America/Bogota")
VENTA_ID_PATTERN = re.compile(r"Cargo\s+#(\d+)", re.IGNORECASE)
MESES_ES = (
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
)


class MigracionPagosAdelantadosPendienteError(RuntimeError):
    pass


def _calcular_total_pago(pago):
    metodos = getattr(pago, 'metodos', None)
    if metodos and isinstance(metodos, list) and len(metodos) > 0:
        return sum(float(metodo.monto or 0) for metodo in metodos)
    return float(getattr(pago, 'monto', 0) or 0)


def _formatear_tipo_pago(metodo):
    tipo = str(getattr(metodo, "tipo", "") or "").strip()
    nota = str(getattr(metodo, "nota", "") or "").strip()
    if nota:
        return f"{tipo} - {nota}"
    return tipo


def _fecha_pago_local(fecha_seleccionada=None):
    ahora_bogota = datetime.datetime.now(ZONA_HORARIA_LOCAL)
    if fecha_seleccionada:
        return datetime.datetime.combine(fecha_seleccionada, ahora_bogota.time()).replace(tzinfo=None)
    return ahora_bogota.replace(tzinfo=None)


def _tabla_pagos_aplicaciones_existe(cursor):
    cursor.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = ANY (current_schemas(false))
          AND table_name = 'pagos_aplicaciones'
        """
    )
    return cursor.fetchone() is not None


def _exigir_tabla_pagos_aplicaciones(cursor):
    if not _tabla_pagos_aplicaciones_existe(cursor):
        raise MigracionPagosAdelantadosPendienteError(
            "La función de pagos adelantados requiere la migración "
            "20260716_pagos_adelantados.sql."
        )


def _exigir_indice_aplicaciones_parciales(cursor):
    cursor.execute(
        """
        SELECT 1 FROM pg_indexes
        WHERE schemaname = ANY (current_schemas(false))
          AND indexname = 'uq_pagos_aplicaciones_pago_periodo_activas'
        """
    )
    if cursor.fetchone() is None:
        raise MigracionPagosAdelantadosPendienteError(
            "La selección de meses vencidos requiere la migración "
            "20260716_pagos_aplicaciones_parciales.sql."
        )


def _tomar_lock(cursor, clave):
    cursor.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (clave,))


def _bloquear_aplicaciones_concepto(cursor, estudiante_id, tipo_pago_id):
    _tomar_lock(cursor, f"pagos_aplicaciones:{estudiante_id}:{tipo_pago_id}")


def _bloquear_registro_de_pagos(cursor, estudiante_id):
    """Serializa el registro de pagos de un estudiante dentro de la transacción.

    Sin él, dos peticiones simultáneas leen la deuda antes de que ninguna
    confirme, las dos pasan la validación de saldo y las dos insertan: un doble
    clic cobra dos veces. El lock es de transacción, así que se libera solo en el
    `commit` o el `rollback`.

    No introduce riesgo de interbloqueo con `_bloquear_aplicaciones_concepto`:
    donde se toman los dos, este va siempre primero, y el camino de adelantos
    solo toma el de concepto.
    """
    _tomar_lock(cursor, f"pagos:registro:{estudiante_id}")


def _periodos_programados(concepto, hoy):
    """Meses que todavia se pueden adelantar de un concepto mensual.

    Son meses del año del concepto (su año lectivo), no del calendario: en el
    año en curso, los que faltan despues del de hoy; en un año que no ha
    empezado, todos; en uno que ya termino, ninguno.
    """
    frecuencia = max(1, int(concepto.get("frecuencia_meses") or 1))
    mes_inicial = concepto.get("mes_inicial")
    mes_final = int(concepto.get("mes_final") or 12)
    if not 1 <= mes_final <= 12:
        mes_final = 12
    anio = int(concepto.get("anio") or hoy.year)
    if anio < hoy.year:
        return []
    primer_mes = hoy.month + 1 if anio == hoy.year else 1
    periodos = []

    for mes in range(primer_mes, mes_final + 1):
        if mes_inicial:
            inicio = int(mes_inicial)
            if mes < inicio or (mes - inicio) % frecuencia != 0:
                continue
        elif (mes - primer_mes) % frecuencia != 0:
            continue
        periodos.append(datetime.date(anio, mes, 1))

    return periodos


def _etiqueta_periodo(periodo):
    return f"{MESES_ES[periodo.month - 1]} {periodo.year}"


def _periodos_disponibles(cursor, estudiante_id, concepto, hoy):
    filas = leer_aplicaciones_vigentes(cursor, estudiante_id, concepto["id"])
    aplicados = {row[0]: float(row[1] or 0) for row in filas}
    valor_unitario = round(float(concepto["valor_unitario"] or 0), 2)
    periodos = []
    for periodo in _periodos_programados(concepto, hoy):
        monto_aplicado = max(0.0, aplicados.get(periodo, 0.0))
        saldo = round(max(0.0, valor_unitario - monto_aplicado), 2)
        if saldo <= 0:
            continue
        periodos.append({
            "periodo": periodo,
            "saldo": saldo,
            "estado": "parcial" if saldo < valor_unitario else "disponible",
        })
    return periodos


def _serializar_opcion_adelanto(cursor, estudiante_id, concepto, hoy):
    periodos = _periodos_disponibles(cursor, estudiante_id, concepto, hoy)
    return {
        "tipo_pago_id": concepto["id"],
        "concepto": concepto["nombre"],
        "valor_unitario": round(float(concepto["valor_unitario"]), 2),
        "valor_origen": concepto["valor_origen"],
        "mes_final": int(concepto.get("mes_final") or 12),
        "periodos_disponibles": [
            {
                "periodo": item["periodo"].isoformat(),
                "etiqueta": _etiqueta_periodo(item["periodo"]),
                "saldo": item["saldo"],
                "estado": item["estado"],
            }
            for item in periodos
        ],
        "max_meses": len(periodos),
        "total_disponible": round(sum(item["saldo"] for item in periodos), 2),
    }


def _distribuir_monto_adelantado(periodos, monto):
    restante = int(round(float(monto or 0) * 100))
    if restante <= 0:
        raise ValueError("El monto a distribuir debe ser mayor a cero.")

    distribuciones = []
    for item in periodos:
        saldo_centavos = int(round(float(item["saldo"] or 0) * 100))
        usado = min(restante, saldo_centavos)
        if usado <= 0:
            continue
        distribuciones.append({**item, "monto_aplicado": usado / 100})
        restante -= usado
        if restante == 0:
            break

    if restante > 0:
        disponible = sum(float(item["saldo"] or 0) for item in periodos)
        raise ValueError(
            f"Solo hay ${disponible:,.2f} disponibles para adelantar dentro del año actual."
        )
    return distribuciones


def obtener_opciones_adelanto_controller(estudiante_id, hoy=None, anio_lectivo_id=None):
    """Meses que se pueden adelantar; sin `anio_lectivo_id`, del año activo.

    Con el año siguiente en preparacion, en diciembre se ofrecen sus meses.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _exigir_tabla_pagos_aplicaciones(cursor)
        if anio_lectivo_id is not None:
            exigir_anio_lectivo(cursor, anio_lectivo_id)
        fecha_referencia = hoy or datetime.datetime.now(ZONA_HORARIA_LOCAL).date()
        opciones = [
            _serializar_opcion_adelanto(cursor, estudiante_id, concepto, fecha_referencia)
            for concepto in obtener_conceptos_mensuales_estudiante(
                cursor, estudiante_id, **con_anio(anio_lectivo_id),
            )
        ]
        return {"estudiante_id": estudiante_id, "opciones": opciones}
    finally:
        cursor.close()
        conn.close()


def obtener_opciones_vencidas_controller(estudiante_id, hoy=None, anio_lectivo_id=None):
    """Meses vencidos por pagar; sin `anio_lectivo_id`, del año activo."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _exigir_tabla_pagos_aplicaciones(cursor)
        if anio_lectivo_id is not None:
            exigir_anio_lectivo(cursor, anio_lectivo_id)
        fecha_referencia = hoy or datetime.datetime.now(ZONA_HORARIA_LOCAL).date()
        return {
            "estudiante_id": estudiante_id,
            "opciones": obtener_cuotas_vencidas_estudiante(
                cursor,
                estudiante_id,
                hoy=fecha_referencia,
                **con_anio(anio_lectivo_id),
            ),
        }
    finally:
        cursor.close()
        conn.close()


def _preparar_aplicaciones_pago(cursor, pago, hoy=None):
    aplicaciones = list(getattr(pago, "aplicaciones", None) or [])
    if not aplicaciones:
        return None
    if getattr(pago, "venta_id", None):
        raise ValueError("Los cargos de inventario no admiten aplicaciones mensuales.")

    _exigir_tabla_pagos_aplicaciones(cursor)
    _exigir_indice_aplicaciones_parciales(cursor)
    tipo_pago_ids = {int(item.tipo_pago_id) for item in aplicaciones}
    if len(tipo_pago_ids) != 1:
        raise ValueError("Todas las cuotas seleccionadas deben pertenecer al mismo concepto.")

    tipo_pago_id = next(iter(tipo_pago_ids))
    _bloquear_aplicaciones_concepto(cursor, pago.estudiante_id, tipo_pago_id)
    fecha_referencia = hoy or datetime.datetime.now(ZONA_HORARIA_LOCAL).date()
    # Las cuotas, y por lo tanto los conceptos validos, son las del año del
    # pago: una aplicacion a un concepto de otro año no aparece aqui.
    opciones = obtener_cuotas_vencidas_estudiante(
        cursor,
        pago.estudiante_id,
        hoy=fecha_referencia,
        **con_anio(getattr(pago, "anio_lectivo_id", None)),
    )
    opcion = next(
        (item for item in opciones if int(item["tipo_pago_id"]) == tipo_pago_id),
        None,
    )
    if not opcion:
        raise ValueError("El concepto no tiene cuotas vencidas disponibles para pagar.")
    if str(getattr(pago, "descripcion", "") or "").strip().lower() != opcion["concepto"].strip().lower():
        raise ValueError("El concepto seleccionado no coincide con las cuotas enviadas.")

    disponibles = {item["periodo"]: item for item in opcion["cuotas"]}
    normalizadas = []
    vistos = set()
    for item in aplicaciones:
        periodo = item.periodo
        periodo_iso = periodo.isoformat()
        if periodo.day != 1 or periodo_iso in vistos:
            raise ValueError("Cada mes debe aparecer una sola vez y comenzar el día 1.")
        vistos.add(periodo_iso)
        cuota = disponibles.get(periodo_iso)
        if not cuota:
            raise ValueError(f"La cuota de {_etiqueta_periodo(periodo)} ya no está disponible.")

        monto = round(float(item.monto or 0), 2)
        saldo = round(float(cuota["saldo"] or 0), 2)
        if monto <= 0 or monto > saldo:
            raise ValueError(
                f"El valor para {_etiqueta_periodo(periodo)} debe ser mayor a cero "
                f"y no superar ${saldo:,.2f}."
            )
        normalizadas.append({
            "tipo_pago_id": tipo_pago_id,
            "periodo": periodo,
            "monto": monto,
            "etiqueta": _etiqueta_periodo(periodo),
        })

    total_aplicaciones = round(sum(item["monto"] for item in normalizadas), 2)
    total_pago = round(_calcular_total_pago(pago), 2)
    if total_aplicaciones != total_pago:
        raise ValueError("El total del pago debe coincidir con los meses seleccionados.")

    return {
        "concepto": opcion["concepto"],
        "items": normalizadas,
    }


def _insertar_aplicaciones_distribuidas(cursor, pagos_creados, aplicaciones):
    pendientes = [
        {**item, "centavos": int(round(float(item["monto"]) * 100))}
        for item in aplicaciones
    ]
    indice = 0
    for pago_id, monto_pago in pagos_creados:
        disponibles = int(round(float(monto_pago) * 100))
        while disponibles > 0 and indice < len(pendientes):
            aplicacion = pendientes[indice]
            usado = min(disponibles, aplicacion["centavos"])
            insertar_aplicacion(
                cursor,
                pago_id,
                aplicacion["estudiante_id"],
                aplicacion["tipo_pago_id"],
                aplicacion["periodo"],
                usado / 100,
            )
            disponibles -= usado
            aplicacion["centavos"] -= usado
            if aplicacion["centavos"] == 0:
                indice += 1

    if indice != len(pendientes):
        raise ValueError("No fue posible distribuir el pago entre los meses seleccionados.")


def registrar_pago_adelantado_controller(pago, hoy=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _exigir_tabla_pagos_aplicaciones(cursor)
        # Sin año, el adelanto es del año activo; con año, de ese año y con
        # sus conceptos (fase 2 del año lectivo).
        anio_lectivo_id = getattr(pago, "anio_lectivo_id", None)
        if anio_lectivo_id is not None:
            exigir_anio_lectivo(cursor, anio_lectivo_id)
        fecha_referencia = hoy or datetime.datetime.now(ZONA_HORARIA_LOCAL).date()
        conceptos = obtener_conceptos_mensuales_estudiante(
            cursor, pago.estudiante_id, **con_anio(anio_lectivo_id),
        )
        concepto = next((item for item in conceptos if item["id"] == pago.tipo_pago_id), None)
        if not concepto:
            raise ValueError("El concepto no es mensual o no está asignado al estudiante.")

        _bloquear_aplicaciones_concepto(cursor, pago.estudiante_id, concepto["id"])
        disponibles = _periodos_disponibles(cursor, pago.estudiante_id, concepto, fecha_referencia)
        monto_distribuir = getattr(pago, "monto_distribuir", None)
        if monto_distribuir is not None:
            periodos = _distribuir_monto_adelantado(disponibles, monto_distribuir)
        else:
            cantidad_meses = int(getattr(pago, "cantidad_meses", 0) or 0)
            if cantidad_meses > len(disponibles):
                raise ValueError("No hay suficientes meses disponibles para registrar este adelanto.")
            periodos = [
                {**item, "monto_aplicado": item["saldo"]}
                for item in disponibles[:cantidad_meses]
            ]

        total = round(sum(float(item["monto_aplicado"]) for item in periodos), 2)
        total_metodos = round(sum(float(metodo.monto or 0) for metodo in pago.metodos), 2)
        if total_metodos != total:
            raise ValueError(
                f"La suma de los métodos (${total_metodos:,.2f}) debe ser igual "
                f"al total del adelanto (${total:,.2f})."
            )

        etiquetas = [_etiqueta_periodo(item["periodo"]) for item in periodos]
        detalle_periodos = ", ".join(
            f"{etiqueta}: ${float(item['monto_aplicado']):,.2f}"
            for item, etiqueta in zip(periodos, etiquetas)
        )
        descripcion = f"{concepto['nombre']} · Pago adelantado: {detalle_periodos}"
        resumen_metodos = " + ".join(_formatear_tipo_pago(metodo) for metodo in pago.metodos)[:100]
        fecha_registro = _fecha_pago_local(getattr(pago, "fecha", None))

        pago_id = insertar_pago_adelantado(
            cursor,
            pago.estudiante_id,
            total,
            descripcion,
            fecha_registro,
            resumen_metodos,
            anio_lectivo_id=anio_lectivo_id,
        )

        for item in periodos:
            insertar_aplicacion(
                cursor,
                pago_id,
                pago.estudiante_id,
                concepto["id"],
                item["periodo"],
                item["monto_aplicado"],
            )

        conn.commit()
        return {
            "mensaje": "Pago adelantado registrado correctamente",
            "pago_id": pago_id,
            "monto": total,
            "descripcion": descripcion,
            "periodos": [
                {
                    "periodo": item["periodo"].isoformat(),
                    "etiqueta": etiqueta,
                    "monto_aplicado": item["monto_aplicado"],
                    "saldo_restante": round(item["saldo"] - item["monto_aplicado"], 2),
                }
                for item, etiqueta in zip(periodos, etiquetas)
            ],
        }
    except IntegrityError as exc:
        conn.rollback()
        raise ValueError("Uno de los meses seleccionados ya tiene un pago adelantado.") from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def _formatear_pago(row):
    fecha = row[3]
    estado = row[6] if len(row) > 6 and row[6] else "Pagado"
    return {
        "pago_id": row[0],
        "estudiante_id": row[1],
        "monto": float(row[2]),
        "fecha": fecha.strftime("%d/%m/%Y %I:%M %p") if fecha else "",
        "descripcion": row[4] if len(row) > 4 else '',
        "tipo_pago": row[5] if len(row) > 5 else None,
        "estado": estado,
        "anulado": str(estado).strip().lower() == "anulado",
        "motivo_anulacion": row[7] if len(row) > 7 else None,
        "fecha_anulacion": row[8].strftime("%d/%m/%Y %I:%M %p") if len(row) > 8 and row[8] else None,
        "anulado_por": row[9] if len(row) > 9 else None
    }


def _obtener_saldo_venta(cursor, venta_id):
    venta = leer_saldo_de_venta(cursor, venta_id)
    if not venta:
        raise ValueError("El cargo de inventario seleccionado no existe.")

    total, pagado, estado = venta
    saldo = max(0.0, float(total or 0) - float(pagado or 0))
    if estado != "Pendiente" or saldo <= 0:
        raise ValueError("Este cargo de inventario ya no tiene saldo pendiente.")
    return saldo


def _obtener_saldo_concepto(cursor, estudiante_id, concepto, anio_lectivo_id=None):
    return obtener_saldo_concepto(cursor, estudiante_id, concepto, **con_anio(anio_lectivo_id))


def _validar_pago_no_excede_deuda(cursor, pago):
    monto_total = _calcular_total_pago(pago)
    if monto_total <= 0:
        raise ValueError("El monto del pago debe ser mayor a cero.")

    if getattr(pago, 'venta_id', None):
        saldo = _obtener_saldo_venta(cursor, pago.venta_id)
        if monto_total > saldo:
            raise ValueError(
                f"El monto a pagar (${monto_total:,.2f}) no puede ser mayor al saldo pendiente (${saldo:,.2f})."
            )
        return

    # La deuda que se salda es la del año del pago (el activo si no se pide).
    saldo = _obtener_saldo_concepto(
        cursor,
        pago.estudiante_id,
        getattr(pago, 'descripcion', None),
        getattr(pago, 'anio_lectivo_id', None),
    )
    if monto_total > saldo:
        raise ValueError(
            f"El monto a pagar (${monto_total:,.2f}) no puede ser mayor a la deuda pendiente (${saldo:,.2f})."
        )


# 🎯 Registrar pago
def registrar_pago_controller(pago):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        _bloquear_registro_de_pagos(cursor, pago.estudiante_id)
        # Un pago se registra en el año de la deuda que salda, aunque ese año
        # este cerrado (decision 6 del año lectivo). Sin año, el activo.
        anio_lectivo_id = getattr(pago, "anio_lectivo_id", None)
        if anio_lectivo_id is not None:
            exigir_anio_lectivo(cursor, anio_lectivo_id)
        aplicaciones_preparadas = _preparar_aplicaciones_pago(cursor, pago)
        _validar_pago_no_excede_deuda(cursor, pago)
        fecha_registro = _fecha_pago_local(getattr(pago, "fecha", None))
        descripcion_registro = getattr(pago, "descripcion", "")
        if aplicaciones_preparadas:
            etiquetas = ", ".join(item["etiqueta"] for item in aplicaciones_preparadas["items"])
            descripcion_registro = f"{aplicaciones_preparadas['concepto']} · Cuotas: {etiquetas}"

        pago_ids = []
        pagos_creados = []
        metodos = getattr(pago, 'metodos', None)
        if metodos and isinstance(metodos, list) and len(metodos) > 0:
            for metodo in metodos:
                pago_id = insertar_pago(
                    cursor,
                    pago.estudiante_id,
                    getattr(pago, 'venta_id', None),
                    metodo.monto,
                    descripcion_registro,
                    fecha_registro,
                    _formatear_tipo_pago(metodo),
                    anio_lectivo_id=anio_lectivo_id,
                )
                pago_ids.append(pago_id)
                pagos_creados.append((pago_id, float(metodo.monto or 0)))

                # Si se envía un venta_id, acumular abono a la venta (cargo de inventario)
                if getattr(pago, 'venta_id', None):
                    venta = abonar_a_venta(cursor, metodo.monto, pago.venta_id)
                    if venta:
                        total_venta, total_pagado = venta
                        if total_pagado >= total_venta:
                            marcar_venta_pagada(cursor, pago.venta_id)
        else:
            # Caso compatibilidad: pago simple
            pago_id = insertar_pago(
                cursor,
                pago.estudiante_id,
                getattr(pago, 'venta_id', None),
                pago.monto,
                descripcion_registro,
                fecha_registro,
                getattr(pago, 'tipo_pago', None),
                anio_lectivo_id=anio_lectivo_id,
            )
            pago_ids.append(pago_id)
            pagos_creados.append((pago_id, float(pago.monto or 0)))

            if getattr(pago, 'venta_id', None):
                venta = abonar_a_venta(cursor, pago.monto, pago.venta_id)
                if venta:
                    total_venta, total_pagado = venta
                    if total_pagado >= total_venta:
                        marcar_venta_pagada(cursor, pago.venta_id)

        if aplicaciones_preparadas:
            aplicaciones_con_estudiante = [
                {**item, "estudiante_id": pago.estudiante_id}
                for item in aplicaciones_preparadas["items"]
            ]
            _insertar_aplicaciones_distribuidas(
                cursor,
                pagos_creados,
                aplicaciones_con_estudiante,
            )

        conn.commit()
        return pago_ids[0] if len(pago_ids) == 1 else pago_ids

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


# 🎯 Historial de pagos por estudiante
def historial_pagos_controller(estudiante_id):

    with get_cursor() as cursor:
        resultado = listar_pagos_de_estudiante(cursor, estudiante_id)

    return [_formatear_pago(row) for row in resultado]


def historial_pagos_paginado_controller(estudiante_id, limit=50, offset=0):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        total = contar_pagos_de_estudiante(cursor, estudiante_id)
        resultado = listar_pagos_de_estudiante_paginado(
            cursor, estudiante_id, limit, offset
        )

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [_formatear_pago(row) for row in resultado]
        }
    finally:
        cursor.close()
        conn.close()


def anular_pago_controller(pago_id, motivo, admin_id):
    motivo_limpio = str(motivo or "").strip()
    if len(motivo_limpio) < 5:
        raise ValueError("Debes escribir un motivo de anulación de al menos 5 caracteres.")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        pago = leer_pago_para_anular(cursor, pago_id)

        if not pago:
            raise ValueError("El pago no existe.")

        if str(pago[1]).strip().lower() == "anulado":
            raise ValueError("Este pago ya está anulado.")

        monto_pago = float(pago[2] or 0)
        venta_id = pago[3]
        descripcion = pago[4] or ""

        if venta_id is None:
            match = VENTA_ID_PATTERN.search(descripcion)
            if match:
                venta_id = int(match.group(1))
                asignar_venta_a_pago(cursor, venta_id, pago_id)

        if venta_id is not None:
            venta = leer_venta_para_anular(cursor, venta_id)
            if not venta:
                raise ValueError("La venta asociada a este pago ya no existe.")

            total_venta = float(venta[1] or 0)
            pagado_actual = float(venta[2] or 0)
            nuevo_pagado = max(0.0, pagado_actual - monto_pago)
            nuevo_estado = "Pagado" if nuevo_pagado >= total_venta and total_venta > 0 else "Pendiente"

            ajustar_venta_tras_anulacion(
                cursor, nuevo_pagado, nuevo_estado, venta_id
            )

        if _tabla_pagos_aplicaciones_existe(cursor):
            desactivar_aplicaciones_de_pago(cursor, pago_id)

        marcar_pago_anulado(
            cursor,
            motivo_limpio,
            datetime.datetime.now(ZONA_HORARIA_LOCAL).replace(tzinfo=None),
            admin_id,
            pago_id,
        )

        conn.commit()
        return {"mensaje": "Pago anulado correctamente", "pago_id": pago_id}
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
