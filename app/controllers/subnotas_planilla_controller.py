"""Reglas de las subnotas de la planilla. Ver `docs/funcionalidades/SUBNOTAS_PLANILLA.md`.

Sus errores propios son excepciones con mensaje **constante**, y la ruta las
traduce a 404, 409 o 422, como en `listas_seguimiento_controller`. Las guardias
compartidas (permiso de la asignacion, año lectivo, estudiante del curso) ya
son `HTTPException` y llegan a la respuesta tal cual, igual que en el resto de
la planilla.

**Cada funcion abre una sola conexion para todo lo que hace**, y comprobar y
escribir van en la misma transaccion. El permiso del profesor se comprueba con
el cursor ya abierto (`cursor=`), asi que no paga una segunda conexion como
las tres rutas viejas de la planilla. Consultas de cada una, para un profesor
(el admin hace una menos: su permiso no consulta nada):

- `crear_subnota_controller`: 6 -permiso, año, asignacion academica, que el
  tipo exista, conteo e insercion-.
- `renombrar_subnota_controller`: 4 -permiso, año, asignacion academica y el
  cambio-.
- `eliminar_subnota_controller`: 7 si nadie la habia calificado -permiso, año,
  asignacion academica, buscarla, bloquear el tipo, leer sus calificaciones y
  borrarla-, y 10 si alguien si: el nivel del curso y rehacer las celdas en dos
  sentencias. **No crece con el numero de estudiantes.**
- `guardar_calificaciones_controller`: 9 o 10 -permiso, año, estudiante,
  asignacion academica, nivel, bloquear y leer, vaciar o escribir (una o las
  dos) y la celda (borrar e insertar)-.

La celda la calcula `app/core/subnotas_planilla.py` y la escribe este modulo en
la misma transaccion que las subnotas: o se guarda todo o nada (P9).
"""
from psycopg2 import IntegrityError

from app.core.nivel_academico import resolver_tipo_evaluacion
from app.core.permissions import require_asignacion_access, require_estudiante_in_asignacion
from app.core.subnotas_planilla import (
    MAXIMO_SUBNOTAS_POR_TIPO,
    admite_subnotas,
    calcular_celda,
    normalizar_nota,
    tipo_de_calificaciones,
    valor_de_calificacion,
)
from app.core.valoraciones_desarrollo import es_valoracion
from app.database import get_cursor
from app.repositories import planilla_repository
from app.repositories import subnotas_planilla_repository as repositorio
from app.services.anio_lectivo import exigir_asignacion_editable
from app.services.asignacion_academica import (
    resolver_asignacion_academica_id_cursor,
    resolver_nivel_curso_cursor,
)


TIPO_NO_ENCONTRADO = "Ese tipo de nota no existe en esta planilla."
TIPO_SIN_SUBNOTAS = "Ese tipo de nota no admite subnotas."
SUBNOTA_DUPLICADA = "Ya existe una subnota con ese nombre en este tipo de nota."
LIMITE_DE_SUBNOTAS = (
    f"Un tipo de nota admite hasta {MAXIMO_SUBNOTAS_POR_TIPO} subnotas."
)
SUBNOTA_NO_ENCONTRADA = "Esa subnota ya no existe."
SUBNOTAS_AJENAS = "Alguna de esas subnotas no es de este tipo de nota."
NOTA_INVALIDA = "Cada subnota debe ser un número entre 1 y 5."
CARITA_INVALIDA = "Cada subnota debe ser una de las valoraciones de la escala."


class ErrorDeSubnotas(Exception):
    """Base de los errores propios. La ruta decide el codigo HTTP de cada uno."""


class TipoNoEncontradoError(ErrorDeSubnotas):
    """El tipo de nota no esta en la planilla. La ruta lo traduce a 404."""


class TipoSinSubnotasError(ErrorDeSubnotas):
    """Columna interna que no se muestra (P11). La ruta lo traduce a 422."""


class SubnotaDuplicadaError(ErrorDeSubnotas):
    """Ese tipo ya tiene una subnota con ese nombre. La ruta lo traduce a 409."""


class LimiteDeSubnotasError(ErrorDeSubnotas):
    """El tipo ya tiene el maximo de subnotas (P11). La ruta lo traduce a 422."""


class SubnotaNoEncontradaError(ErrorDeSubnotas):
    """La subnota no existe o es de otra clase. La ruta lo traduce a 404."""


class SubnotasAjenasError(ErrorDeSubnotas):
    """El cuerpo trae una subnota de otro tipo o de otra clase. 422."""


class CalificacionInvalidaError(ErrorDeSubnotas):
    """Una calificacion no sirve para el tipo de evaluacion del curso. 422."""


def _abrir_clase(cursor, asignacion_id, usuario):
    """Permiso, año lectivo y asignacion academica: lo primero de cada escritura.

    El permiso va antes que el año, igual que en las rutas viejas de la
    planilla, donde lo comprueba la ruta antes de llamar al controlador. Asi
    quien no tiene la clase recibe 403 sin enterarse de en que año esta.
    """
    require_asignacion_access(asignacion_id, usuario, cursor=cursor)
    exigir_asignacion_editable(cursor, asignacion_id, usuario)
    return resolver_asignacion_academica_id_cursor(cursor, asignacion_id)


def crear_subnota_controller(datos, *, usuario):
    """Crea una subnota para todo el curso (decision 5) y la devuelve.

    El nombre repetido se atrapa dos veces, como en Listas de seguimiento: el
    conteo previo da el 409 del caso normal, y el indice unico cubre la carrera
    de dos peticiones a la vez, que sin el `except` saldria como 500.
    """
    if not admite_subnotas(datos.tipo_nota):
        raise TipoSinSubnotasError(TIPO_SIN_SUBNOTAS)

    with get_cursor(commit=True) as cursor:
        asignacion_id = _abrir_clase(cursor, datos.asignacion_id, usuario)

        if not repositorio.existe_tipo_nota(
            cursor, asignacion_id, datos.periodo, datos.tipo_nota
        ):
            raise TipoNoEncontradoError(TIPO_NO_ENCONTRADO)

        total, repetidas = repositorio.contar_subnotas_del_tipo(
            cursor, asignacion_id, datos.periodo, datos.tipo_nota, datos.nombre
        )
        if repetidas:
            raise SubnotaDuplicadaError(SUBNOTA_DUPLICADA)
        if total >= MAXIMO_SUBNOTAS_POR_TIPO:
            raise LimiteDeSubnotasError(LIMITE_DE_SUBNOTAS)

        try:
            subnota_id = repositorio.insertar_subnota(
                cursor, asignacion_id, datos.periodo, datos.tipo_nota, datos.nombre
            )
        except IntegrityError as exc:
            raise SubnotaDuplicadaError(SUBNOTA_DUPLICADA) from exc

    return {"id": subnota_id, "tipo_nota": datos.tipo_nota, "nombre": datos.nombre}


def renombrar_subnota_controller(subnota_id, datos, *, usuario):
    """Cambia el nombre de una subnota. No toca ninguna calificacion (P5)."""
    with get_cursor(commit=True) as cursor:
        asignacion_id = _abrir_clase(cursor, datos.asignacion_id, usuario)
        try:
            existe = repositorio.renombrar_subnota(
                cursor, subnota_id, asignacion_id, datos.nombre
            )
        except IntegrityError as exc:
            raise SubnotaDuplicadaError(SUBNOTA_DUPLICADA) from exc
        if not existe:
            raise SubnotaNoEncontradaError(SUBNOTA_NO_ENCONTRADA)

    return {"id": subnota_id, "nombre": datos.nombre}


def _celda_en_json(nota, valoracion):
    return {"nota": float(nota) if nota is not None else None, "valoracion": valoracion}


def eliminar_subnota_controller(subnota_id, asignacion_id_pedido, *, usuario):
    """Borra la subnota y recalcula la celda de cada estudiante afectado (P5).

    Afectado es quien tenia esa subnota calificada. Su celda pasa a ser el
    promedio de lo que le queda, o vacia si no le queda nada (P4). Los demas
    no cambian, porque una subnota vacia no contaba en su promedio (P2).

    Devuelve las celdas nuevas para que la pantalla se actualice sin recargar
    la planilla.
    """
    with get_cursor(commit=True) as cursor:
        asignacion_id = _abrir_clase(cursor, asignacion_id_pedido, usuario)

        subnota = repositorio.buscar_subnota(cursor, subnota_id, asignacion_id)
        if subnota is None:
            raise SubnotaNoEncontradaError(SUBNOTA_NO_ENCONTRADA)
        periodo, tipo_nota = subnota

        repositorio.bloquear_subnotas_del_tipo(cursor, asignacion_id, periodo, tipo_nota)
        calificaciones = repositorio.leer_calificaciones_del_tipo(
            cursor, asignacion_id, periodo, tipo_nota
        )
        repositorio.borrar_subnota(cursor, subnota_id)

        por_estudiante = {}
        afectados = set()
        for calificada_id, estudiante_id, nota, valoracion in calificaciones:
            por_estudiante.setdefault(estudiante_id, []).append(
                (calificada_id, nota, valoracion)
            )
            if calificada_id == subnota_id:
                afectados.add(estudiante_id)

        celdas = []
        if afectados:
            nivel = resolver_nivel_curso_cursor(cursor, asignacion_id)
            for estudiante_id in sorted(afectados):
                suyas = por_estudiante[estudiante_id]
                tipo_evaluacion = resolver_tipo_evaluacion(
                    nivel, tipo_de_calificaciones((n, v) for _, n, v in suyas)
                )
                nota, valoracion = calcular_celda(
                    tipo_evaluacion,
                    ((n, v) for calificada_id, n, v in suyas if calificada_id != subnota_id),
                )
                celdas.append((estudiante_id, nota, tipo_evaluacion, valoracion))

            repositorio.borrar_celdas(
                cursor, asignacion_id, periodo, tipo_nota, [celda[0] for celda in celdas]
            )
            repositorio.insertar_celdas(cursor, asignacion_id, periodo, tipo_nota, celdas)

    return {
        "mensaje": "Subnota eliminada correctamente",
        "calificaciones_borradas": len(afectados),
        "celdas": {
            str(estudiante_id): _celda_en_json(nota, valoracion)
            for estudiante_id, nota, _, valoracion in celdas
        },
    }


def _calificacion(valor, tipo_evaluacion):
    """`(nota, valoracion)` que se guarda, o None para dejar la subnota vacia."""
    if valor is None:
        return None
    if tipo_evaluacion == "desarrollo":
        if isinstance(valor, str) and es_valoracion(valor):
            return None, valor
        raise CalificacionInvalidaError(CARITA_INVALIDA)

    nota = normalizar_nota(valor)
    if nota is None:
        raise CalificacionInvalidaError(NOTA_INVALIDA)
    return nota, None


def guardar_calificaciones_controller(datos, *, usuario):
    """Guarda las subnotas de un estudiante en un tipo y recalcula su celda.

    Solo se tocan las subnotas que llegan (ver `CalificacionesCreate`). La
    celda se escribe con las mismas dos sentencias del guardado a mano
    (`planilla_repository`), asi queda exactamente como si el profesor la
    hubiera escrito.

    El tipo de evaluacion se resuelve como en `POST /planilla/nota`: el nivel
    del curso manda (preescolar caritas, primaria numeros).
    """
    with get_cursor(commit=True) as cursor:
        require_asignacion_access(datos.asignacion_id, usuario, cursor=cursor)
        exigir_asignacion_editable(cursor, datos.asignacion_id, usuario)
        require_estudiante_in_asignacion(
            datos.estudiante_id, datos.asignacion_id, cursor=cursor
        )
        asignacion_id = resolver_asignacion_academica_id_cursor(cursor, datos.asignacion_id)
        tipo_evaluacion = resolver_tipo_evaluacion(
            resolver_nivel_curso_cursor(cursor, asignacion_id), datos.tipo_evaluacion
        )

        actuales = {
            subnota_id: (nota, valoracion)
            for subnota_id, nota, valoracion in repositorio.bloquear_subnotas_con_calificaciones_de(
                cursor, asignacion_id, datos.periodo, datos.tipo_nota, datos.estudiante_id
            )
        }
        if not set(datos.valores) <= set(actuales):
            raise SubnotasAjenasError(SUBNOTAS_AJENAS)

        # Todo se valida antes de escribir nada.
        nuevas = {
            subnota_id: _calificacion(valor, tipo_evaluacion)
            for subnota_id, valor in datos.valores.items()
        }
        repositorio.borrar_calificaciones(
            cursor,
            datos.estudiante_id,
            [subnota_id for subnota_id, calificacion in nuevas.items() if calificacion is None],
        )
        repositorio.guardar_calificaciones(
            cursor,
            datos.estudiante_id,
            [
                (subnota_id, *calificacion)
                for subnota_id, calificacion in nuevas.items()
                if calificacion is not None
            ],
        )

        resultado = {
            subnota_id: calificacion
            for subnota_id, calificacion in actuales.items()
            if calificacion != (None, None)
        }
        for subnota_id, calificacion in nuevas.items():
            if calificacion is None:
                resultado.pop(subnota_id, None)
            else:
                resultado[subnota_id] = calificacion

        nota, valoracion = calcular_celda(tipo_evaluacion, resultado.values())
        planilla_repository.borrar_nota_existente(
            cursor, datos.estudiante_id, asignacion_id, datos.periodo, datos.tipo_nota
        )
        planilla_repository.insertar_nota(
            cursor,
            datos.estudiante_id,
            asignacion_id,
            datos.periodo,
            nota,
            datos.tipo_nota,
            tipo_evaluacion,
            valoracion,
        )

    return {
        "estudiante_id": datos.estudiante_id,
        "tipo_nota": datos.tipo_nota,
        "tipo_evaluacion": tipo_evaluacion,
        **_celda_en_json(nota, valoracion),
        "subnotas": {
            str(subnota_id): valor_de_calificacion(*calificacion)
            for subnota_id, calificacion in resultado.items()
        },
    }
