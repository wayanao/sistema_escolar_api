"""Años lectivos: consulta, preparación y matrícula del año siguiente.

Ver docs/funcionalidades/ANIO_LECTIVO.md (fase 3, paso 3.1; fase 5, pasos
5.3 a 5.5, y fase 6, pasos 6.2a, 6.2b y 6.3a). Qué años ve cada usuario lo
decide `app/services/anio_lectivo.py`.
"""
from app.controllers.estudiante_controller import (
    guardar_sisben_y_residencia_si_llegaron,
)
from app.database import get_cursor
from app.repositories import anios_lectivos_repository, estudiantes_repository
from app.services.anio_lectivo import (
    AnioLectivoInexistenteError,
    listar_anios_visibles,
)
from psycopg2 import IntegrityError


class AnioLectivoEnPreparacionError(Exception):
    """Ya existe el único año que se puede preparar a la vez."""


class AnioLectivoActivoInexistenteError(Exception):
    """No hay año activo desde el cual calcular exactamente N+1."""


class AnioLectivoSiguienteExistenteError(Exception):
    """El N+1 calculado ya existe y no se puede duplicar."""


class AnioLectivoDestinoInvalidoError(Exception):
    """El destino no es el N+1 que está en preparación."""


class ConfiguracionAnioDuplicadaError(Exception):
    """Un curso o concepto del origen ya existe en el destino."""


class ConfiguracionAnioInconsistenteError(Exception):
    """Una referencia del origen no pudo reconstruirse en el destino."""


class CursoMatriculaInvalidoError(Exception):
    """Un curso no pertenece al año que corresponde a la matrícula."""


class CandidatosMatriculaInvalidosError(Exception):
    """La selección contiene estudiantes ajenos o ya matriculados."""


class ValoresEspecialesInconsistentesError(Exception):
    """Un valor especial no tiene concepto equivalente en el destino."""


class ConfirmacionAnioInvalidaError(Exception):
    """El año escrito para confirmar no es el que se activa, reabre o cierra."""


class AnioLectivoReabiertoExistenteError(Exception):
    """Ya hay un año reabierto; solo se permite uno a la vez (fase 6.4a)."""


class ActivacionConPendientesError(Exception):
    """Quedan estudiantes sin decidir (decisión 9); viajan con la lista."""

    codigo = "activacion_con_pendientes"

    def __init__(self, mensaje, sin_decidir):
        super().__init__(mensaje)
        self.sin_decidir = sin_decidir


class ActivacionInconsistenteError(Exception):
    """Una comprobación final falló; la transacción se deshace entera."""


class EstudianteNoReingresableError(Exception):
    """Quien ya es estudiante no puede matricularse así desde una admisión."""


class AltaDirectaCerradaError(Exception):
    """El alta directa en el año en preparación quedó cerrada (paso E7)."""


def _formatear_anio(row):
    return {
        "id": row[0],
        "anio": row[1],
        "estado": row[2],
    }


def listar_anios_lectivos_controller(usuario):
    with get_cursor() as cursor:
        filas = listar_anios_visibles(cursor, usuario)
    return [_formatear_anio(row) for row in filas]


def crear_anio_lectivo_controller():
    """Crea exactamente el año posterior al activo, en preparación."""
    with get_cursor(commit=True) as cursor:
        activo = anios_lectivos_repository.leer_anio_activo_para_actualizar(cursor)
        if activo is None:
            raise AnioLectivoActivoInexistenteError(
                "No hay un año lectivo activo para calcular el siguiente."
            )

        if anios_lectivos_repository.leer_anio_en_preparacion(cursor) is not None:
            raise AnioLectivoEnPreparacionError(
                "Ya hay un año lectivo en preparación."
            )

        siguiente = activo[1] + 1
        creado = anios_lectivos_repository.crear_anio_en_preparacion(
            cursor, siguiente
        )
        if creado is None:
            raise AnioLectivoSiguienteExistenteError(
                f"El año lectivo {siguiente} ya existe o está en preparación."
            )

    return _formatear_anio(creado)


def _validar_destino_de_copia(activo, destino):
    if destino[2] != "preparacion":
        raise AnioLectivoDestinoInvalidoError(
            "La configuración solo se puede copiar a un año en preparación."
        )
    esperado = activo[1] + 1
    if destino[1] != esperado:
        raise AnioLectivoDestinoInvalidoError(
            f"El destino debe ser el año lectivo {esperado}."
        )


def _copiar_cursos(cursor, cursos, anio_destino_id, copiar_directores):
    mapa = {}
    directores = 0
    for curso in cursos:
        try:
            nuevo_id = anios_lectivos_repository.insertar_curso_copiado(
                cursor, curso, anio_destino_id, copiar_directores
            )
        except IntegrityError as exc:
            raise ConfiguracionAnioDuplicadaError(
                f"Ya existe el curso '{curso['nombre']}' de jornada "
                f"'{curso['jornada']}' en el año destino."
            ) from exc
        mapa[curso["id"]] = nuevo_id
        if copiar_directores and curso["director_grupo_id"] is not None:
            directores += 1
    return mapa, directores


def _copiar_conceptos(cursor, conceptos, anio_destino_id):
    mapa = {}
    for concepto in conceptos:
        try:
            nuevo_id = anios_lectivos_repository.insertar_concepto_copiado(
                cursor, concepto, anio_destino_id
            )
        except IntegrityError as exc:
            raise ConfiguracionAnioDuplicadaError(
                f"Ya existe el concepto de pago '{concepto['nombre']}' "
                "en el año destino."
            ) from exc
        mapa[concepto["id"]] = nuevo_id
    return mapa


def _copiar_precios(cursor, anio_origen_id, cursos, conceptos):
    copiados = 0
    for precio in anios_lectivos_repository.listar_precios_para_copiar(
        cursor, anio_origen_id
    ):
        curso_id = cursos.get(precio["curso_id"])
        tipo_pago_id = conceptos.get(precio["tipo_pago_id"])
        if curso_id is None or tipo_pago_id is None:
            raise ConfiguracionAnioInconsistenteError(
                "Un precio del año de origen no tiene curso o concepto copiado."
            )
        try:
            anios_lectivos_repository.insertar_precio_copiado(
                cursor, precio, tipo_pago_id, curso_id
            )
        except IntegrityError as exc:
            raise ConfiguracionAnioInconsistenteError(
                "No se pudo copiar un precio por curso del año de origen."
            ) from exc
        copiados += 1
    return copiados


def _copiar_asignaciones(cursor, anio_origen_id, cursos):
    asignaciones = anios_lectivos_repository.listar_asignaciones_para_copiar(
        cursor, anio_origen_id
    )
    mapa = {}
    for asignacion in asignaciones:
        curso_id = cursos.get(asignacion["curso_id"])
        if curso_id is None:
            raise ConfiguracionAnioInconsistenteError(
                f"La asignación {asignacion['id']} no tiene un curso copiado."
            )
        try:
            nuevo_id = anios_lectivos_repository.insertar_asignacion_copiada(
                cursor, asignacion, curso_id
            )
        except IntegrityError as exc:
            raise ConfiguracionAnioInconsistenteError(
                f"No se pudo copiar la asignación {asignacion['id']}."
            ) from exc
        mapa[asignacion["id"]] = nuevo_id

    for asignacion in asignaciones:
        cabecera_origen = (
            asignacion["asignacion_academica_id"] or asignacion["id"]
        )
        cabecera_nueva = mapa.get(cabecera_origen)
        if cabecera_nueva is None:
            raise ConfiguracionAnioInconsistenteError(
                f"La asignación {asignacion['id']} apunta a una cabecera "
                "que no pertenece a la copia."
            )
        anios_lectivos_repository.enlazar_asignacion_academica_copiada(
            cursor, mapa[asignacion["id"]], cabecera_nueva
        )
    return len(mapa)


def copiar_configuracion_anio_controller(anio_destino_id, opciones):
    """Copia cursos y conceptos del activo; los extras dependen del cuerpo."""
    with get_cursor(commit=True) as cursor:
        activo = anios_lectivos_repository.leer_anio_activo_para_actualizar(cursor)
        if activo is None:
            raise AnioLectivoActivoInexistenteError(
                "No hay un año lectivo activo para copiar."
            )

        destino = anios_lectivos_repository.leer_anio_lectivo_para_actualizar(
            cursor, anio_destino_id
        )
        if destino is None:
            raise AnioLectivoInexistenteError(
                "El año lectivo seleccionado no existe."
            )
        _validar_destino_de_copia(activo, destino)

        choque_curso = anios_lectivos_repository.buscar_choque_curso_para_copia(
            cursor, activo[0], destino[0]
        )
        if choque_curso is not None:
            raise ConfiguracionAnioDuplicadaError(
                f"Ya existe el curso '{choque_curso[0]}' de jornada "
                f"'{choque_curso[1]}' en {destino[1]}."
            )

        choque_concepto = (
            anios_lectivos_repository.buscar_choque_concepto_para_copia(
                cursor, activo[0], destino[0]
            )
        )
        if choque_concepto is not None:
            raise ConfiguracionAnioDuplicadaError(
                f"Ya existe el concepto de pago '{choque_concepto[0]}' "
                f"en {destino[1]}."
            )

        cursos_origen = anios_lectivos_repository.listar_cursos_para_copiar(
            cursor, activo[0]
        )
        cursos, directores = _copiar_cursos(
            cursor,
            cursos_origen,
            destino[0],
            opciones.copiar_directores,
        )

        conceptos_origen = (
            anios_lectivos_repository.listar_conceptos_para_copiar(
                cursor, activo[0]
            )
        )
        conceptos = _copiar_conceptos(cursor, conceptos_origen, destino[0])

        precios = 0
        if opciones.copiar_precios:
            precios = _copiar_precios(cursor, activo[0], cursos, conceptos)

        asignaciones = 0
        if opciones.copiar_carga_academica:
            asignaciones = _copiar_asignaciones(cursor, activo[0], cursos)

    return {
        "anio_origen_id": activo[0],
        "anio_origen": activo[1],
        "anio_destino_id": destino[0],
        "anio_destino": destino[1],
        "copiados": {
            "cursos": len(cursos),
            "conceptos_pago": len(conceptos),
            "precios_curso": precios,
            "asignaciones": asignaciones,
            "directores_grupo": directores,
        },
    }


def _contexto_matricula_en_preparacion(cursor, anio_destino_id):
    activo = anios_lectivos_repository.leer_anio_activo_para_actualizar(cursor)
    if activo is None:
        raise AnioLectivoActivoInexistenteError(
            "No hay un año lectivo activo desde el cual matricular."
        )

    destino = anios_lectivos_repository.leer_anio_lectivo_para_actualizar(
        cursor, anio_destino_id
    )
    if destino is None:
        raise AnioLectivoInexistenteError(
            "El año lectivo seleccionado no existe."
        )
    if destino[2] != "preparacion":
        raise AnioLectivoDestinoInvalidoError(
            "Solo se puede matricular en un año en preparación."
        )
    if destino[1] != activo[1] + 1:
        raise AnioLectivoDestinoInvalidoError(
            f"El destino de la matrícula debe ser el año lectivo {activo[1] + 1}."
        )
    return activo, destino


def resumen_anio_preparacion_controller(anio_destino_id):
    """Resume lo preparado y el dinero registrado para el siguiente año."""
    with get_cursor() as cursor:
        _activo, destino = _contexto_matricula_en_preparacion(
            cursor, anio_destino_id
        )
        resumen = anios_lectivos_repository.leer_resumen_anio(
            cursor, destino[0]
        )

    return {
        "anio_lectivo": {
            "id": destino[0],
            "anio": destino[1],
            "estado": destino[2],
        },
        "resumen": {
            "cursos": resumen["cursos"],
            "conceptos_pago": resumen["conceptos_pago"],
            "estudiantes_matriculados": resumen["estudiantes_matriculados"],
            "valores_especiales": resumen["valores_especiales"],
            "pagos_registrados": resumen["pagos_registrados"],
            "total_pagado": float(resumen["total_pagado"] or 0),
        },
    }


def _contexto_activacion(cursor, anio_destino_id, bloquear=False):
    """Año activo y el siguiente en preparación.

    La vista previa los lee sin bloquear. La activación los bloquea, en el
    mismo orden que la promoción y la marca de salida, para que ninguna de las
    dos cambie la lista de pendientes mientras se activa.
    """
    repositorio = anios_lectivos_repository
    if bloquear:
        leer_activo = repositorio.leer_anio_activo_para_actualizar
        leer_destino = repositorio.leer_anio_lectivo_para_actualizar
    else:
        leer_activo = repositorio.leer_anio_activo
        leer_destino = repositorio.leer_anio_lectivo

    activo = leer_activo(cursor)
    if activo is None:
        raise AnioLectivoActivoInexistenteError(
            "No hay un año lectivo activo para cerrar."
        )

    destino = leer_destino(cursor, anio_destino_id)
    if destino is None:
        raise AnioLectivoInexistenteError(
            "El año lectivo seleccionado no existe."
        )
    if destino[2] != "preparacion":
        raise AnioLectivoDestinoInvalidoError(
            "Solo se puede activar un año en preparación."
        )
    if destino[1] != activo[1] + 1:
        raise AnioLectivoDestinoInvalidoError(
            f"El año que se activa debe ser el {activo[1] + 1}."
        )
    return activo, destino


def vista_previa_activacion_controller(anio_destino_id):
    """Cuenta quién sigue y quién sale, y lista quién falta por decidir.

    Solo lee (fase 6, paso 6.2a). Con alguien sin decidir no se puede activar
    (decisión 9); lo dice el backend para que el frontend no lo calcule.
    """
    with get_cursor() as cursor:
        activo, destino = _contexto_activacion(cursor, anio_destino_id)
        conteos = anios_lectivos_repository.contar_decisiones_activacion(
            cursor, activo[0], destino[0]
        )
        pendientes = anios_lectivos_repository.listar_sin_decidir_activacion(
            cursor, activo[0], destino[0]
        )

    return {
        "anio_origen": {"id": activo[0], "anio": activo[1]},
        "anio_destino": {"id": destino[0], "anio": destino[1]},
        "resumen": {
            "continuan": conteos["continuan"],
            "nuevos": conteos["nuevos"],
            "retirados": conteos["retirados"],
            "egresados": conteos["egresados"],
            "sin_decidir": len(pendientes),
        },
        "puede_activar": not pendientes,
        "sin_decidir": pendientes,
    }


def activar_anio_controller(anio_destino_id, datos):
    """Cierra el año activo y activa el siguiente, todo o nada (fase 6.3a).

    Vuelve a revisar los pendientes con los dos años bloqueados, guarda la
    foto de materias ocultas del año que cierra, aplica las marcas de salida,
    cambia los estados y copia a cada estudiante el curso del año nuevo. Al
    final corre la consulta de control: si no da 0, se deshace todo.
    """
    with get_cursor(commit=True) as cursor:
        activo, destino = _contexto_activacion(
            cursor, anio_destino_id, bloquear=True
        )
        if datos.confirmar_anio != destino[1]:
            raise ConfirmacionAnioInvalidaError(
                f"Para activar, escribe el año {destino[1]}."
            )

        pendientes = anios_lectivos_repository.listar_sin_decidir_activacion(
            cursor, activo[0], destino[0]
        )
        if pendientes:
            raise ActivacionConPendientesError(
                f"No se puede activar {destino[1]}: faltan {len(pendientes)} "
                "estudiantes por decidir.",
                pendientes,
            )

        conteos = anios_lectivos_repository.contar_decisiones_activacion(
            cursor, activo[0], destino[0]
        )
        materias_ocultas = anios_lectivos_repository.guardar_materias_ocultas(
            cursor, activo[0]
        )
        anios_lectivos_repository.aplicar_marcas_de_salida(
            cursor, activo[0], destino[0]
        )
        cambios = anios_lectivos_repository.activar_anio_siguiente(
            cursor, activo[0], destino[0]
        )
        if tuple(cambios) != (1, 1):
            raise ActivacionInconsistenteError(
                "No se pudo cambiar el estado de los dos años. Nada cambió."
            )
        actualizados = anios_lectivos_repository.sincronizar_curso_vigente_de_todos(
            cursor
        )
        if anios_lectivos_repository.contar_desajustes_curso_vigente(cursor):
            raise ActivacionInconsistenteError(
                "El curso vigente de algunos estudiantes no coincide con su "
                "matrícula del año nuevo. Nada cambió."
            )

    return {
        "anio_cerrado": {"id": activo[0], "anio": activo[1], "estado": "cerrado"},
        "anio_activo": {"id": destino[0], "anio": destino[1], "estado": "activo"},
        "resumen": {
            "continuan": conteos["continuan"],
            "nuevos": conteos["nuevos"],
            "retirados": conteos["retirados"],
            "egresados": conteos["egresados"],
            "materias_ocultas": materias_ocultas,
            "cursos_vigentes_actualizados": actualizados,
        },
    }


def _cambiar_estado_anio_pasado(
    anio_lectivo_id, datos, estado_actual, estado_nuevo, accion, rechazo
):
    """Reabre o vuelve a cerrar un año pasado; solo cambia su estado.

    Bloquea primero el año activo, que hace de turno para todo cambio de
    estado de los años, y después el año pedido. No toca estudiantes, cursos,
    la foto de materias ni las fechas de activación y cierre.
    """
    with get_cursor(commit=True) as cursor:
        repositorio = anios_lectivos_repository
        if repositorio.leer_anio_activo_para_actualizar(cursor) is None:
            raise AnioLectivoActivoInexistenteError("No hay un año lectivo activo.")

        anio = repositorio.leer_anio_lectivo_para_actualizar(cursor, anio_lectivo_id)
        if anio is None:
            raise AnioLectivoInexistenteError("El año lectivo seleccionado no existe.")
        if anio[2] != estado_actual:
            raise AnioLectivoDestinoInvalidoError(rechazo)
        if datos.confirmar_anio != anio[1]:
            raise ConfirmacionAnioInvalidaError(
                f"Para {accion}, escribe el año {anio[1]}."
            )

        if estado_nuevo == "reabierto":
            otro = repositorio.leer_anio_reabierto(cursor)
            if otro is not None:
                raise AnioLectivoReabiertoExistenteError(
                    f"Ya está reabierto el año {otro[1]}. "
                    "Ciérralo antes de reabrir otro."
                )

        cambiadas = repositorio.cambiar_estado_anio(
            cursor, anio[0], estado_actual, estado_nuevo
        )
        if cambiadas != 1:
            raise AnioLectivoDestinoInvalidoError(
                "El año cambió de estado mientras se guardaba. Nada cambió."
            )

    return {"anio_lectivo": {"id": anio[0], "anio": anio[1], "estado": estado_nuevo}}


def reabrir_anio_controller(anio_lectivo_id, datos):
    """Abre un año cerrado para correcciones del admin (fase 6.4a)."""
    return _cambiar_estado_anio_pasado(
        anio_lectivo_id,
        datos,
        "cerrado",
        "reabierto",
        "reabrir",
        "Solo se puede reabrir un año cerrado.",
    )


def cerrar_anio_reabierto_controller(anio_lectivo_id, datos):
    """Vuelve a cerrar un año reabierto (fase 6.4a)."""
    return _cambiar_estado_anio_pasado(
        anio_lectivo_id,
        datos,
        "reabierto",
        "cerrado",
        "cerrar",
        "Solo se puede volver a cerrar un año reabierto.",
    )


def _exigir_curso_del_anio(
    cursor, curso_id, anio_lectivo_id, nombre_curso, nombre_anio
):
    curso = anios_lectivos_repository.leer_curso_para_matricula(cursor, curso_id)
    if curso is None or curso["anio_lectivo_id"] != anio_lectivo_id:
        raise CursoMatriculaInvalidoError(
            f"El curso {nombre_curso} debe pertenecer al {nombre_anio}."
        )
    return curso


def _formatear_candidato(candidato):
    return {
        "id": candidato["id"],
        "nombre": candidato["nombre"],
        "apellido": candidato["apellido"],
        "documento_identidad": candidato["documento_identidad"],
        "estado": candidato["estado"],
        "matriculado_en_destino": candidato["curso_destino_id"] is not None,
        "curso_destino_id": candidato["curso_destino_id"],
        # Fase 6.5: la pantalla de promoción muestra y quita la marca.
        "estado_salida": candidato.get("estado_salida"),
    }


def listar_candidatos_matricula_controller(anio_destino_id, curso_origen_id):
    """Lista el curso activo completo para que el admin elija a quién promover."""
    with get_cursor() as cursor:
        activo, destino = _contexto_matricula_en_preparacion(
            cursor, anio_destino_id
        )
        curso = _exigir_curso_del_anio(
            cursor, curso_origen_id, activo[0], "de origen", "año activo"
        )
        candidatos = anios_lectivos_repository.listar_candidatos_matricula(
            cursor, curso_origen_id, activo[0], destino[0]
        )

    return {
        "anio_origen": {"id": activo[0], "anio": activo[1]},
        "anio_destino": {"id": destino[0], "anio": destino[1]},
        "curso_origen": {
            "id": curso["id"],
            "nombre": curso["nombre"],
            "jornada": curso["jornada"],
        },
        "candidatos": [_formatear_candidato(fila) for fila in candidatos],
    }


def _exigir_seleccion_disponible(candidatos, estudiante_ids):
    por_id = {fila["id"]: fila for fila in candidatos}
    ajenos = [estudiante_id for estudiante_id in estudiante_ids if estudiante_id not in por_id]
    if ajenos:
        raise CandidatosMatriculaInvalidosError(
            "Los estudiantes "
            f"{', '.join(map(str, ajenos))} no pertenecen al curso de origen."
        )

    matriculados = [
        estudiante_id
        for estudiante_id in estudiante_ids
        if por_id[estudiante_id]["curso_destino_id"] is not None
    ]
    if matriculados:
        raise CandidatosMatriculaInvalidosError(
            "Los estudiantes "
            f"{', '.join(map(str, matriculados))} ya tienen matrícula en el año destino."
        )

    # Fase 6.2b: una marca de salida y una matrícula siguiente se excluyen.
    marcados = [
        estudiante_id
        for estudiante_id in estudiante_ids
        if por_id[estudiante_id].get("estado_salida")
    ]
    if marcados:
        raise CandidatosMatriculaInvalidosError(
            "Los estudiantes "
            f"{', '.join(map(str, marcados))} están marcados como que no siguen. "
            "Quita la marca antes de matricularlos."
        )


def _copiar_valores_especiales(cursor, estudiante_id, activo_id, destino_id):
    valores = anios_lectivos_repository.listar_valores_especiales_para_copiar(
        cursor, estudiante_id, activo_id, destino_id
    )
    sin_equivalente = [
        valor for valor in valores if valor["tipo_pago_destino_id"] is None
    ]
    if sin_equivalente:
        nombres = ", ".join(
            valor["tipo_pago_origen_nombre"] for valor in sin_equivalente
        )
        raise ValoresEspecialesInconsistentesError(
            f"No existe en el año destino una copia de: {nombres}."
        )

    copiados = []
    for valor in valores:
        valor_id = anios_lectivos_repository.insertar_valor_especial_copiado(
            cursor, estudiante_id, valor
        )
        copiados.append(
            {
                "id": valor_id,
                "estudiante_id": estudiante_id,
                "tipo_pago_origen_id": valor["tipo_pago_origen_id"],
                "tipo_pago_id": valor["tipo_pago_destino_id"],
                "tipo_pago_nombre": valor["tipo_pago_destino_nombre"],
                "valor": float(valor["valor"] or 0),
                "motivo": valor["motivo"] or "",
                "activo": valor["activo"],
                "estado": "revisar",
            }
        )
    return copiados


def promover_estudiantes_controller(anio_destino_id, datos):
    """Matricula solo la selección y copia sus valores especiales."""
    with get_cursor(commit=True) as cursor:
        activo, destino = _contexto_matricula_en_preparacion(
            cursor, anio_destino_id
        )
        _exigir_curso_del_anio(
            cursor,
            datos.curso_origen_id,
            activo[0],
            "de origen",
            "año activo",
        )
        _exigir_curso_del_anio(
            cursor,
            datos.curso_destino_id,
            destino[0],
            "de destino",
            "año en preparación",
        )
        candidatos = anios_lectivos_repository.listar_candidatos_matricula(
            cursor, datos.curso_origen_id, activo[0], destino[0]
        )
        _exigir_seleccion_disponible(candidatos, datos.estudiante_ids)

        valores_copiados = []
        try:
            for estudiante_id in datos.estudiante_ids:
                anios_lectivos_repository.insertar_matricula_en_anio(
                    cursor, estudiante_id, datos.curso_destino_id, destino[0]
                )
                valores_copiados.extend(
                    _copiar_valores_especiales(
                        cursor, estudiante_id, activo[0], destino[0]
                    )
                )
        except IntegrityError as exc:
            raise CandidatosMatriculaInvalidosError(
                "Uno de los estudiantes ya tiene matrícula o valores especiales "
                "en el año destino."
            ) from exc

    return {
        "anio_lectivo_id": destino[0],
        "curso_origen_id": datos.curso_origen_id,
        "curso_destino_id": datos.curso_destino_id,
        "matriculados": datos.estudiante_ids,
        "cantidad_matriculados": len(datos.estudiante_ids),
        "valores_especiales_copiados": valores_copiados,
    }


def _exigir_salida_posible(matriculas, datos, activo, destino):
    por_id = {fila["estudiante_id"]: fila for fila in matriculas}
    sin_matricula = [
        estudiante_id
        for estudiante_id in datos.estudiante_ids
        if estudiante_id not in por_id
    ]
    if sin_matricula:
        raise CandidatosMatriculaInvalidosError(
            "Los estudiantes "
            f"{', '.join(map(str, sin_matricula))} no tienen matrícula en el año "
            f"lectivo {activo[1]}."
        )

    # Quitar la marca siempre se permite: deshace un choque, nunca lo crea.
    if datos.estado_salida is None:
        return
    matriculados = [
        estudiante_id
        for estudiante_id in datos.estudiante_ids
        if por_id[estudiante_id]["matriculado_en_destino"]
    ]
    if matriculados:
        raise CandidatosMatriculaInvalidosError(
            "Los estudiantes "
            f"{', '.join(map(str, matriculados))} ya tienen matrícula en "
            f"{destino[1]}; no se pueden marcar como que no siguen."
        )


def guardar_decision_salida_controller(anio_destino_id, datos):
    """Marca o desmarca quién no sigue en el año siguiente (fase 6.2b).

    La marca va en la matrícula del año activo. Bloquea los dos años igual que
    la promoción, para que marcar y matricular no se crucen.
    """
    with get_cursor(commit=True) as cursor:
        activo, destino = _contexto_matricula_en_preparacion(
            cursor, anio_destino_id
        )
        matriculas = anios_lectivos_repository.listar_matriculas_para_salida(
            cursor, datos.estudiante_ids, activo[0], destino[0]
        )
        _exigir_salida_posible(matriculas, datos, activo, destino)
        anios_lectivos_repository.guardar_estado_salida(
            cursor, datos.estudiante_ids, activo[0], datos.estado_salida
        )

    return {
        "anio_origen": {"id": activo[0], "anio": activo[1]},
        "anio_destino": {"id": destino[0], "anio": destino[1]},
        "estado_salida": datos.estado_salida,
        "estudiante_ids": datos.estudiante_ids,
        "cantidad": len(datos.estudiante_ids),
    }


def _valores_globales_estudiante(est):
    estado = str(est.estado or "activo").strip().lower()
    return (
        est.nombre,
        est.apellido,
        est.documento_identidad,
        est.fecha_nacimiento,
        est.descuento_matricula,
        est.descuento_mensualidad,
        est.datos_medicos,
        est.telefono,
        est.email,
        est.direccion,
        est.nombre_padre,
        est.telefono_padre,
        est.nombre_madre,
        est.telefono_madre,
        est.contacto_emergencia,
        est.tipo_documento,
        est.lugar_expedicion,
        est.eps,
        est.estrato,
        est.jornada,
        est.colegio_anterior,
        est.anio_cursado_anterior,
        est.pre_escolar_anterior,
        est.ebp_anterior,
        est.motivo_retiro_anterior,
        est.paz_salvo_anterior,
        est.ocupacion_padre,
        est.tipo_documento_padre,
        est.documento_padre,
        est.ocupacion_madre,
        est.tipo_documento_madre,
        est.documento_madre,
        est.condicion_diagnostico,
        estado,
    )


def _crear_estudiante_en_preparacion(cursor, destino, est):
    """Ficha nueva y solo su matrícula del año en preparación: `(id, matrícula)`.

    La usan el alta directa (paso 5.5) y la matrícula desde una admisión
    (entrevista de admisión, paso E3), cada una en su transacción.
    """
    _exigir_curso_del_anio(
        cursor,
        est.curso_id,
        destino[0],
        "seleccionado",
        "año en preparación",
    )
    estudiante_id = estudiantes_repository.insertar_estudiante(
        cursor, _valores_globales_estudiante(est)
    )
    guardar_sisben_y_residencia_si_llegaron(cursor, estudiante_id, est)
    matricula_id = anios_lectivos_repository.insertar_matricula_en_anio(
        cursor, estudiante_id, est.curso_id, destino[0]
    )
    # Al no tener matrícula activa, esta sincronización conserva NULL.
    anios_lectivos_repository.sincronizar_curso_vigente(
        cursor, estudiante_id
    )
    return estudiante_id, matricula_id


def crear_estudiante_en_preparacion_controller(
    anio_destino_id, est, usa_entrevista=True
):
    """El alta directa del paso 5.5, cerrada desde el paso E7 de la entrevista
    de admisión en los colegios que la usan.

    En esos colegios, un estudiante nuevo del año en preparación solo entra
    desde una admisión aprobada (`POST /admisiones/{id}/matricular`, decisión
    3 de docs/funcionalidades/ENTREVISTA_ADMISION.md); quien sigue, por la
    promoción. La ruta se conserva para que una pestaña vieja reciba un
    mensaje claro: con un año que no está en preparación responde como
    siempre, y con el año en preparación, que entre por Admisiones. No
    escribe nada.

    Desde el 2026-10-30, en un colegio que no usa la entrevista
    (`usa_entrevista=False`, lo dice la ruta) vuelve a ser la del paso 5.5:
    crea la ficha y solo la matrícula del año en preparación. Sin decirlo,
    queda cerrada.
    """
    if not usa_entrevista:
        with get_cursor(commit=True) as cursor:
            _activo, destino = _contexto_matricula_en_preparacion(
                cursor, anio_destino_id
            )
            estudiante_id, matricula_id = _crear_estudiante_en_preparacion(
                cursor, destino, est
            )

        return {
            "mensaje": "Estudiante creado y matriculado en el año en preparación",
            "id": estudiante_id,
            "matricula_id": matricula_id,
            "anio_lectivo_id": destino[0],
            "curso_id": est.curso_id,
            "curso_vigente_id": None,
            "valores_especiales_copiados": [],
        }

    with get_cursor() as cursor:
        _activo, destino = _contexto_matricula_en_preparacion(
            cursor, anio_destino_id
        )
        raise AltaDirectaCerradaError(
            f"Un estudiante nuevo en {destino[1]} se matricula desde su "
            "entrevista aprobada (Admisiones)."
        )


def _exigir_reingreso_posible(existente, activo, destino):
    nombre = " ".join(
        parte for parte in (existente["nombre"], existente["apellido"]) if parte
    )
    if existente["matricula_destino_id"] is not None:
        raise EstudianteNoReingresableError(
            f"{nombre} ya tiene matrícula en {destino[1]}."
        )
    if existente["curso_activo_id"] is not None and existente["estado"] == "activo":
        raise EstudianteNoReingresableError(
            f"{nombre} estudia en {activo[1]}: pásalo a {destino[1]} desde la "
            "promoción (Matricular estudiantes)."
        )
    if existente["curso_activo_id"] is not None and existente["estado_salida"]:
        # Como en la promoción (6.2b): marca de salida y matrícula siguiente
        # se excluyen.
        raise EstudianteNoReingresableError(
            f"{nombre} está marcado como que no sigue en {destino[1]}. Quita la "
            "marca antes de matricularlo."
        )


def matricular_aspirante_en_preparacion(cursor, anio_destino_id, est):
    """Matrícula de un aspirante aprobado (entrevista de admisión, paso E3).

    Corre dentro de la transacción de quien llama (`admisiones_controller`),
    que además copia los datos de la entrevista y enlaza la admisión: todo o
    nada.

    - El aspirante queda `activo`, diga lo que diga la ficha: se está
      matriculando.
    - Si el documento de la ficha no es de nadie, se crea como en el alta
      directa del paso 5.5.
    - Si es de un estudiante (un exalumno que vuelve, decisión 11), se usa su
      mismo registro: se actualiza su ficha como en `PUT /estudiantes/{id}` y
      conserva su historial. No vale para quien ya tiene matrícula en el año
      en preparación, para quien estudia en el año activo (va por la
      promoción) ni para quien está marcado como que no sigue.
    """
    activo, destino = _contexto_matricula_en_preparacion(cursor, anio_destino_id)
    est = est.model_copy(update={"estado": "activo"})

    existente = None
    if est.documento_identidad:
        existente = anios_lectivos_repository.leer_estudiante_para_reingreso(
            cursor, est.documento_identidad, activo[0], destino[0]
        )

    if existente is None:
        estudiante_id, matricula_id = _crear_estudiante_en_preparacion(
            cursor, destino, est
        )
    else:
        _exigir_reingreso_posible(existente, activo, destino)
        _exigir_curso_del_anio(
            cursor,
            est.curso_id,
            destino[0],
            "seleccionado",
            "año en preparación",
        )
        estudiante_id = existente["id"]
        estudiantes_repository.actualizar_estudiante(
            cursor, (*_valores_globales_estudiante(est), estudiante_id)
        )
        guardar_sisben_y_residencia_si_llegaron(cursor, estudiante_id, est)
        matricula_id = anios_lectivos_repository.insertar_matricula_en_anio(
            cursor, estudiante_id, est.curso_id, destino[0]
        )
        # El curso vigente sigue siendo el de su matrícula activa, si tiene.
        anios_lectivos_repository.sincronizar_curso_vigente(cursor, estudiante_id)

    return {
        "estudiante_id": estudiante_id,
        "matricula_id": matricula_id,
        "anio_lectivo_id": destino[0],
        "anio": destino[1],
        "curso_id": est.curso_id,
        "estudiante_existente": existente is not None,
    }
