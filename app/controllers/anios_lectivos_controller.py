"""Años lectivos: listado y creación del siguiente año en preparación.

Ver docs/funcionalidades/ANIO_LECTIVO.md (fase 3, paso 3.1, y fase 5, paso
5.3). Qué años ve cada usuario lo decide `app/services/anio_lectivo.py`.
"""
from app.database import get_cursor
from app.repositories import anios_lectivos_repository
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
    """La configuración solo se copia al N+1 que está en preparación."""


class ConfiguracionAnioDuplicadaError(Exception):
    """Un curso o concepto del origen ya existe en el destino."""


class ConfiguracionAnioInconsistenteError(Exception):
    """Una referencia del origen no pudo reconstruirse en el destino."""


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
