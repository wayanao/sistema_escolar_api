"""Reglas del año lectivo que comparten varios modulos.

Ver docs/funcionalidades/ANIO_LECTIVO.md. Es el servicio que el documento
preve para el año lectivo: valida el año que se pide (fase 2), decide que
años puede mirar cada usuario, cuando avisar al renombrar una materia y en
que años puede guardar cada usuario (fase 3).
"""
from fastapi import HTTPException, status

from app.repositories.anios_lectivos_repository import (
    leer_anio_activo,
    leer_anio_de_anotacion,
    leer_anio_de_asignacion,
    leer_anio_de_concepto,
    leer_anio_de_plan,
    leer_anio_lectivo,
    leer_anios_de_cursos,
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


ESTADOS_DE_ANIO_PASADO = {"cerrado", "reabierto"}


def anios_a_avisar_al_renombrar(usos):
    """Los años que hay que nombrar al avisar de un cambio de nombre de materia.

    `usos` son los años en que se dicta la materia, como `(anio, estado)`. El
    nombre se lee al imprimir, asi que cambiarlo cambia tambien los boletines
    y certificados de esos años (decision 12). Se avisa si la materia se usa
    en mas de un año o en uno cerrado o reabierto, y se nombran los años que
    no son el activo. Con un solo año, como hoy, devuelve `[]`: nunca avisa.
    """
    if len(usos) <= 1 and not any(estado in ESTADOS_DE_ANIO_PASADO for _, estado in usos):
        return []
    return [anio for anio, estado in usos if estado != "activo"]


def mensaje_materia_usada_en_otro_anio(anios):
    """El aviso de la decision 12, listo para mostrar."""
    textos = [str(anio) for anio in anios]
    if len(textos) > 1:
        texto = f"{', '.join(textos[:-1])} y {textos[-1]}"
    else:
        texto = textos[0]
    return (
        f"Esta materia se usa en {texto}. Si cambias el nombre, también "
        f"cambiará en los boletines y certificados de {texto}."
    )


def _es_admin(usuario):
    # Todo lo que no sea admin se trata como profesor: si mañana aparece otro
    # rol, ve solo el año activo hasta que alguien decida otra cosa.
    return usuario.get("rol") == "admin"


# ---------------------------------------------------------------------------
# Guardia de escritura (fase 3, paso 3.7).
# ---------------------------------------------------------------------------

# El frontend reconoce este texto para titular su aviso (`esAvisoAnioCerrado`
# en frontend-react/src/utils/anioLectivo.js, paso 6.9): cambiarlos juntos.
MENSAJE_ANIO_CERRADO = "El año lectivo {anio} está cerrado. Solo se puede consultar."
MENSAJE_SOLO_ANIO_ACTIVO = "Solo se pueden guardar cambios en el año lectivo activo."
ESTADOS_EDITABLES_POR_ADMIN = {"preparacion", "reabierto"}


class AnioLectivoNoEditableError(HTTPException):
    """El año de lo que se quiere guardar no admite cambios de este usuario.

    Es una `HTTPException` a proposito: la guardia corre dentro de cada
    guardado, y asi llega a la respuesta tal cual (409 o 403, con su mensaje)
    sin que cada ruta la traduzca. Las rutas que atrapan `Exception` dejan
    pasar antes las `HTTPException`.
    """

    def __init__(self, codigo_http, mensaje):
        super().__init__(status_code=codigo_http, detail=mensaje)


def exigir_anio_editable(anio_y_estado, usuario):
    """La regla de la guardia, sobre el `(anio, estado)` ya leido.

    | Estado          | Admin | Profesor |
    |-----------------|-------|----------|
    | activo          | si    | si       |
    | preparacion     | si    | 403      |
    | reabierto       | si    | 403      |
    | cerrado         | 409   | 409      |

    Un estado desconocido se trata como cerrado. Sin fila (`None`: lo que se
    quiere guardar no existe) no hace nada: el guardado responde como siempre.
    """
    if anio_y_estado is None:
        return
    anio, estado = anio_y_estado
    if estado == "activo":
        return
    if estado in ESTADOS_EDITABLES_POR_ADMIN:
        if _es_admin(usuario):
            return
        raise AnioLectivoNoEditableError(status.HTTP_403_FORBIDDEN, MENSAJE_SOLO_ANIO_ACTIVO)
    raise AnioLectivoNoEditableError(
        status.HTTP_409_CONFLICT, MENSAJE_ANIO_CERRADO.format(anio=anio)
    )


def exigir_asignacion_editable(cursor, asignacion_id, usuario):
    """Guardia para lo que cuelga de una clase. Una consulta, en el cursor dado."""
    exigir_anio_editable(leer_anio_de_asignacion(cursor, asignacion_id), usuario)


def exigir_plan_editable(cursor, plan_id, usuario):
    """Guardia para un plan de clases. Una consulta, en el cursor dado."""
    exigir_anio_editable(leer_anio_de_plan(cursor, plan_id), usuario)


def exigir_anotacion_editable(cursor, anotacion_id, usuario):
    """Guardia para una anotacion del observador. Una consulta, en el cursor dado."""
    exigir_anio_editable(leer_anio_de_anotacion(cursor, anotacion_id), usuario)


# Paso 3.7b: rutas de solo admin. Su router ya exige admin, asi que la regla
# es la del admin (todo menos un año cerrado) y no hace falta pasar el usuario
# por cada capa. Si una de esas rutas se abriera algun dia a profesores, tiene
# que pasar a las versiones con usuario.
_ADMIN = {"rol": "admin"}


def exigir_anio_editable_para_admin(anio_y_estado):
    """La regla del admin sobre un `(anio, estado)` ya leido: 409 si esta cerrado."""
    exigir_anio_editable(anio_y_estado, _ADMIN)


def exigir_cursos_editables_para_admin(cursor, curso_ids):
    """Guardia de solo admin para uno o varios cursos. Una consulta."""
    for anio_y_estado in leer_anios_de_cursos(cursor, curso_ids):
        exigir_anio_editable_para_admin(anio_y_estado)


def exigir_asignacion_editable_para_admin(cursor, asignacion_id):
    """Guardia de solo admin para una clase. Una consulta."""
    exigir_anio_editable_para_admin(leer_anio_de_asignacion(cursor, asignacion_id))


def exigir_plan_editable_para_admin(cursor, plan_id):
    """Guardia de solo admin para un plan de clases. Una consulta."""
    exigir_anio_editable_para_admin(leer_anio_de_plan(cursor, plan_id))


def exigir_concepto_editable_para_admin(cursor, tipo_pago_id):
    """Guardia de solo admin para un concepto de pago. Una consulta."""
    exigir_anio_editable_para_admin(leer_anio_de_concepto(cursor, tipo_pago_id))


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
