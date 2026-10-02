"""Reglas del año lectivo que comparten varios modulos.

Ver docs/funcionalidades/ANIO_LECTIVO.md. Es el servicio que el documento
preve para el año lectivo: valida el año que se pide (fase 2) y decide que
años puede mirar cada usuario (fase 3).
"""
from app.repositories.anios_lectivos_repository import (
    leer_anio_activo,
    leer_anio_lectivo,
    listar_anios_lectivos,
)


class AnioLectivoNoPermitidoError(Exception):
    """Un usuario que no es admin pidio un año que no es el activo."""


class AnioLectivoInexistenteError(ValueError):
    """El año lectivo pedido no existe.

    Es un `ValueError` para que quien ya lo atrapaba asi (las rutas de las
    fases 2 y 3) siga igual; quien necesita distinguirlo de otros
    `ValueError` lo atrapa por su nombre.
    """


def exigir_anio_lectivo(cursor, anio_lectivo_id):
    """Devuelve el año pedido como `(id, anio, estado)`.

    Lanza `AnioLectivoInexistenteError`, con un mensaje listo para mostrar, si
    no existe. Cualquier estado vale: un pago se registra en el año de la
    deuda que salda, aunque ese año este cerrado (decision 6).
    """
    anio = leer_anio_lectivo(cursor, anio_lectivo_id)
    if anio is None:
        raise AnioLectivoInexistenteError("El año lectivo seleccionado no existe.")
    return anio


def anio_distinto_del_activo(cursor, anio_lectivo_id, usuario=None):
    """El año pedido si no es el activo; `None` si no se pidio o es el activo.

    Es la regla de "con el año activo, las consultas de siempre": quien recibe
    `None` sigue su camino de hoy, letra por letra, y solo un año distinto
    toma el camino que lee por matriculas. Sin año no consulta nada; con año,
    una consulta para validarlo (`AnioLectivoInexistenteError` si no existe).

    Con `usuario`, para las rutas que tambien usa el profesor, aplica ademas
    `resolver_anio_pedido`: si no es admin y pide otro año,
    `AnioLectivoNoPermitidoError`.
    """
    if anio_lectivo_id is None:
        return None
    if usuario is None:
        anio = exigir_anio_lectivo(cursor, anio_lectivo_id)
    else:
        anio = resolver_anio_pedido(cursor, anio_lectivo_id, usuario)
    return None if anio[2] == "activo" else anio_lectivo_id


def _es_admin(usuario):
    # Todo lo que no sea admin se trata como profesor: si mañana aparece otro
    # rol, ve solo el año activo hasta que alguien decida otra cosa.
    return usuario.get("rol") == "admin"


def listar_anios_visibles(cursor, usuario):
    """Los años que puede mirar el usuario, como filas `(id, anio, estado)`.

    El admin ve todos (decision 3: consulta los años pasados). El profesor
    solo el activo (decision 4), y una lista vacia si el colegio no tuviera
    año activo.
    """
    if _es_admin(usuario):
        return listar_anios_lectivos(cursor)
    activo = leer_anio_activo(cursor)
    return [activo] if activo else []


def resolver_anio_pedido(cursor, anio_lectivo_id, usuario):
    """El año que se quiere mirar en un listado, ya validado.

    Sin `anio_lectivo_id` devuelve `None` **sin consultar nada**: quien llama
    usa el año activo con `ANIO_ACTIVO_ID_SQL` dentro de su propia consulta,
    asi que la peticion de hoy, que no manda año, cuesta lo mismo que antes.

    Con el, devuelve `(id, anio, estado)`. Lanza `ValueError` si no existe y
    `AnioLectivoNoPermitidoError` si el usuario no es admin y el año no es el
    activo: el profesor no navega otros años (decision 4).
    """
    if anio_lectivo_id is None:
        return None
    anio = exigir_anio_lectivo(cursor, anio_lectivo_id)
    if not _es_admin(usuario) and anio[2] != "activo":
        raise AnioLectivoNoPermitidoError(
            "Solo se puede consultar el año lectivo activo."
        )
    return anio
