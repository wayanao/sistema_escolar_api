"""Años lectivos: consulta, preparación y matrícula del año siguiente.

Ver docs/funcionalidades/ANIO_LECTIVO.md (fase 3, paso 3.1; fase 5, pasos
5.3 a 5.5, y fase 6, paso 6.2a). Qué años ve cada usuario lo decide
`app/services/anio_lectivo.py`.
"""
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


def _contexto_activacion(cursor, anio_destino_id):
    """Año activo y el siguiente en preparación, leídos sin bloquear."""
    activo = anios_lectivos_repository.leer_anio_activo(cursor)
    if activo is None:
        raise AnioLectivoActivoInexistenteError(
            "No hay un año lectivo activo para cerrar."
        )

    destino = anios_lectivos_repository.leer_anio_lectivo(cursor, anio_destino_id)
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


def crear_estudiante_en_preparacion_controller(anio_destino_id, est):
    """Crea datos globales y solo la matrícula del año en preparación."""
    with get_cursor(commit=True) as cursor:
        _activo, destino = _contexto_matricula_en_preparacion(
            cursor, anio_destino_id
        )
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
        matricula_id = anios_lectivos_repository.insertar_matricula_en_anio(
            cursor, estudiante_id, est.curso_id, destino[0]
        )
        # Al no tener matrícula activa, esta sincronización conserva NULL.
        anios_lectivos_repository.sincronizar_curso_vigente(
            cursor, estudiante_id
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
