from app.services.cobros import calcular_deudas_desde_contexto


def construir_estado_cuenta_curso(
    *,
    estudiantes,
    tipos_pago,
    asignaciones_curso,
    pagos_concepto_rows,
    pagos_nombre_rows,
    pagos_aplicados_por_estudiante,
    valores_por_estudiante,
    pagos_otros_rows,
):
    """Construye el payload financiero con datos ya precargados."""
    pagos_por_concepto = {}
    for estudiante_id, concepto_id, monto in pagos_concepto_rows:
        pagos_por_concepto.setdefault(estudiante_id, {})[concepto_id] = float(monto)

    pagos_por_nombre = {}
    for estudiante_id, tipo_pago, monto in pagos_nombre_rows:
        if tipo_pago:
            pagos_por_nombre.setdefault(estudiante_id, {})[
                str(tipo_pago).lower()
            ] = float(monto)

    pagos_otros_por_estudiante = {
        estudiante_id: float(monto) if monto else 0.0
        for estudiante_id, monto in pagos_otros_rows
    }

    resultados = []
    for estudiante_id, nombre, apellido in estudiantes:
        pagos_dict = pagos_por_concepto.get(estudiante_id, {})
        pagos_nombre_estudiante = dict(pagos_por_nombre.get(estudiante_id, {}))
        for tipo in tipos_pago:
            nombre_tipo = str(tipo["nombre"]).lower()
            if nombre_tipo not in pagos_nombre_estudiante and tipo["id"] in pagos_dict:
                pagos_nombre_estudiante[nombre_tipo] = pagos_dict[tipo["id"]]

        resumen = calcular_deudas_desde_contexto(
            tipos_pago=tipos_pago,
            asignaciones_curso=asignaciones_curso,
            pagos_nombre=pagos_nombre_estudiante,
            pagos_descripcion={},
            pagos_aplicados=pagos_aplicados_por_estudiante.get(estudiante_id, {}),
            valores_estudiante=valores_por_estudiante.get(estudiante_id, {}),
        )

        deudas_detalle = []
        total_adeudado = 0.0
        total_pagado_general = 0.0
        for deuda in resumen["deudas"]:
            pagado = deuda["pagado"]
            total_adeudado += deuda["deuda"]
            total_pagado_general += pagado
            deudas_detalle.append(
                {
                    "concepto": deuda["concepto"],
                    "valor_total": deuda["valor_total"],
                    "pagado": pagado,
                    "deuda": deuda["deuda"],
                    "mora": deuda["mora"],
                    "cuotas_vencidas": deuda["cuotas_vencidas"],
                }
            )

        pagos_otros = pagos_otros_por_estudiante.get(estudiante_id, 0.0)
        if pagos_otros > 0:
            total_pagado_general += pagos_otros
            deudas_detalle.append(
                {
                    "concepto": "Otros Pagos",
                    "valor_total": 0,
                    "pagado": pagos_otros,
                    "deuda": -pagos_otros,
                }
            )

        resultados.append(
            {
                "id": estudiante_id,
                "nombre": nombre,
                "apellido": apellido,
                "pagado": float(total_pagado_general),
                "total": float(total_adeudado + total_pagado_general),
                "deuda": float(total_adeudado),
                "deudas_detalle": deudas_detalle,
            }
        )

    return resultados
